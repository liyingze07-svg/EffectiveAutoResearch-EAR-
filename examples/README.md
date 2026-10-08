# Pick a demo

Start by opening a result, then run the corresponding check. All commands below run from the EAR repository root and require only Python 3.10+. None invokes a live model.

| Demo | What you can inspect | Provenance |
| --- | --- | --- |
| [EAR project homepage and demo](../docs/demo-studio.md) | Input/output figure, workflow mechanisms, report charts, research workspace, proof, validation, review and revised manuscript | Authored reference workflow; separate historical records and executed synthetic fixtures |
| [Technical report](../docs/technical-report/v10/) | Bilingual PDFs, revision and strategy figures, reproducible metric summaries | Public aggregates from historical runs; individual manuscripts and raw reviews are not released |
| [An idea that changed after retrieval](../autovibeidea/examples/judge-run/README.md) | Novelty 8 → 4; close prior work changes a recommendation to ABANDON | Sanitized excerpts from a real historical run; scores are model judgments |
| [Candidate selection and pruning](../autovibeidea/examples/search-demo/README.md) | How feasibility signals and saturation affect candidate selection | Real root candidates with explicitly constructed demonstration children |
| [Math revision and continuation](../autonomousmath/README.md#inspect-the-complete-loop-without-model-calls) | Rejection, revision, another review and saved state | Synthetic fixtures executed through the portable workflow |
| [Rebuttal input and dry-run](../rebuttal/examples/offline-demo/) | Paper, reviewer comments, task card and planned stages | Synthetic example; no generated scientific or rebuttal-quality claim |

## Explore the project, then try a case

```bash
python3 -m ear demo studio
```

The local page introduces EAR with an input/output figure, project explanation,
interactive mechanisms and released results. Its Demo lets visitors choose a research goal, inspect the proof, compute numerical evidence, revise a manuscript and download the research artifacts. The authored reference workflow is separate from historical records and executed fixtures.
Use `--export workspaces/ear-demo.html` to produce a self-contained recorded
snapshot for a meeting. See the [Studio guide](../docs/demo-studio.md) for source
boundaries, downloads, your own inputs and a two-minute walkthrough.

## 1. Recompute the report

```bash
python3 -m ear demo report
python3 -m ear demo report --json
```

The command recalculates counts, means and per-pass ratios from the bundled aggregates and checks the result against `derived_metrics.json`. It does not rerun the private historical research campaign. Reported evaluator F1 values are aggregate inputs; the release does not contain the individual predictions needed to independently reestimate them.

Read [the report release](../docs/technical-report/v10/README.md) for what is reproducible and [the protocol](../docs/technical-report/v6/data/protocol.json) for population denominators, retrospective selection, review rules and cost coverage.

## 2. Follow the changed idea decision

Open [the annotated trace](../autovibeidea/examples/judge-run/README.md), then inspect the screening excerpt and critique excerpt linked there. The useful outcome is the change in reasoning after finding closer prior work. No benchmark-wide accuracy claim follows from this one example.

Validate its current node representation:

```bash
python3 autovibeidea/tools/idea_nodes.py \
  --path autovibeidea/examples/judge-run/IDEA_NODES.jsonl validate
```

## 3. Run the math loop

```bash
python3 -m ear math run --offline --workspace workspaces/math-demo --episodes 1
python3 -m ear math status --workspace workspaces/math-demo
```

Inspect the workspace's task artifacts and `reviews/`. The first fixture draft is rejected, then revised, then receives a passing fixture review. The result remains `offline_demo` with `accepted=false`; it is an execution demonstration, not a scientific result.

## 4. Check the shared workflow wiring

```bash
python3 -m ear demo check
```

This validates the idea example, generates five rebuttal contract files and executes a synthetic rebuttal dry-run. The command prints the output directory; inspect `SUMMARY.json` and the rebuttal `DRY_RUN.txt`.

To retain the artifacts at a chosen **new** directory:

```bash
python3 -m ear demo check --output workspaces/first-check
```

Existing output directories are refused to preserve their contents. Once you understand the artifacts, continue with [your own inputs](../docs/getting-started.md).
