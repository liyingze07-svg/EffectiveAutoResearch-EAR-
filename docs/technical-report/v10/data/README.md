# Released evidence aggregates

These tables reproduce the report's numerical comparisons without access to
individual research targets, manuscripts or private execution records. They are
freshly constructed release aggregates, rather than copies of the raw archive.

This edition reports G0 initialization and three evolution generations, G1-G3.
The window is a retrospective presentation choice; the underlying archive has
subsequent generations, retained separately. Stage results use every episode
inside the stated window. G3 selected-strategy success is 3/4 (75%), while its
baseline is 2/4 (50%); whole-generation success is 9/20 (45%).

| File | Unit and coverage |
|---|---|
| `round_aggregates.csv` | Four rounds for a fixed cohort of 28 completed manuscripts from G0-G3; current and selected-best counts and recorded score sums are separate. |
| `generation_population.csv` | All 64 retained episode endpoints in the G0-G3 reporting window, including failed and unwritten episodes. |
| `generation_comparison.csv` | Baseline and generation-selection batches, four episodes per role per generation. The two roles share a batch in G0 and G1. |
| `selected_cost.csv` | Raw aggregate components of the G3 selection comparison, four episodes per strategy; ratios are derived by the script. |
| `rebuttal_evaluator.csv` | Three source-reported aggregate metrics. The 57-case rows describe two metric framings of the same source test. |
| `idea_process.json` | Anonymous evidence-to-decision rescreen example. |
| `rebuttal_process.json` | Anonymous two-round strategy comparison under a historical proxy rule. |
| `protocol.json` | Outcome definitions, historical and portable version boundaries, cost coverage, and retained-vote sensitivity. |
| `claims.csv` | Four shared claims, evidence IDs and supported scope. |
| `derived_metrics.json` | Deterministic output of `scripts/recompute.py`. |

Run from the release root:

```sh
python3 scripts/recompute.py --output data/derived_metrics.json
python3 scripts/draw_figures.py
```

The recomputation needs only Python's standard library. Drawing needs
`matplotlib` and an installed CJK font such as Noto Sans CJK SC. Default drawing
outputs are `figures/en/` and `figures/cn/`, in PDF, PNG and editable SVG.

Counts, means, rates, cost totals and cost-per-pass comparisons are calculated
from the released counts and score sums. F1 values are preserved reported
aggregate inputs: individual gold labels and predictions are not included, so
this release does not independently reestimate those F1 values. Per-round score
sums use the source's recorded two-decimal scores.

Historical math passes are model-assessor labels under the protocol in
`protocol.json`. The fixed 28-manuscript cohort is conditional on successful
writing. Active human time has not been measured; invocation counts are partial
machine-work proxies. These definitions also apply to the bilingual figures.
