# stage r3_triage_feasibility — response modes and the experiment feasibility ladder

> Fresh engine context. concern_ledger → response modes plus a deduplicated experiment queue. The core idea: **an experiment is a warrant, not a goal**; most concerns need no new experiment.

## Slot `{{SLUG}}`
## Inputs (read-only): `concern_ledger.json`, `evidence_map.json`, `harness/shared-assets/experiment-ladder.md` (the feasibility ladder).

## Rules (per concern)
1. Decide the response mode: A clarify / B existing evidence / C new experiment / D literature / E concede / F rebut.
2. **Assign a `priority` first — it decides how hard you try to add an experiment.**
   - **P0 = the reviewer explicitly asks for an experiment, or challenges generalisation, missing experiments, a missing baseline, lack of verification, or "only tested on X"** (especially for the OA≤3 reviewers you are trying to move). For these the real concern is "show me evidence", and no amount of writing will paper over it.
   - P1/P2 = nice-to-have, or a secondary clarification.
3. **Mode C follows the warrant fallback ladder** (see the ladder table in experiment-ladder: 1 already exists → 2 argumentatively irrelevant → 3 cheaper proxy → 4 pilot → 5 literature → 6 concede → 7 run the full experiment), **graded by priority**:
   - **P0: default to rung 4, `pilot`** — a small real experiment, run it whenever existing infrastructure, data or code can be reused. Only drop to rung 6 (concede) when the pilot is clearly infeasible (no reusable infrastructure, human annotation required, or far beyond the budget or time window), and then you **must** fill in `pilot_rejected_reason`. Never slide straight to a concession because it is easier or because the writing could work around it.
   - P1/P2: add an experiment only when infrastructure is reusable and the cost is small; otherwise use existing evidence or concede.
4. **Honesty gate (hard)**: before any concern lands on "E concede", you must explicitly answer "could a pilot cover this?" — if `pilot_rejected_reason` is empty, the concession is **not** allowed. A concession is the fallback after a pilot has been ruled out, not the default.
5. For concerns that genuinely need an experiment, write an `experiment_request`, **deduplicate by specification** into a paper-level queue, each carrying `serves:[concern/reviewer]` and `priority`.

## Output: `concern_ledger.json` gains `response_mode` and `priority` (plus `pilot_rejected_reason` for concessions); `campaigns/{{SLUG}}/ledger/experiment_queue.json` holds the deduplicated experiment requests with `serves[]` and `priority`. Receipt: `{n_by_mode, n_experiments_queued, n_pilot_P0}`.
