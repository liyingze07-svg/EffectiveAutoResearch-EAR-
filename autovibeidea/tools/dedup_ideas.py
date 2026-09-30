#!/usr/bin/env python3
"""Flag potentially duplicate idea pairs in IDEA_NODES.jsonl.

**This flags candidates; it does not adjudicate duplicates.** Cheap lexical/structural overlap identifies **pairs worth reviewing**;
high lexical overlap does not imply duplicate mechanisms (one mechanism can be reworded, and different mechanisms can share terminology).
Output therefore contains candidate pairs and overlap evidence only; **a model or human adjudicates actual duplication**, then uses
`mark` to set `prune.mask=duplicate` after confirmation.

Commands
----
pairs   Print candidate duplicate pairs and overlap evidence for adjudication
mark    For a confirmed pair, prune the lower-composite node as duplicate

Example
----
python3 tools/dedup_ideas.py pairs --threshold 0.45
python3 tools/dedup_ideas.py mark IDEA-03 IDEA-07 --reason "Same mechanism, different wording"
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

# These words occur throughout idea descriptions in this field and add no discrimination
STOP = {
    "the", "a", "an", "of", "for", "to", "and", "or", "in", "on", "with", "by", "is", "are",
    "we", "our", "that", "this", "it", "as", "at", "from", "be", "can", "via", "using", "use",
    "show", "shows", "propose", "proposed", "method", "approach", "model", "models", "framework",
    "novel", "new", "improve", "improves", "better", "task", "tasks", "data", "based",
    "\u7684", "\u4e86", "\u548c", "\u4e0e", "\u5728", "\u662f", "\u5bf9", "\u628a", "\u6211\u4eec", "\u4e00\u4e2a", "\u8fd9\u4e2a", "\u65b9\u6cd5", "\u6a21\u578b", "\u6846\u67b6",
    # LaTeX residue: actual runs leak \text{}, \mathbb{}, etc. into tokens, creating meaningless shared words
    "text", "mathbb", "mathrm", "mathcal", "frac", "left", "right", "begin", "end",
    "align", "equation", "cdot", "quad", "operatorname", "hat", "tilde", "bar",
}
CJK_RUN = re.compile(r"[\u4e00-\u9fff]{2,}")

# Lexical overlap misses alternate names for the same mechanism (abstention and reject option).
# This table normalizes common expressions of a concept to one #concept token.
# **This is domain-specific; extend it for your subfield**. Unlisted synonyms can still be missed.
CONCEPTS: dict[str, tuple[str, ...]] = {
    "abstain": ("abstention", "abstain", "reject option", "reject-option", "rejection option",
                "selective prediction", "selective classification", "\u5f03\u6743", "\u62d2\u8bc6", "\u9009\u62e9\u6027\u9884\u6d4b"),
    "coverage": ("conformal", "coverage guarantee", "coverage-guaranteed", "calibrated coverage",
                 "split conformal", "\u8986\u76d6\u4fdd\u8bc1", "\u6821\u51c6\u8986\u76d6"),
    "budget": ("budget", "cost-aware", "token budget", "compute budget", "\u9884\u7b97", "\u6210\u672c"),
    "stopping": ("early stopping", "optimal stopping", "halting", "stop rule", "\u505c\u6b62", "\u7ec8\u6b62"),
    "routing": ("routing", "router", "dispatch", "allocation", "\u8def\u7531", "\u8c03\u5ea6", "\u5206\u914d"),
    "toolcall": ("tool call", "tool-calling", "tool invocation", "tool use", "function call",
                 "\u5de5\u5177\u8c03\u7528", "\u8c03\u7528\u5de5\u5177"),
    "handoff": ("handoff", "escalation", "escalate", "human handoff", "\u79fb\u4ea4", "\u5347\u7ea7"),
    "uncertainty": ("uncertainty", "confidence", "calibration", "\u4e0d\u786e\u5b9a\u6027", "\u7f6e\u4fe1\u5ea6", "\u6821\u51c6"),
    "distill": ("distillation", "distill", "teacher-student", "\u84b8\u998f"),
    "memory": ("memory", "eviction", "retention", "\u8bb0\u5fc6", "\u6dd8\u6c70"),
}

FIELDS = {  # Field -> weight. Mechanism descriptions discriminate ideas best; titles share words most easily
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
    """Concept tokens + Latin-word tokens + CJK character bigrams."""
    text = unicodedata.normalize("NFKC", text).lower()
    out: set[str] = set()
    # Normalize concepts first: add #concept on a match to make synonymous expressions comparable
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
    """Find field values reused verbatim across nodes (template/placeholder text).

    Such text inflates similarity: for example, when every node has the same placeholder thesis,
    that field always has jaccard 1.0. Skip boilerplate fields during comparison.
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
            continue           # Both values are boilerplate; this field has no discriminative value
        ta, tb = tokens(va), tokens(vb)
        if not ta or not tb:
            continue
        inter = ta & tb
        jac = len(inter) / len(ta | tb)
        # containment captures paraphrased duplicates where one idea is a subset of the other
        cont = len(inter) / min(len(ta), len(tb))
        score = max(jac, 0.7 * cont)
        detail[field] = {"jaccard": round(jac, 3), "containment": round(cont, 3),
                         "shared": sorted(inter)[:8]}
        acc += weight * score
        total_w += weight
    return (acc / total_w if total_w else 0.0), detail


