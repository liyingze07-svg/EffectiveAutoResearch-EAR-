#!/usr/bin/env python3
"""Manage outputs/IDEA_NODES.jsonl — idea 作为可审查对象。

Schema 说明见 docs/IDEA_NODE_SCHEMA.md。

命令
----
init      建空文件（已存在则不动）
add       追加一个节点（--file node.json 或 --json '{...}'），写入前校验
update    改字段：--set status=pruned --set prune.mask=collision
validate  全量校验，返回非 0 表示有问题
stats     状态 / 算子 / mask / 成本汇总
tree      打印派生谱系
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_PATH = Path("outputs/IDEA_NODES.jsonl")

STATUSES = {"pending", "supported", "refuted", "impl_failed", "shelved", "pruned"}
OPERATORS = {"critique_anchored", "fossil_hunt", "entropy_region", "failure_mode", "manual"}
MASKS = {"collision", "not_feasible", "fit_below_threshold", "duplicate", "critique_saturated"}
FEASIBILITY = {"FEASIBLE", "CAVEATS", "NOT_FEASIBLE"}

REQUIRED = ("id", "status", "title", "generator")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    nodes = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            nodes.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{lineno} JSON 解析失败: {exc}")
    return nodes


def save(path: Path, nodes: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(n, ensure_ascii=False) + "\n" for n in nodes), encoding="utf-8"
    )


def validate_node(node: dict, known_ids: set[str]) -> list[str]:
    """Return a list of problems; empty means valid."""
    errs = []
    nid = node.get("id", "<no id>")
    for field in REQUIRED:
        if not node.get(field):
            errs.append(f"{nid}: 缺少必填字段 {field}")

    if node.get("status") not in STATUSES:
        errs.append(f"{nid}: status={node.get('status')!r} 不在 {sorted(STATUSES)}")

    gen = node.get("generator") or {}
    if gen and gen.get("operator") not in OPERATORS:
        errs.append(f"{nid}: generator.operator={gen.get('operator')!r} 不在 {sorted(OPERATORS)}")
    if gen and not gen.get("anchor"):
        errs.append(f"{nid}: generator.anchor 为空 — 每个 idea 必须锚定到具体证据 ID")

    parent = node.get("parent_id")
    if parent and parent not in known_ids:
        errs.append(f"{nid}: parent_id={parent!r} 指向不存在的节点")
    if parent == nid:
        errs.append(f"{nid}: parent_id 不能指向自身")

    scores = node.get("scores") or {}
    if scores:
        if not scores.get("source"):
            errs.append(f"{nid}: scores 存在但缺 scores.source — 分数必须记录由谁给出")
        if "degraded" not in scores:
            errs.append(f"{nid}: scores 存在但缺 scores.degraded — 必须记录外部模型是否降级为自评")
        for key in ("novelty", "venue", "strategic", "feasibility", "composite"):
            v = scores.get(key)
            if v is not None and not (0 <= float(v) <= 10):
                errs.append(f"{nid}: scores.{key}={v} 超出 0-10")
        rf = scores.get("researcher_fit")
        if rf is not None and not (4 <= float(rf) <= 20):
            errs.append(f"{nid}: scores.researcher_fit={rf} 超出 4-20")

    prune = node.get("prune") or {}
    if prune.get("pruned"):
        if prune.get("mask") not in MASKS:
            errs.append(f"{nid}: prune.mask={prune.get('mask')!r} 不在 {sorted(MASKS)}")
        if node.get("status") != "pruned":
            errs.append(f"{nid}: prune.pruned=true 但 status={node.get('status')!r}（应为 pruned）")
    if node.get("status") == "pruned" and not prune.get("pruned"):
        errs.append(f"{nid}: status=pruned 但 prune.pruned 未置 true")

    cw = node.get("closest_work") or {}
    if cw.get("ref") and not cw.get("delta"):
        errs.append(f"{nid}: closest_work 有 ref 但无 delta — 查新未完成")

    hyp = node.get("hypothesis") or {}
    if hyp.get("core") and not hyp.get("falsifier"):
        errs.append(f"{nid}: hypothesis.core 有但 falsifier 为空 — 假设不可否证")

    for i, claim in enumerate(node.get("theory_claims") or []):
        if claim.get("feasibility") not in FEASIBILITY:
            errs.append(f"{nid}: theory_claims[{i}].feasibility={claim.get('feasibility')!r} 非法")
    return errs


def _set_path(node: dict, dotted: str, raw: str) -> None:
    """Set node['a']['b'] = value from 'a.b=value', coercing obvious literals."""
    if raw in ("true", "false"):
        value: object = raw == "true"
    elif raw == "null":
        value = None
    else:
        try:
            value = int(raw)
        except ValueError:
            try:
                value = float(raw)
            except ValueError:
                value = raw
    keys = dotted.split(".")
    cur = node
    for k in keys[:-1]:
        cur = cur.setdefault(k, {})
        if not isinstance(cur, dict):
            raise SystemExit(f"字段 {dotted} 的中间层不是对象")
    cur[keys[-1]] = value


def cmd_init(args) -> int:
    path = Path(args.path)
    if path.exists():
        print(f"{path} 已存在，未改动（{len(load(path))} 个节点）")
        return 0
    save(path, [])
    print(f"已创建 {path}")
    return 0


def cmd_add(args) -> int:
    path = Path(args.path)
    nodes = load(path)
    payload = json.loads(Path(args.file).read_text(encoding="utf-8")) if args.file else json.loads(args.json)
    incoming = payload if isinstance(payload, list) else [payload]
    known = {n.get("id") for n in nodes}
    problems = []
    for node in incoming:
        node.setdefault("created_at", _now())
        node["updated_at"] = _now()
        if node.get("id") in known:
            problems.append(f"{node.get('id')}: id 重复")
            continue
        errs = validate_node(node, known | {n.get("id") for n in incoming})
        problems.extend(errs)
        if not errs:
            nodes.append(node)
            known.add(node.get("id"))
    if problems:
        print("校验失败，未写入：", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    save(path, nodes)
    print(f"已追加 {len(incoming)} 个节点，共 {len(nodes)}")
    return 0


def cmd_update(args) -> int:
    path = Path(args.path)
    nodes = load(path)
    target = next((n for n in nodes if n.get("id") == args.id), None)
    if target is None:
        print(f"未找到节点 {args.id}", file=sys.stderr)
        return 1
    for assignment in args.set:
        if "=" not in assignment:
            print(f"--set 需形如 field=value，收到 {assignment!r}", file=sys.stderr)
            return 1
        key, raw = assignment.split("=", 1)
        _set_path(target, key, raw)
    # 剪枝时自动保持 status 与 prune.pruned 一致
    if (target.get("prune") or {}).get("pruned"):
        target["status"] = "pruned"
    target["updated_at"] = _now()
    errs = validate_node(target, {n.get("id") for n in nodes})
    if errs:
        print("更新后校验失败，未写入：", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        return 1
    save(path, nodes)
    print(f"已更新 {args.id}")
    return 0


def cmd_validate(args) -> int:
    path = Path(args.path)
    nodes = load(path)
    ids = [n.get("id") for n in nodes]
    problems = [f"id 重复: {i}" for i, c in Counter(ids).items() if c > 1]
    known = set(ids)
    for node in nodes:
        problems.extend(validate_node(node, known))
    if problems:
        print(f"❌ {len(problems)} 个问题：")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"✅ {len(nodes)} 个节点全部通过校验")
    return 0


def cmd_stats(args) -> int:
    nodes = load(Path(args.path))
    if not nodes:
        print("无节点")
        return 0
    status = Counter(n.get("status") for n in nodes)
    ops = Counter((n.get("generator") or {}).get("operator") for n in nodes)
    masks = Counter((n.get("prune") or {}).get("mask") for n in nodes if (n.get("prune") or {}).get("pruned"))
    anchors = Counter(a for n in nodes for a in (n.get("generator") or {}).get("anchor", []))
    degraded = sum(1 for n in nodes if (n.get("scores") or {}).get("degraded"))
    scored = [float((n.get("scores") or {}).get("composite")) for n in nodes if (n.get("scores") or {}).get("composite") is not None]
    cost = defaultdict(float)
    for n in nodes:
        for k, v in (n.get("cost") or {}).items():
            cost[k] += float(v or 0)

    print(f"节点总数: {len(nodes)}")
    print("状态分布: " + ", ".join(f"{k}={v}" for k, v in status.most_common()))
    print("生成算子: " + ", ".join(f"{k}={v}" for k, v in ops.most_common()))
    if masks:
        print("剪枝 mask: " + ", ".join(f"{k}={v}" for k, v in masks.most_common()))
    if anchors:
        top = ", ".join(f"{k}×{v}" for k, v in anchors.most_common(5))
        print(f"锚定证据 (top5): {top}")
        sat = [k for k, v in anchors.items() if v > 3]
        if sat:
            print(f"  ⚠️ 单个证据锚定超过 3 个 idea: {sat} — 多样性约束已被突破")
    if scored:
        print(f"composite: n={len(scored)} 均值={sum(scored)/len(scored):.2f} 最高={max(scored):.2f}")
    if degraded:
        print(f"⚠️ {degraded}/{len(nodes)} 个节点的分数来自降级自评，与正常评分不可比")
    if cost:
        print("累计成本: " + ", ".join(f"{k}={v:g}" for k, v in sorted(cost.items())))
    return 0


def cmd_tree(args) -> int:
    nodes = load(Path(args.path))
    children = defaultdict(list)
    for n in nodes:
        children[n.get("parent_id")].append(n)

    def walk(parent, depth):
        for n in children.get(parent, []):
            mark = ""
            if n.get("status") == "pruned":
                mark = f"  [剪枝: {(n.get('prune') or {}).get('mask')}]"
            comp = (n.get("scores") or {}).get("composite")
            score = f"  composite={comp}" if comp is not None else ""
            print(f"{'  ' * depth}{'└─ ' if depth else ''}{n.get('id')} {n.get('title', '')[:56]}{score}{mark}")
            walk(n.get("id"), depth + 1)

    walk(None, 0)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--path", default=str(DEFAULT_PATH), help=f"默认 {DEFAULT_PATH}")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init").set_defaults(func=cmd_init)
    p_add = sub.add_parser("add")
    src = p_add.add_mutually_exclusive_group(required=True)
    src.add_argument("--file")
    src.add_argument("--json")
    p_add.set_defaults(func=cmd_add)
    p_up = sub.add_parser("update")
    p_up.add_argument("id")
    p_up.add_argument("--set", action="append", default=[], metavar="field=value")
    p_up.set_defaults(func=cmd_update)
    sub.add_parser("validate").set_defaults(func=cmd_validate)
    sub.add_parser("stats").set_defaults(func=cmd_stats)
    sub.add_parser("tree").set_defaults(func=cmd_tree)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
