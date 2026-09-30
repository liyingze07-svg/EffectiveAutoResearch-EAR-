#!/usr/bin/env python3
"""Compute high-entropy regions and failure modes from LANDSCAPE.json as additional input to idea-gen Phase 2a.

High-entropy regions
--------
For each claim, collect papers' stance labels, compute empirical entropy H, and apply a **comparability penalty**:

    score = H(stances) / log2(k_labels)  ×  comparability

`comparability` ∈ [0,1] measures whether these papers reach different conclusions under comparable conditions.
**Without this penalty, most computed high entropy is spurious conflict**: different datasets, scales, and metrics naturally yield
different conclusions; this reflects different settings rather than disagreement in the field. Comparability is estimated automatically from each
observation's `setting` fields (dataset / scale / metric) in LANDSCAPE.json: identical settings=1.0,
with weighted deductions for mismatches in each field.

Failure modes
--------
Extract `(method, failure condition)` from each paper's `limitations` / `negative_results` fields,
and group by failure condition. **Multiple papers failing under the same condition without a direct explanation** is a high-value target.

Input format (optional LANDSCAPE.json extension fields produced by /lit-survey)
--------------------------------------------------------------
{
  "claims": [
    {"id": "C1", "statement": "...",
     "observations": [
        {"paper": "P01", "stance": "supports|refutes|conditional",
         "setting": {"dataset": "ImageNet", "scale": "7B", "metric": "top-1"}}
     ]}
  ],
  "papers": [
    {"id": "P01", "limitations": ["Fails on long contexts"], "negative_results": ["..."]}
  ]
}

Usage
----
python3 tools/entropy_map.py outputs/LANDSCAPE.json            # Human-readable report
python3 tools/entropy_map.py outputs/LANDSCAPE.json --json     # Machine-readable input for Phase 2a
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

STANCES = ("supports", "refutes", "conditional")
# Comparability penalty weights: metric mismatches are most consequential (changing metrics often reverses conclusions)
SETTING_WEIGHTS = {"metric": 0.45, "dataset": 0.35, "scale": 0.20}


def entropy(labels: list[str]) -> float:
    """Normalized Shannon entropy over stance labels; 0 = unanimous, 1 = maximal split."""
    if len(labels) < 2:
        return 0.0
    counts = Counter(labels)
    n = sum(counts.values())
    h = -sum((c / n) * math.log2(c / n) for c in counts.values())
    max_h = math.log2(min(len(counts), len(STANCES))) if len(counts) > 1 else 1.0
    return max(0.0, h / max_h) if max_h else 0.0   # Avoid floating-point -0.0


def _setting_tokens(value: str) -> set[str]:
    """Tokenize setting values for graded comparison.

    Model-generated settings are often free text (e.g., normalized return and convergence speed),
    **Exact string matching almost always declares a mismatch**, making comparability constantly 0 and defeating the feature.
    Use graded token-level agreement instead.
    """
    v = re.sub(r"[^\w\u4e00-\u9fff]+", " ", str(value).lower())
    drop = {"and", "the", "of", "with", "on", "in", "a", "an", "to", "for", "up"}
    return {w for w in v.split() if w and w not in drop and len(w) > 1}


def _agreement(values: list[str]) -> float:
    """Mean pairwise Jaccard across observations; 1.0 = identical, 0.0 = no overlap."""
    sets = [s for s in (_setting_tokens(v) for v in values) if s]
    if len(sets) < 2:
        return 1.0
    pairs, total = 0, 0.0
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            union = sets[i] | sets[j]
            total += len(sets[i] & sets[j]) / len(union) if union else 1.0
            pairs += 1
    return total / pairs if pairs else 1.0


def comparability(observations: list[dict]) -> tuple[float, list[str]]:
    """1.0 = closely matched settings (genuine disagreement); lower values suggest differences in settings.

    Graded calculation: discount each field by token-level agreement rather than binary equality.
    """
    if len(observations) < 2:
        return 1.0, []
    penalty, notes = 0.0, []
    for key, weight in SETTING_WEIGHTS.items():
        values = [str((o.get("setting") or {}).get(key, "")).strip()
                  for o in observations]
        present = [v for v in values if v and v.lower() not in ("unknown", "n/a", "\u672a\u77e5")]
        if not present:
            penalty += weight * 0.5
            notes.append(f"{key} not recorded")
            continue
        if len(present) < len(values):
            penalty += weight * 0.25
            notes.append(f"{key} partially missing ({len(present)}/{len(values)} values present)")
        agree = _agreement(present)
        penalty += weight * (1.0 - agree)
        if agree < 0.5:
            notes.append(f"{key} low agreement {agree:.2f} ({' / '.join(sorted(set(present))[:3])})")
        elif agree < 0.95:
            notes.append(f"{key} partial agreement {agree:.2f}")
    return max(0.0, 1.0 - penalty), notes


def analyze_claims(landscape: dict) -> list[dict]:
    rows = []
    for claim in landscape.get("claims", []) or []:
        obs = claim.get("observations", []) or []
        stances = [o.get("stance", "") for o in obs if o.get("stance")]
        unknown = {s for s in stances} - set(STANCES)
        h = entropy(stances)
        comp, notes = comparability(obs)
        rows.append({
            "id": claim.get("id"),
            "statement": claim.get("statement", ""),
            "n_papers": len(obs),
            "stance_counts": dict(Counter(stances)),
            "entropy": round(h, 3),
            "comparability": round(comp, 3),
            "score": round(h * comp, 3),
            "comparability_notes": notes,
            "papers": [o.get("paper") for o in obs],
            "warnings": ([f"Unknown stance labels: {sorted(unknown)}"] if unknown else [])
                       + (["Fewer than 3 observations; entropy estimate is unstable"] if len(obs) < 3 else []),
        })
    rows.sort(key=lambda r: -r["score"])
    return rows


def analyze_failures(landscape: dict) -> list[dict]:
    """Group (method, condition) pairs by failure condition; a condition shared by multiple papers is a high-value target."""
    buckets: dict[str, list[dict]] = defaultdict(list)
    for paper in landscape.get("papers", []) or []:
        texts = list(paper.get("limitations") or []) + list(paper.get("negative_results") or [])
        for text in texts:
            key = normalize_condition(text)
            if key:
                buckets[key].append({"paper": paper.get("id"),
                                     "method": paper.get("method", ""), "raw": text})
    rows = [{"condition": k, "n_papers": len({e["paper"] for e in v}),
             "entries": v} for k, v in buckets.items()]
    rows.sort(key=lambda r: -r["n_papers"])
    return rows


def normalize_condition(text: str) -> str:
    """Reduce failure descriptions to coarse condition keys. Sufficient for clustering; clusters require human review."""
    t = re.sub(r"\s+", " ", text.strip().lower())
    t = re.sub(r"^(we |our |the |this )?(method|approach|model)s? ", "", t)
    return t[:80]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("landscape", help="outputs/LANDSCAPE.json")
    ap.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    ap.add_argument("--min-score", type=float, default=0.3, help="Minimum score for high-entropy regions (default 0.3)")
    args = ap.parse_args()

    path = Path(args.landscape)
    if not path.exists():
        print(f"{path} not found (run /lit-survey first)", file=sys.stderr)
        return 2
    landscape = json.loads(path.read_text(encoding="utf-8"))

    claims, failures = analyze_claims(landscape), analyze_failures(landscape)
    if args.json:
        print(json.dumps({"entropy_map": claims, "failure_modes": failures},
                         ensure_ascii=False, indent=2))
        return 0

    if not claims and not failures:
        print("LANDSCAPE.json has no claims / limitations fields.")
        print("These fields are optional /lit-survey extensions: without them this tool produces no output, and the pipeline is unaffected.")
        return 0

    print("=" * 66)
    print("High-entropy regions (conclusion disagreement x condition comparability)")
    print("=" * 66)
    hi = [c for c in claims if c["score"] >= args.min_score]
    if not hi:
        print(f"No claim has score >= {args.min_score} ({len(claims)} claims total)")
    for c in hi:
        print(f"\n[{c['id']}] score={c['score']}  (entropy={c['entropy']} x comparability={c['comparability']})")
        print(f"  {c['statement'][:90]}")
        print(f"  Stance distribution: {c['stance_counts']}  Papers: {c['papers']}")
        if c["comparability_notes"]:
            print(f"  ⚠️ Reasons for the comparability discount: {'; '.join(c['comparability_notes'])}")
            print("     -> If setting mismatches drive the discount, this is more likely spurious conflict than disagreement in the field")
        for w in c["warnings"]:
            print(f"  ⚠️ {w}")
    low = [c for c in claims if c["entropy"] >= 0.6 and c["comparability"] < 0.5]
    if low:
        print("\n" + "=" * 66)
        print("Comparability gaps (high entropy with incomparable conditions)")
        print("=" * 66)
        print("The literature disagrees on these claims, but observations differ in dataset / scale / metric,")
        print("so **do not attack them as established contradictions in the field**.")
        print("They define another target: **nobody has tested the claim under comparable conditions**.")
        print("Designing matched-condition experiments (same encoder/compute/data scale/metric) and drawing causal conclusions")
        print("is itself a publishable untested-assumption contribution. This differs from attacking high-entropy regions; do not conflate them.\n")
        for c in low:
            print(f"  [{c['id']}] entropy={c['entropy']:.2f} comparability={c['comparability']:.2f}")
            print(f"    {c['statement'][:88]}")
            print(f"    Stances: {c['stance_counts']}  Papers: {c['papers']}")
            print(f"    Reasons conditions are incomparable: {'; '.join(c['comparability_notes'])}")
            print("    -> Minimal comparable design: hold all other conditions fixed and vary only the factor asserted by the claim\n")

    print("\n" + "=" * 66)
    print("Failure modes (multiple papers failing under the same condition = high-value target)")
    print("=" * 66)
    multi = [f for f in failures if f["n_papers"] >= 2]
    if not multi:
        print(f"No failure conditions shared across papers ({len(failures)} single-paper records)")
    for f in multi:
        print(f"\n[{f['n_papers']} papers] {f['condition']}")
        for e in f["entries"][:4]:
            print(f"    {e['paper']}: {e['raw'][:70]}")
    print("\nNote: failure conditions are clustered through text normalization; these coarse clusters require human review.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
