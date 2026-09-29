# stage r5_evidence_merge — merge accepted experiments into one evidence pool

> Fresh engine context. evidence_map + accepted experiments → `evidence_pool.json`. **Only numbers from experiments that passed the acceptance audit are trusted; anything REJECTed or lacking an acceptance record stays out of the pool.**

## Slot `{{SLUG}}`

## Inputs (read-only)
- `campaigns/{{SLUG}}/ledger/evidence_map.json` — the original evidence (paper anchors, existing assets, concessions)
- `campaigns/{{SLUG}}/ledger/concern_ledger.json` — the concern list (its `id` is the binding key)
- Each `campaigns/{{SLUG}}/experiments/<expid>/ACCEPTANCE.json` and the `results.json` beside it
- Each `campaigns/{{SLUG}}/experiments/<expid>/PERSUASION.json` (produced by r4_experiment_persuasion) — the `verdict` (STRENGTH / LOWER_BOUND / CONCEDE) and `framing_hint` for every (reviewer, concern) it serves. **This is where "honest ≠ persuasive" is adjudicated: the acceptance audit only establishes honesty; persuasiveness is decided here.**

## Rules (numbered, applied in order)
1. **Honesty admission**: an experiment's `derived` numbers may enter the pool **only if** `ACCEPTANCE.json.verdict ∈ {ACCEPT, PARTIAL}`. For `PARTIAL`, merge **only the sub-axes that were actually run**. For `REJECT` or a **missing** ACCEPTANCE, **exclude the experiment** and mark every concern that depended on it `evidence_status="unmet"`.
2. **Persuasion grading (from PERSUASION.json, per concern served)**: after honesty admission, `evidence_status` is set by the **persuasion gate**, not defaulted to met:
   - `STRENGTH` → `evidence_status="met"` (hard evidence that can answer the concern directly).
   - `LOWER_BOUND` → `evidence_status="partial"`, and carry the `framing_hint` verbatim into the pool entry (r6 must write an honest lower bound and must not generalise).
   - `CONCEDE` → `evidence_status="unmet"` with `reason="passed the acceptance audit but does not resolve this concern (persuasion gate)"`. **Its numbers are not merged as evidence that clears the concern** — the result stays on disk and auditable, and r6 moves down the warrant ladder and concedes, **never presenting it as a strength**.
   - **An accepted experiment with no PERSUASION.json** → conservatively record `evidence_status="partial"` plus a flag; **never silently treat it as met**.
3. **Move only `derived`**: never copy raw numbers that the acceptance audit did not recompute. Move only the quantities in `results.json.derived` together with their `interpretation`.
4. **Traceable**: every merged entry records the `concern_id` it serves, the `expid`, the `derived` numbers, the path to `results.json`, the `interpretation`, the `persuasion_verdict` and the `framing_hint`.
5. **No fabrication**: if an experiment is missing, rejected, or judged CONCEDE, **say so explicitly** (`evidence_status="unmet"` plus the reason). Never pad with a placeholder number, and never quietly write an unmet or conceded item as met.

## Output (write exactly this file)
`campaigns/{{SLUG}}/ledger/evidence_pool.json` — the unified pool: every entry from evidence_map plus the accepted experimental evidence. Each entry:
```json
{ "concern_id":"C1", "source":"paper|experiment|existing_asset|concession",
  "expid":"02-E-...", "numbers":{"...":0.0}, "results_path":"campaigns/.../results.json",
  "interpretation":"which claim this number supports or weakens", "evidence_status":"met|partial|unmet",
  "persuasion_verdict":"STRENGTH|LOWER_BOUND|CONCEDE|null", "framing_hint":"how r6 should frame this entry" }
```
Receipt (one line): `{merged_from_experiments, accepted, rejected_or_missing, concerns_unmet, conceded_by_persuasion}`.

## DO-NOT
- Do not admit any number from an unaccepted or rejected experiment.
- Do not quietly turn `unmet` or `CONCEDE` into `met`; do not default a missing-PERSUASION experiment to met; do not invent an `interpretation` or a `framing_hint`.
