#!/usr/bin/env python3
"""从 LANDSCAPE.json 计算"高熵区域"与"失效模式"，作为 idea-gen Phase 2a 的额外输入。

高熵区域
--------
对同一 claim，收集各论文的立场标签，算经验熵 H，再乘**可比性惩罚**：

    score = H(stances) / log2(k_labels)  ×  comparability

`comparability` ∈ [0,1] 衡量这些论文是否在可比条件下得出不同结论。
**没有这个惩罚，算出来的"高熵"大半是伪冲突**——数据集、规模、指标不同本来就会得到
不同结论，那不是领域的分歧，只是设定不同。可比性由 LANDSCAPE.json 中每条
观测的 `setting` 字段（dataset / scale / metric）自动估计：设定完全一致=1.0，
逐项不一致按权重扣减。

失效模式
--------
从每篇论文的 `limitations` / `negative_results` 字段抽取 `(方法, 失效条件)`，
按失效条件聚合。**多篇论文在同一条件下都失效、却没人正面解释**，是高价值目标。

输入格式（LANDSCAPE.json 的可选扩展字段，由 /lit-survey 产出）
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
    {"id": "P01", "limitations": ["长上下文下失效"], "negative_results": ["..."]}
  ]
}

用法
----
python3 tools/entropy_map.py outputs/LANDSCAPE.json            # 人读报告
python3 tools/entropy_map.py outputs/LANDSCAPE.json --json     # 机读，供 Phase 2a 注入
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
# 可比性惩罚权重：指标不一致最致命（换指标常直接翻转结论）
SETTING_WEIGHTS = {"metric": 0.45, "dataset": 0.35, "scale": 0.20}


def entropy(labels: list[str]) -> float:
    """Normalized Shannon entropy over stance labels; 0 = unanimous, 1 = maximal split."""
    if len(labels) < 2:
        return 0.0
    counts = Counter(labels)
    n = sum(counts.values())
    h = -sum((c / n) * math.log2(c / n) for c in counts.values())
    max_h = math.log2(min(len(counts), len(STANCES))) if len(counts) > 1 else 1.0
    return max(0.0, h / max_h) if max_h else 0.0   # 避免浮点 -0.0


def _setting_tokens(value: str) -> set[str]:
    """把 setting 值切成 token，用于分级比较。

    模型写出的 setting 往往是自由文本（"normalized return and convergence speed"），
    **精确字符串比较几乎必然判为不一致**，会让可比性恒为 0、整个功能失效。
    因此改为 token 级的分级一致度。
    """
    v = re.sub(r"[^\w\u4e00-\u9fff]+", " ", str(value).lower())
    drop = {"and", "the", "of", "with", "on", "in", "a", "an", "to", "for", "up"}
    return {w for w in v.split() if w and w not in drop and len(w) > 1}


def _agreement(values: list[str]) -> float:
    """观测间的平均成对 Jaccard；1.0 = 完全一致，0.0 = 毫无重叠。"""
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
    """1.0 = 设定高度一致（分歧是真的）；越低说明越可能由设定差异导致。

    分级计算：每个字段按 token 级一致度打折，而不是"相等/不等"二值判断。
    """
    if len(observations) < 2:
        return 1.0, []
    penalty, notes = 0.0, []
    for key, weight in SETTING_WEIGHTS.items():
        values = [str((o.get("setting") or {}).get(key, "")).strip()
                  for o in observations]
        present = [v for v in values if v and v.lower() not in ("unknown", "n/a", "未知")]
        if not present:
            penalty += weight * 0.5
            notes.append(f"{key} 未记录")
            continue
        if len(present) < len(values):
            penalty += weight * 0.25
            notes.append(f"{key} 部分缺失（{len(present)}/{len(values)} 条有值）")
        agree = _agreement(present)
        penalty += weight * (1.0 - agree)
        if agree < 0.5:
            notes.append(f"{key} 一致度低 {agree:.2f}（{' / '.join(sorted(set(present))[:3])}）")
        elif agree < 0.95:
            notes.append(f"{key} 部分一致 {agree:.2f}")
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
            "warnings": ([f"未知 stance 标签: {sorted(unknown)}"] if unknown else [])
                       + (["观测数 < 3，熵估计不稳定"] if len(obs) < 3 else []),
        })
    rows.sort(key=lambda r: -r["score"])
    return rows


def analyze_failures(landscape: dict) -> list[dict]:
    """按失效条件聚合 (方法, 条件)；多篇论文共享同一条件 = 高价值目标。"""
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
    """把失效描述压成粗粒度条件键。粗糙但足以聚类；聚类结果需人工复核。"""
    t = re.sub(r"\s+", " ", text.strip().lower())
    t = re.sub(r"^(we |our |the |this )?(method|approach|model)s? ", "", t)
    return t[:80]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("landscape", help="outputs/LANDSCAPE.json")
    ap.add_argument("--json", action="store_true", help="输出机读 JSON")
    ap.add_argument("--min-score", type=float, default=0.3, help="高熵区域的最低 score（默认 0.3）")
    args = ap.parse_args()

    path = Path(args.landscape)
    if not path.exists():
        print(f"未找到 {path}（先跑 /lit-survey）", file=sys.stderr)
        return 2
    landscape = json.loads(path.read_text(encoding="utf-8"))

    claims, failures = analyze_claims(landscape), analyze_failures(landscape)
    if args.json:
        print(json.dumps({"entropy_map": claims, "failure_modes": failures},
                         ensure_ascii=False, indent=2))
        return 0

    if not claims and not failures:
        print("LANDSCAPE.json 里没有 claims / limitations 字段。")
        print("这两个字段是 /lit-survey 的可选扩展：没有它们时本工具无输出，pipeline 不受影响。")
        return 0

    print("=" * 66)
    print("高熵区域（结论分歧 × 条件可比性）")
    print("=" * 66)
    hi = [c for c in claims if c["score"] >= args.min_score]
    if not hi:
        print(f"无 score ≥ {args.min_score} 的 claim（共 {len(claims)} 条）")
    for c in hi:
        print(f"\n[{c['id']}] score={c['score']}  (熵={c['entropy']} × 可比性={c['comparability']})")
        print(f"  {c['statement'][:90]}")
        print(f"  立场分布: {c['stance_counts']}  论文: {c['papers']}")
        if c["comparability_notes"]:
            print(f"  ⚠️ 可比性折扣原因: {'; '.join(c['comparability_notes'])}")
            print("     → 若折扣主要来自设定不一致，这更可能是伪冲突而非领域分歧")
        for w in c["warnings"]:
            print(f"  ⚠️ {w}")
    low = [c for c in claims if c["entropy"] >= 0.6 and c["comparability"] < 0.5]
    if low:
        print("\n" + "=" * 66)
        print("可比性缺口（高熵但条件不可比）")
        print("=" * 66)
        print("这些 claim 在文献中结论分歧明显，但各观测的 dataset / scale / metric 不可比，")
        print("因此**不能当作已确立的领域矛盾直接攻击**。")
        print("但它们本身构成另一类目标：**没人在可比条件下检验过这条 claim**——")
        print("设计 matched-condition 实验（统一 encoder/compute/数据规模/指标）并给出因果结论，")
        print("本身就是 untested-assumption 类的可发表贡献。攻击方式与高熵区域不同，不要混用。\n")
        for c in low:
            print(f"  [{c['id']}] 熵={c['entropy']:.2f} 可比性={c['comparability']:.2f}")
            print(f"    {c['statement'][:88]}")
            print(f"    立场: {c['stance_counts']}  论文: {c['papers']}")
            print(f"    不可比的原因: {'; '.join(c['comparability_notes'])}")
            print("    → 可比化的最小设计: 固定其余条件，仅变动该 claim 所断言的因素\n")

    print("\n" + "=" * 66)
    print("失效模式（多篇论文在同一条件下失效 = 高价值目标）")
    print("=" * 66)
    multi = [f for f in failures if f["n_papers"] >= 2]
    if not multi:
        print(f"无跨论文共享的失效条件（共 {len(failures)} 条单篇记录）")
    for f in multi:
        print(f"\n[{f['n_papers']} 篇] {f['condition']}")
        for e in f["entries"][:4]:
            print(f"    {e['paper']}: {e['raw'][:70]}")
    print("\n注：失效条件按文本归一聚类，粒度粗糙，聚类结果需人工复核。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
