#!/usr/bin/env python3
"""标记 IDEA_NODES.jsonl 中可能重复的 idea 对。

**这是一个标记器，不是判定器。** 它用廉价的词法/结构重叠找出**值得复核的候选对**；
词法重叠高不等于机制重复（同一机制可以换词表述，不同机制也可以共用术语）。
因此输出只给候选对与重叠证据，**是否真重复由模型或人裁定**，确认后再用
`mark` 写入 `prune.mask=duplicate`。

命令
----
pairs   打印候选重复对 + 重叠证据（供裁定）
mark    对已确认的一对，把 composite 较低的一方标记为 duplicate 剪枝

示例
----
python3 tools/dedup_ideas.py pairs --threshold 0.45
python3 tools/dedup_ideas.py mark IDEA-03 IDEA-07 --reason "同一机制，仅表述不同"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from itertools import combinations
from pathlib import Path

DEFAULT_PATH = Path("outputs/IDEA_NODES.jsonl")

# 这些词在本领域的 idea 描述里几乎处处出现，对区分度没有贡献
STOP = {
    "the", "a", "an", "of", "for", "to", "and", "or", "in", "on", "with", "by", "is", "are",
    "we", "our", "that", "this", "it", "as", "at", "from", "be", "can", "via", "using", "use",
    "show", "shows", "propose", "proposed", "method", "approach", "model", "models", "framework",
    "novel", "new", "improve", "improves", "better", "task", "tasks", "data", "based",
    "的", "了", "和", "与", "在", "是", "对", "把", "我们", "一个", "这个", "方法", "模型", "框架",
    # LaTeX 残留：真实 run 中 \text{} \mathbb{} 等会漏成 token，成为无意义的共享词
    "text", "mathbb", "mathrm", "mathcal", "frac", "left", "right", "begin", "end",
    "align", "equation", "cdot", "quad", "operatorname", "hat", "tilde", "bar",
}
CJK_RUN = re.compile(r"[\u4e00-\u9fff]{2,}")

# 词法重叠抓不到"同一机制的不同叫法"（abstention 与 reject option）。
# 这张表把同一概念的常见表述归一到一个 #concept token。
# **它是领域相关的，请按自己的子领域扩充** —— 覆盖不到的同义词仍会漏报。
CONCEPTS: dict[str, tuple[str, ...]] = {
    "abstain": ("abstention", "abstain", "reject option", "reject-option", "rejection option",
                "selective prediction", "selective classification", "弃权", "拒识", "选择性预测"),
    "coverage": ("conformal", "coverage guarantee", "coverage-guaranteed", "calibrated coverage",
                 "split conformal", "覆盖保证", "校准覆盖"),
    "budget": ("budget", "cost-aware", "token budget", "compute budget", "预算", "成本"),
    "stopping": ("early stopping", "optimal stopping", "halting", "stop rule", "停止", "终止"),
    "routing": ("routing", "router", "dispatch", "allocation", "路由", "调度", "分配"),
    "toolcall": ("tool call", "tool-calling", "tool invocation", "tool use", "function call",
                 "工具调用", "调用工具"),
    "handoff": ("handoff", "escalation", "escalate", "human handoff", "移交", "升级"),
    "uncertainty": ("uncertainty", "confidence", "calibration", "不确定性", "置信度", "校准"),
    "distill": ("distillation", "distill", "teacher-student", "蒸馏"),
    "memory": ("memory", "eviction", "retention", "记忆", "淘汰"),
}

FIELDS = {  # 字段 -> 权重。机制描述最能区分 idea，标题最容易撞词
    "title": 0.2,
    "thesis": 0.3,
    "hypothesis.core": 0.5,
}


def _get(node: dict, dotted: str) -> str:
    cur: object = node
    for k in dotted.split("."):
        if not isinstance(cur, dict):
            return ""
        cur = cur.get(k)
    return cur if isinstance(cur, str) else ""


def tokens(text: str) -> set[str]:
    """概念 token + 拉丁词 token + CJK 字符二元组。"""
    text = unicodedata.normalize("NFKC", text).lower()
    out: set[str] = set()
    # 概念归一优先：命中即加 #concept，使同义表述可比
    for concept, surfaces in CONCEPTS.items():
        if any(s in text for s in surfaces):
            out.add(f"#{concept}")
    for word in re.findall(r"[a-z0-9][a-z0-9\-_]*", text):
        if word not in STOP and len(word) > 2:
            out.add(word)
    for run in CJK_RUN.findall(text):
        for i in range(len(run) - 1):
            bigram = run[i : i + 2]
            if bigram not in STOP:
                out.add(bigram)
    return out


def find_boilerplate(nodes: list[dict]) -> dict[str, set[str]]:
    """找出被多个节点逐字复用的字段值（模板/占位文本）。

    这类文本会把相似度抬到虚高——例如所有节点的 thesis 都写着同一句占位说明时，
    该字段的 jaccard 恒为 1.0。命中样板的字段在比较时跳过。
    """
    from collections import Counter
    threshold = max(3, int(len(nodes) * 0.4))
    boiler: dict[str, set[str]] = {}
    for field in FIELDS:
        counts = Counter(_get(n, field).strip() for n in nodes if _get(n, field).strip())
        boiler[field] = {v for v, c in counts.items() if c >= threshold}
    return boiler


def similarity(a: dict, b: dict, boilerplate: dict[str, set[str]] | None = None) -> tuple[float, dict]:
    """Weighted Jaccard/containment over selected fields; also returns per-field detail."""
    total_w, acc, detail = 0.0, 0.0, {}
    boilerplate = boilerplate or {}
    for field, weight in FIELDS.items():
        va, vb = _get(a, field).strip(), _get(b, field).strip()
        skip = boilerplate.get(field, set())
        if va in skip and vb in skip:
            continue           # 双方都是样板文本，该字段无区分度
        ta, tb = tokens(va), tokens(vb)
        if not ta or not tb:
            continue
        inter = ta & tb
        jac = len(inter) / len(ta | tb)
        # containment 捕捉"一个 idea 是另一个的子集"这种改写式重复
        cont = len(inter) / min(len(ta), len(tb))
        score = max(jac, 0.7 * cont)
        detail[field] = {"jaccard": round(jac, 3), "containment": round(cont, 3),
                         "shared": sorted(inter)[:8]}
        acc += weight * score
        total_w += weight
    return (acc / total_w if total_w else 0.0), detail


def same_lineage(a: dict, b: dict, by_id: dict[str, dict]) -> bool:
    """祖先-后代关系的两个节点天然相似（精炼派生），不应报为重复。"""
    def chain(node: dict) -> set[str]:
        seen, cur = set(), node
        while cur is not None:
            nid = cur.get("id")
            if nid in seen:
                break
            seen.add(nid)
            cur = by_id.get(cur.get("parent_id"))
        return seen
    return a.get("id") in chain(b) or b.get("id") in chain(a)


def load(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"未找到 {path}（先跑 python3 tools/idea_nodes.py init）")
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def cmd_pairs(args) -> int:
    nodes = [n for n in load(Path(args.path)) if n.get("status") != "pruned" or args.include_pruned]
    if len(nodes) < 2:
        print("节点不足 2 个，无需比较")
        return 0
    by_id = {n.get("id"): n for n in load(Path(args.path))}
    boilerplate = find_boilerplate(nodes)
    n_boiler = sum(len(v) for v in boilerplate.values())
    scored = []
    skipped_lineage = 0
    for a, b in combinations(nodes, 2):
        if same_lineage(a, b, by_id):
            skipped_lineage += 1
            continue
        score, detail = similarity(a, b, boilerplate)
        same_anchor = bool(
            set((a.get("generator") or {}).get("anchor", []))
            & set((b.get("generator") or {}).get("anchor", []))
        )
        scored.append((score, same_anchor, a, b, detail))
    scored.sort(key=lambda r: -r[0])

    over = [r for r in scored if r[0] >= args.threshold or (r[1] and r[0] >= args.threshold * 0.7)]
    # 阈值单独用不可靠：同义机制的词法重叠可能很低。因此总是额外呈现 top-K 供裁定。
    extra = [r for r in scored if r not in over][: max(0, args.top - len(over))]
    rows = over + extra
    if skipped_lineage:
        print(f"（跳过 {skipped_lineage} 组祖先-后代关系的节点对）")
    if n_boiler:
        fields = ", ".join(f for f, v in boilerplate.items() if v)
        print(f"（检测到 {n_boiler} 处逐字复用的样板文本，已在这些字段上跳过比较：{fields}）")
    if not rows:
        print(f"✅ 无可比较的节点对")
        return 0

    print(f"⚠️ {len(over)} 组超过阈值 {args.threshold}，另附 {len(extra)} 组相似度最高的待裁定对")
    print("   词法重叠 ≠ 机制重复，反之亦然：换词表述的同一机制重叠可能很低。")
    print("   请逐对判断是否为同一机制的不同表述。\n")
    for score, same_anchor, a, b, detail in rows:
        ca = (a.get("scores") or {}).get("composite")
        cb = (b.get("scores") or {}).get("composite")
        flag = "，且锚定同一证据" if same_anchor else ""
        print(f"  {a['id']} (composite={ca})  ↔  {b['id']} (composite={cb})   相似度={score:.2f}{flag}")
        print(f"    {a.get('title','')[:70]}")
        print(f"    {b.get('title','')[:70]}")
        for field, d in detail.items():
            if d["shared"]:
                print(f"      {field}: jac={d['jaccard']} cont={d['containment']} 共享词={d['shared']}")
        print(f"    裁定后如确认重复: python3 tools/dedup_ideas.py mark {a['id']} {b['id']} --reason \"...\"")
        print()
    return 1 if (args.strict and over) else 0


def cmd_mark(args) -> int:
    path = Path(args.path)
    nodes = load(path)
    by_id = {n.get("id"): n for n in nodes}
    for nid in (args.id_a, args.id_b):
        if nid not in by_id:
            print(f"未找到节点 {nid}", file=sys.stderr)
            return 1
    a, b = by_id[args.id_a], by_id[args.id_b]

    def comp(n):
        v = (n.get("scores") or {}).get("composite")
        return float(v) if v is not None else -1.0

    loser, keeper = (a, b) if comp(a) <= comp(b) else (b, a)
    loser["status"] = "pruned"
    loser["prune"] = {"pruned": True, "mask": "duplicate",
                      "reason": args.reason or f"与 {keeper['id']} 机制重复（人工/模型裁定）",
                      "duplicate_of": keeper["id"]}
    path.write_text("".join(json.dumps(n, ensure_ascii=False) + "\n" for n in nodes), encoding="utf-8")
    print(f"已将 {loser['id']} 标记为 duplicate（保留 {keeper['id']}）")
    print("提示: 被剪节点仍保留在文件中，便于统计剪枝量与剪枝精度")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--path", default=str(DEFAULT_PATH))
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pairs")
    p.add_argument("--threshold", type=float, default=0.25,
                   help="默认 0.25。**该阈值未在标注数据上校准**，仅由少量手工样例定出；请以 --top 的排序结果为主要依据")
    p.add_argument("--top", type=int, default=5, help="无论是否超阈值，总是呈现相似度最高的 N 对供裁定（默认 5）")
    p.add_argument("--include-pruned", action="store_true")
    p.add_argument("--strict", action="store_true", help="有候选对时返回退出码 1（供 CI 使用）")
    p.set_defaults(func=cmd_pairs)
    m = sub.add_parser("mark")
    m.add_argument("id_a")
    m.add_argument("id_b")
    m.add_argument("--reason")
    m.set_defaults(func=cmd_mark)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