def same_lineage(a: dict, b: dict, by_id: dict[str, dict]) -> bool:
    """Ancestor-descendant nodes are naturally similar through refinement and must not be flagged as duplicates."""
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
        raise SystemExit(f"{path} not found (run python3 tools/idea_nodes.py init first)")
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def cmd_pairs(args) -> int:
    nodes = [n for n in load(Path(args.path)) if n.get("status") != "pruned" or args.include_pruned]
    if len(nodes) < 2:
        print("Fewer than 2 nodes; no comparison needed")
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
    # A threshold alone is unreliable: equivalent mechanisms may have low lexical overlap. Always show the top-K for adjudication as well.
    extra = [r for r in scored if r not in over][: max(0, args.top - len(over))]
    rows = over + extra
    if skipped_lineage:
        print(f"(Skipped {skipped_lineage} ancestor-descendant pairs)")
    if n_boiler:
        fields = ", ".join(f for f, v in boilerplate.items() if v)
        print(f"(Detected {n_boiler} verbatim boilerplate values; skipped comparison for these fields: {fields})")
    if not rows:
        print(f"✅ No comparable node pairs")
        return 0

    print(f"⚠️ {len(over)} pairs exceed threshold {args.threshold}; also showing {len(extra)} highest-similarity pairs for adjudication")
    print("   Lexical overlap does not imply duplicate mechanisms, or vice versa: paraphrases of the same mechanism can have low overlap.")
    print("   Judge each pair to determine whether it describes the same mechanism in different words.\n")
    for score, same_anchor, a, b, detail in rows:
        ca = (a.get("scores") or {}).get("composite")
        cb = (b.get("scores") or {}).get("composite")
        flag = ", anchored to the same evidence" if same_anchor else ""
        print(f"  {a['id']} (composite={ca})  ↔  {b['id']} (composite={cb})   similarity={score:.2f}{flag}")
        print(f"    {a.get('title','')[:70]}")
        print(f"    {b.get('title','')[:70]}")
        for field, d in detail.items():
            if d["shared"]:
                print(f"      {field}: jac={d['jaccard']} cont={d['containment']} shared terms={d['shared']}")
        print(f"    If adjudication confirms duplication: python3 tools/dedup_ideas.py mark {a['id']} {b['id']} --reason \"...\"")
        print()
    return 1 if (args.strict and over) else 0


def cmd_mark(args) -> int:
    path = Path(args.path)
    nodes = load(path)
    by_id = {n.get("id"): n for n in nodes}
    for nid in (args.id_a, args.id_b):
        if nid not in by_id:
            print(f"Node {nid} not found", file=sys.stderr)
            return 1
    a, b = by_id[args.id_a], by_id[args.id_b]

    def comp(n):
        v = (n.get("scores") or {}).get("composite")
        return float(v) if v is not None else -1.0

    loser, keeper = (a, b) if comp(a) <= comp(b) else (b, a)
    loser["status"] = "pruned"
    loser["prune"] = {"pruned": True, "mask": "duplicate",
                      "reason": args.reason or f"Duplicates the mechanism in {keeper['id']} (human/model adjudication)",
                      "duplicate_of": keeper["id"]}
    path.write_text("".join(json.dumps(n, ensure_ascii=False) + "\n" for n in nodes), encoding="utf-8")
    print(f"Marked {loser['id']} as duplicate (kept {keeper['id']})")
    print("Tip: pruned nodes remain in the file so pruning volume and precision can be measured")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--path", default=str(DEFAULT_PATH))
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pairs")
    p.add_argument("--threshold", type=float, default=0.25,
                   help="Default 0.25. **This threshold has not been calibrated on labeled data**; it comes from a few manual examples. Use the --top ranking as the primary reference")
    p.add_argument("--top", type=int, default=5, help="Always show the N most similar pairs for adjudication, regardless of threshold (default 5)")
    p.add_argument("--include-pruned", action="store_true")
    p.add_argument("--strict", action="store_true", help="Exit with code 1 when candidate pairs exist (for CI)")
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
