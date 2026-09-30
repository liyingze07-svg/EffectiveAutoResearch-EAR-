# Screening Results (Excerpt)

**Direction**: LLM-as-a-Judge bias, calibration, and social choice theory | **Venue**: EMNLP 2026
**Screened**: All 6 surviving ideas (second round)

> Excerpt note: Retains the ranking and "Key Adjustments"; detailed Module A/B/C reports and idea mechanisms are omitted.

## Final Ranking

| Rank | Idea | Novelty | Venue | Strategic | Feasibility | Composite | Recommendation |
|------|------|---------|-------|-----------|-------------|-----------|----------------|
| 1 | IDEA-04 Causal Disagreement Decomposition | 8.0 | 6.67 | 7.6 | 7.0 | **7.25** | **PROCEED** |
| 2 | IDEA-05 IIA Attacks | 8.0 | 5.33 | 7.4 | 8.0 | **6.95** | CAUTION |
| 3 | IDEA-02 Stochastic Social Choice | 9.0 | 5.33 | 7.0 | 6.0 | **6.72** | CAUTION |
| 4 | IDEA-08 Minority-Preserving Aggregation | 8.0 | 4.67 | 7.6 | 6.0 | **6.35** | CAUTION |
| 5 | IDEA-01 Correlated Juries | 5.0 | 4.33 | 6.2 | 7.0 | **5.41** | CAUTION (substantial repositioning needed) |
| 6 | IDEA-06 Selection-Aware Conformal Panels | 4.0 | 3.67 | 5.2 | 5.0 | **4.32** | **ABANDON** |

Composite = `0.25×Novelty + 0.35×Venue + 0.20×Strategic + 0.20×Feasibility`
≥7.0 → PROCEED | 5.0–6.9 → CAUTION | <5.0 → ABANDON

## Key Adjustments (Revealed by Second-Round Screening)

**The deeper second-round novelty search found three close baselines missed by the initial `lit-survey`**:

| Newly Found Baseline | Affected Idea | Novelty Adjustment |
|---|---|---|
| Work **jointly treating** split conformal and axiom (transitivity) violations | IDEA-06 | **8 → 4** |
| Work on single-judge selective conformal prediction | IDEA-06 | (Same adjustment) |
| Empirical evidence of cross-model error correlation r=0.77 and effective ensemble size only 1.3 | IDEA-01 | **8 → 5** |

Consequences:

- **IDEA-06 changed from CAUTION to ABANDON** (composite fell from above 6 to 4.32)
- **IDEA-01's core empirical premise had already been established**; survival requires repositioning

## What This Record Shows

1. **The initial novelty=8 was wrong**, by enough to change the recommendation. The first search reported no failure; it simply missed the work.
2. A novelty score alone is therefore uninformative. What can be checked is `closest_work.delta`—the **specific** difference from the closest work—and **what this search covered**.
3. This is why the project requires an explicit difference from the closest work, and why the node schema requires `closest_work.ref` and `closest_work.delta` together (missing `delta` is rejected by `tools/idea_nodes.py validate`).
