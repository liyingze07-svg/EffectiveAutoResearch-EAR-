#!/usr/bin/env python3
"""UCT 引导的 idea 搜索，带基于可验证信号的 mask 先验剪枝。

关于"这是不是 MCTS"
-------------------
标准 MCTS 四阶段中，本工具实现三个：

| 阶段 | 本工具 | 说明 |
|---|---|---|
| Selection | ✅ UCT1 | 在已展开节点中按 Q + c·sqrt(ln N_parent / N_child) 选择 |
| Expansion | ✅（由外部模型执行） | 本工具只输出"下一个该扩展谁"与扩展指令；实际生成由 skill 调用 LLM 完成 |
| Simulation (rollout) | ❌ **没有** | 无法为一个研究 idea 随机模拟到终局。用评估值代替 rollout（AlphaZero 式 value 替代） |
| Backup | ✅ | 评估值沿父链回传，更新 visits 与 value_sum |

因此准确的说法是 **"UCT 引导的最佳优先扩展 + value 估计代替 rollout"**，不是带随机模拟的完整 MCTS。

reward 的诚实说明
-----------------
`reward = alpha × v_model + (1 - alpha) × v_verifiable`

- `v_model` 来自 `scores.composite`，**由 LLM 给出**。单独用它做搜索信号会放大评分模型的
  系统偏差：搜得越狠，候选越向"评分模型偏好的那类提案"塌缩。
- `v_verifiable` 由不依赖 LLM 判断的成分构成（检索结果、规则查表、结构完整性、实测成本、
  计算得到的差异度）。各成分的来源在 `report --provenance` 中逐项列出。
- **alpha 默认 0.5，且当 v_verifiable 无任何可用成分时会明确警告。**

命令
----
init      初始化搜索状态（把现有未剪枝节点作为根集合）
mask      计算 mask 命中；--apply 写入 prune（剪枝在扩展之前，即先验剪枝）
select    按 UCT 选出下一个该扩展的节点，并打印扩展指令
expand    登记外部模型生成的子节点，并记一次访问
backup    回传评估值（默认从 scores.composite 自动折算）
report    搜索树、各节点 Q/visits/UCT、预算消耗、mask 统计
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import idea_nodes as N  # noqa: E402  复用节点读写与校验

try:
    from dedup_ideas import find_boilerplate, same_lineage, similarity
except Exception:      # pragma: no cover - 去重工具缺失时降级
    find_boilerplate = similarity = same_lineage = None

DEFAULT_PATH = Path("outputs/IDEA_NODES.jsonl")
UCT_C = 1.414                # sqrt(2)，标准 UCT 探索常数
FIT_THRESHOLD = 12           # 与 idea-gen 的 FILTER_THRESHOLD 一致
CRITIQUE_SATURATION = 3      # 与 Phase 2b 的"单批判 ≤3 个 idea"一致


# ---------------------------------------------------------------- masks

def mask_hits(node: dict, all_nodes: list[dict], saturated_reason: str | None = None) -> list[tuple[str, str]]:
    """返回 (mask, 理由)。**全部基于可验证信号，不含 LLM 的主观判断。**"""
    hits: list[tuple[str, str]] = []
    scores = node.get("scores") or {}
    cw = node.get("closest_work") or {}

    # 1. 撞车：检索实际找到了紧邻工作（外部检索事实），或查新未完成
    if cw.get("ref") and not str(cw.get("delta") or "").strip():
        hits.append(("collision", "closest_work 有 ref 但 delta 为空 — 查新未完成，无法判断差异"))
    if node.get("evidence_collision") is True:
        hits.append(("collision", "检索确认存在同机制的已发表工作"))

    # 2. 验不起：理论 claim 的验证协议查表判定为 NOT_FEASIBLE 且未走三条出路
    claims = node.get("theory_claims") or []
    infeasible = [c for c in claims if c.get("feasibility") == "NOT_FEASIBLE"
                  and not c.get("resolution")]
    if infeasible:
        hits.append(("not_feasible",
                     f"{len(infeasible)}/{len(claims)} 条理论 claim 判定为 NOT_FEASIBLE 且未采纳出路"))

    # 3. 研究者契合度低于阈值（规则阈值，非模型判断）
    fit = scores.get("researcher_fit")
    if fit is not None and float(fit) < FIT_THRESHOLD:
        hits.append(("fit_below_threshold", f"researcher_fit={fit} < {FIT_THRESHOLD}"))

    # 4. 同一批判下候选过多：只剪**超出上限的最弱叶子**，见 compute_saturated
    if saturated_reason:
        hits.append(("critique_saturated", saturated_reason))

    # 5. 结构性不可否证：没有否证条件的假设无法被实验推翻
    hyp = node.get("hypothesis") or {}
    if hyp.get("core") and not str(hyp.get("falsifier") or "").strip():
        hits.append(("not_feasible", "hypothesis 无 falsifier — 假设不可否证，无法设计验证实验"))
    return hits


def compute_saturated(nodes: list[dict], alpha: float) -> dict[str, str]:
    """同一证据锚定的候选超过上限时，标记**超出部分中 reward 最低的叶子**。

    两条边界，都是为了让 mask 表达"别再往这个分支投预算"而不是"丢掉已有成果"：

    1. 只考虑**叶子**（没有存活子节点的候选）。已经分裂出子节点的父节点代表一条分支，
       不是与兄弟重复的候选，剪掉它会连带废掉其下所有子节点。
    2. 保留 reward 最高的前 `CRITIQUE_SATURATION` 个，只标记其余的。早期实现对该锚定下的
       **所有**节点一律标记，会把父节点和最优子节点一起剪掉。
    """
    live = alive(nodes)
    has_live_child = {n.get("parent_id") for n in live if n.get("parent_id")}
    by_anchor: dict[str, list[dict]] = {}
    for n in live:
        if n.get("id") in has_live_child:
            continue                      # 非叶子，跳过
        for a in ((n.get("generator") or {}).get("anchor", []) or []):
            by_anchor.setdefault(a, []).append(n)

    flagged: dict[str, str] = {}
    for a, group in by_anchor.items():
        if len(group) <= CRITIQUE_SATURATION:
            continue
        ranked = sorted(group, key=lambda n: -reward(n, nodes, alpha)[0])
        for n in ranked[CRITIQUE_SATURATION:]:
            flagged[n["id"]] = (f"批判 {a} 已有 {len(group)} 个候选叶子（上限 "
                                f"{CRITIQUE_SATURATION}），本节点 reward 排名第 "
                                f"{ranked.index(n) + 1}，超出上限")
    return flagged


# ---------------------------------------------------------------- reward

def verifiable_components(node: dict, all_nodes: list[dict]) -> dict[str, tuple[float, str]]:
    """各成分 -> (值 0-1, 来源说明)。缺失的成分不参与平均。"""
    out: dict[str, tuple[float, str]] = {}
    cw = node.get("closest_work") or {}
    if cw.get("ref"):
        out["retrieval"] = (0.0 if node.get("evidence_collision") is True
                            else (1.0 if str(cw.get("delta") or "").strip() else 0.0),
                            "外部检索结果（是否找到同机制已发表工作 / delta 是否写出）")
    claims = node.get("theory_claims") or []
    if claims:
        ok = sum(1 for c in claims if c.get("feasibility") in ("FEASIBLE", "CAVEATS"))
        out["feasibility_rule"] = (ok / len(claims),
                                   "claim 类型 → 验证协议查表（规则，非模型评分）")
    hyp = node.get("hypothesis") or {}
    if hyp.get("core"):
        out["falsifiability"] = (1.0 if str(hyp.get("falsifier") or "").strip() else 0.0,
                                 "结构完整性：是否写出否证条件")
    cost = node.get("cost") or {}
    if cost.get("tokens_total") or cost.get("tokens_in"):
        spent = float(cost.get("tokens_total") or 0) or \
                float(cost.get("tokens_in") or 0) + float(cost.get("tokens_out") or 0)
        peers = []
        for m in all_nodes:
            c = m.get("cost") or {}
            v = float(c.get("tokens_total") or 0) or \
                float(c.get("tokens_in") or 0) + float(c.get("tokens_out") or 0)
            if v:
                peers.append(v)
        if peers and max(peers) > 0:
            out["cost_efficiency"] = (1.0 - min(1.0, spent / max(peers)),
                                      "实测 token 用量（越省越高）")
    if similarity and find_boilerplate and len(all_nodes) > 1:
        boiler = find_boilerplate(all_nodes)
        by_id = {n.get("id"): n for n in all_nodes}
        # 与 dedup_ideas 保持一致：祖先-后代天然相似（子候选沿用父的框架），
        # 不应计入差异度惩罚；只与非同血缘的候选比较。
        sims = [similarity(node, m, boiler)[0] for m in all_nodes
                if m.get("id") != node.get("id")
                and not (same_lineage and same_lineage(node, m, by_id))]
        if sims:
            out["distinctness"] = (1.0 - min(1.0, max(sims)),
                                   "与**非同血缘**候选的词法/概念重叠（计算值，非模型判断）")
    return out


def reward(node: dict, all_nodes: list[dict], alpha: float) -> tuple[float, dict]:
    comp = (node.get("scores") or {}).get("composite")
    v_model = float(comp) / 10.0 if comp is not None else None
    comps = verifiable_components(node, all_nodes)
    v_ver = (sum(v for v, _ in comps.values()) / len(comps)) if comps else None

    if v_model is None and v_ver is None:
        return 0.5, {"note": "无任何信号，按 0.5 处理"}
    if v_ver is None:
        return v_model, {"v_model": v_model, "v_verifiable": None,
                         "warning": "无可验证成分，reward 完全来自 LLM 评分（会放大评分偏差）"}
    if v_model is None:
        return v_ver, {"v_model": None, "v_verifiable": v_ver,
                       "note": "无 LLM 评分，reward 完全来自可验证成分"}
    return (alpha * v_model + (1 - alpha) * v_ver,
            {"v_model": round(v_model, 3), "v_verifiable": round(v_ver, 3), "alpha": alpha,
             "components": {k: round(v, 3) for k, (v, _) in comps.items()}})


# ---------------------------------------------------------------- search state

def s(node: dict) -> dict:
    return node.setdefault("search", {"visits": 0, "value_sum": 0.0,
                                     "expanded": False, "expansions": 0})


def q(node: dict) -> float:
    st = s(node)
    return st["value_sum"] / st["visits"] if st["visits"] else 0.0


def uct(node: dict, parent_visits: int, c: float) -> float:
    st = s(node)
    if st["visits"] == 0:
        return float("inf")
    return q(node) + c * math.sqrt(math.log(max(parent_visits, 1)) / st["visits"])


def children_of(nodes: list[dict], nid: str | None) -> list[dict]:
    return [n for n in nodes if n.get("parent_id") == nid]


# 可被选中扩展的状态：pending（待验证）与 supported（已获支持，可继续深挖）。
# shelved / refuted / impl_failed / pruned 都不应再分配扩展预算——
# 但它们**保留在文件中**，因为剪枝与暂缓记录本身是产物。
SELECTABLE_STATUS = {"pending", "supported"}


def alive(nodes: list[dict]) -> list[dict]:
    return [n for n in nodes
            if not (n.get("prune") or {}).get("pruned")
            and n.get("status") in SELECTABLE_STATUS]


# ---------------------------------------------------------------- commands

def cmd_init(args) -> int:
    path = Path(args.path)
    nodes = N.load(path)
    if not nodes:
        print(f"{path} 为空，先用 tools/idea_nodes.py 写入候选", file=sys.stderr)
        return 1
    for n in nodes:
        st = s(n)
        st.setdefault("visits", 0)
        st.setdefault("value_sum", 0.0)
        st.setdefault("expanded", False)
        st.setdefault("expansions", 0)
    meta = {"budget_expansions": args.budget, "alpha": args.alpha, "uct_c": args.c}
    Path(args.state).write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    N.save(path, nodes)
    print(f"已初始化搜索：{len(nodes)} 个节点，扩展预算 {args.budget}，alpha={args.alpha}，c={args.c}")
    print(f"搜索参数写入 {args.state}")
    return 0


def cmd_mask(args) -> int:
    path = Path(args.path)
    nodes = N.load(path)
    meta = json.loads(Path(args.state).read_text(encoding="utf-8")) if Path(args.state).exists() else {}
    alpha = meta.get("alpha", 0.5)
    saturated = compute_saturated(nodes, alpha)
    rows = []
    for n in alive(nodes):
        hits = mask_hits(n, nodes, saturated.get(n["id"]))
        if hits:
            rows.append((n, hits))
    if not rows:
        print(f"✅ 无 mask 命中（{len(alive(nodes))} 个存活节点）")
        return 0
    print(f"⚠️ {len(rows)} 个节点命中 mask（先验剪枝，在扩展之前执行）\n")
    for n, hits in rows:
        print(f"  {n['id']} {n.get('title','')[:56]}")
        for mask, why in hits:
            print(f"      [{mask}] {why}")
    if args.apply:
        for n, hits in rows:
            mask, why = hits[0]
            n["status"] = "pruned"
            n["prune"] = {"pruned": True, "mask": mask, "reason": why,
                          "all_hits": [{"mask": m, "reason": w} for m, w in hits]}
        N.save(path, nodes)
        print(f"\n已剪枝 {len(rows)} 个节点（保留在文件中，未删除）")
        print("被剪节点的 prune.all_hits 记录了全部命中原因，便于后续统计剪枝精度")
    else:
        print("\n（未写入。加 --apply 才会实际剪枝）")
    return 0


def cmd_select(args) -> int:
    path = Path(args.path)
    nodes = N.load(path)
    meta = json.loads(Path(args.state).read_text(encoding="utf-8")) if Path(args.state).exists() else {}
    c = args.c if args.c is not None else meta.get("uct_c", UCT_C)
    alpha = args.alpha if args.alpha is not None else meta.get("alpha", 0.5)

    pool = alive(nodes)
    if not pool:
        print("没有存活节点可扩展（全部被剪枝）", file=sys.stderr)
        return 1
    saturated = compute_saturated(nodes, alpha)
    blocked = [n for n in pool if mask_hits(n, nodes, saturated.get(n["id"]))]
    if blocked:
        print(f"⚠️ {len(blocked)} 个存活节点命中 mask 但尚未剪枝："
              f"{[n['id'] for n in blocked]}")
        print("   先跑 `mask --apply`，否则搜索会在应剪的分支上花预算\n")

    total_visits = sum(s(n)["visits"] for n in pool) or 1
    ranked = sorted(pool, key=lambda n: -uct(n, total_visits, c))
    best = ranked[0]
    r, detail = reward(best, nodes, alpha)

    print(f"下一个该扩展的节点：**{best['id']}** {best.get('title','')[:60]}")
    st = s(best)
    u = uct(best, total_visits, c)
    print(f"  visits={st['visits']}  Q={q(best):.3f}  UCT={'∞ (未访问)' if u == float('inf') else f'{u:.3f}'}")
    print(f"  当前 reward={r:.3f}  {detail}")
    if detail.get("warning"):
        print(f"  ⚠️ {detail['warning']}")
    print(f"\n候选排序（UCT 前 5）")
    for n in ranked[:5]:
        u2 = uct(n, total_visits, c)
        print(f"    {n['id']:<14} visits={s(n)['visits']:<3} Q={q(n):.3f} "
              f"UCT={'∞' if u2 == float('inf') else f'{u2:.3f}'}")

    print(f"\n--- 扩展指令（交给外部模型执行）---")
    print(f"对 {best['id']}「{best.get('title','')}」产出 {args.k} 个**机制层面不同**的子候选。")
    print("每个子候选必须：")
    print("  1. 锚定到具体证据 ID（CRITIQUE-xx / C-xx / 失效条件），不得为空")
    print("  2. 写出 hypothesis.core 与 **falsifier**（什么结果会否证它）")
    print("  3. 写出 closest_work 的 ref 与 delta（缺 delta 会被 mask 为 collision）")
    print("  4. 与父节点的差异必须在**机制**上，不是措辞上")
    print(f"产出后写入 JSON 数组，然后：")
    print(f"  python3 tools/mcts_search.py expand {best['id']} --children <file.json>")
    return 0


def cmd_expand(args) -> int:
    path = Path(args.path)
    nodes = N.load(path)
    parent = next((n for n in nodes if n.get("id") == args.id), None)
    if parent is None:
        print(f"未找到节点 {args.id}", file=sys.stderr)
        return 1
    payload = json.loads(Path(args.children).read_text(encoding="utf-8"))
    incoming = payload if isinstance(payload, list) else [payload]
    known = {n.get("id") for n in nodes}
    problems, added = [], []
    for child in incoming:
        child["parent_id"] = args.id
        child.setdefault("status", "pending")
        child.setdefault("created_at", N._now())
        child["updated_at"] = N._now()
        if child.get("id") in known:
            problems.append(f"{child.get('id')}: id 重复")
            continue
        errs = N.validate_node(child, known | {c.get("id") for c in incoming})
        if errs:
            problems.extend(errs)
            continue
        s(child)
        nodes.append(child)
        known.add(child.get("id"))
        added.append(child)
    if problems:
        print("子节点校验失败，全部未写入：", file=sys.stderr)
        for p_ in problems:
            print(f"  - {p_}", file=sys.stderr)
        return 1
    st_parent = s(parent)
    st_parent["expanded"] = True
    # 扩展**不**计入 visits：UCT 里的一次访问必须配一个回传的 value，
    # 否则 value_sum/visits 会被稀释，selection 反而会躲开刚扩展过的节点。
    # 预算单独用 expansions 计数。
    st_parent["expansions"] = st_parent.get("expansions", 0) + 1
    N.save(path, nodes)
    print(f"已为 {args.id} 登记 {len(added)} 个子节点：{[c['id'] for c in added]}")
    print(f"  {args.id} expansions -> {st_parent['expansions']}（visits 不变，等 backup 回传）")
    print("接着对子节点评分（/idea-screen），然后 backup 回传：")
    for c in added:
        print(f"  python3 tools/mcts_search.py backup {c['id']}")
    return 0


def cmd_backup(args) -> int:
    path = Path(args.path)
    nodes = N.load(path)
    by_id = {n.get("id"): n for n in nodes}
    node = by_id.get(args.id)
    if node is None:
        print(f"未找到节点 {args.id}", file=sys.stderr)
        return 1
    meta = json.loads(Path(args.state).read_text(encoding="utf-8")) if Path(args.state).exists() else {}
    alpha = args.alpha if args.alpha is not None else meta.get("alpha", 0.5)
    if args.value is not None:
        r, detail = float(args.value), {"note": "人工指定"}
    else:
        r, detail = reward(node, nodes, alpha)

    chain, cur, guard = [], node, 0
    while cur is not None and guard < 50:
        st = s(cur)
        st["visits"] += 1
        st["value_sum"] += r
        chain.append(f"{cur['id']}(visits={st['visits']}, Q={q(cur):.3f})")
        cur = by_id.get(cur.get("parent_id"))
        guard += 1
    N.save(path, nodes)
    print(f"回传 reward={r:.3f} {detail}")
    if detail.get("warning"):
        print(f"⚠️ {detail['warning']}")
    print("更新路径: " + " → ".join(chain))
    return 0


def cmd_report(args) -> int:
    path = Path(args.path)
    nodes = N.load(path)
    meta = json.loads(Path(args.state).read_text(encoding="utf-8")) if Path(args.state).exists() else {}
    alpha = args.alpha if args.alpha is not None else meta.get("alpha", 0.5)
    c = meta.get("uct_c", UCT_C)
    pool = alive(nodes)
    total_visits = sum(s(n)["visits"] for n in pool) or 1

    print("=" * 70)
    print("搜索树")
    print("=" * 70)

    def walk(parent_id, depth):
        for n in sorted(children_of(nodes, parent_id), key=lambda x: -q(x)):
            st = s(n)
            pruned = (n.get("prune") or {}).get("pruned")
            selectable = not pruned and n.get("status") in SELECTABLE_STATUS
            if pruned:
                tag = f"  ✂ {(n.get('prune') or {}).get('mask')}"
            elif not selectable:
                tag = f"  ⏸ {n.get('status')}"
            else:
                tag = ""
            u = uct(n, total_visits, c)
            # 不可选节点（已剪枝 / shelved / refuted / impl_failed）不参与 selection，
            # 显示 UCT 会让人以为它们还在候选池里
            us = "—" if not selectable else ("∞" if u == float("inf") else f"{u:.2f}")
            print(f"{'  ' * depth}{'└─ ' if depth else ''}{n['id']:<14} "
                  f"visits={st['visits']:<3} Q={q(n):.3f} UCT={us:<6} "
                  f"{n.get('title','')[:38]}{tag}")
            walk(n.get("id"), depth + 1)

    walk(None, 0)

    expansions = sum(s(n).get("expansions", 1 if s(n).get("expanded") else 0) for n in nodes)
    budget = meta.get("budget_expansions")
    print(f"\n扩展次数: {expansions}" + (f" / 预算 {budget}" if budget else ""))
    if budget and expansions >= budget:
        print("  ⚠️ 已达扩展预算上限")

    masks: dict[str, int] = {}
    for n in nodes:
        pr = n.get("prune") or {}
        if pr.get("pruned"):
            masks[pr.get("mask", "?")] = masks.get(pr.get("mask", "?"), 0) + 1
    if masks:
        print("剪枝统计: " + ", ".join(f"{k}={v}" for k, v in sorted(masks.items())))
        print("  剪枝精度需人工复核：被剪节点里有多少确实该剪")

    tok = sum(float((n.get("cost") or {}).get("tokens_total") or 0) for n in nodes)
    calls = sum(float((n.get("cost") or {}).get("external_calls") or 0) for n in nodes)
    if tok or calls:
        print(f"累计成本: tokens_total={tok:g}, external_calls={calls:g}")

    if args.provenance:
        print("\n" + "=" * 70)
        print("reward 成分来源（逐节点）")
        print("=" * 70)
        n_llm_only = 0
        for n in pool:
            r, detail = reward(n, nodes, alpha)
            comps = verifiable_components(n, nodes)
            print(f"\n  {n['id']}  reward={r:.3f}")
            print(f"    v_model      = {detail.get('v_model')}   ← LLM 评分（scores.composite）")
            print(f"    v_verifiable = {detail.get('v_verifiable')}")
            for k, (v, src) in comps.items():
                print(f"        {k:<17}={v:.3f}  ← {src}")
            if not comps:
                n_llm_only += 1
                print("        （无可验证成分）")
        if n_llm_only:
            print(f"\n⚠️ {n_llm_only}/{len(pool)} 个节点的 reward 完全来自 LLM 评分。")
            print("   在这种情况下扩大搜索只会放大评分模型的偏好，不会提高 idea 质量。")
            print("   补救方向见 README 的 Roadmap「reward 的非 LLM 信号」。")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--path", default=str(DEFAULT_PATH))
    ap.add_argument("--state", default="outputs/SEARCH_STATE.json")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init"); p.add_argument("--budget", type=int, default=8)
    p.add_argument("--alpha", type=float, default=0.5); p.add_argument("--c", type=float, default=UCT_C)
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("mask"); p.add_argument("--apply", action="store_true")
    p.set_defaults(func=cmd_mask)

    p = sub.add_parser("select"); p.add_argument("-k", type=int, default=3)
    p.add_argument("--c", type=float, default=None); p.add_argument("--alpha", type=float, default=None)
    p.set_defaults(func=cmd_select)

    p = sub.add_parser("expand"); p.add_argument("id"); p.add_argument("--children", required=True)
    p.set_defaults(func=cmd_expand)

    p = sub.add_parser("backup"); p.add_argument("id"); p.add_argument("--value", type=float, default=None)
    p.add_argument("--alpha", type=float, default=None); p.set_defaults(func=cmd_backup)

    p = sub.add_parser("report"); p.add_argument("--provenance", action="store_true")
    p.add_argument("--alpha", type=float, default=None); p.set_defaults(func=cmd_report)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
