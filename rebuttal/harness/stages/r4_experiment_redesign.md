# stage r4_experiment_redesign — Insufficient persuasion → why + how to redesign (DRIVE-side planner)

> New engine context (**writer/default engine, not JUDGE_MODEL** — this is DRIVE-side planning, not an ACQUIT verdict).
> When the S-exp persuasion gate judges **non-STRENGTH** (the experiment is insufficient to persuade this reviewer), this stage answers two questions:
> **① Why this experiment (even with results) cannot move this concern; ② how to redesign a stronger experiment that can genuinely persuade.**
> The output is consumed by `experiment_loop` → if feasible, replace it with a new request and rerun; if infeasible, make an honest concession.

## Slots `{{SLUG}}` `{{EXPID}}` `{{BASIS}}` (`ante_bestcase` = not actually run yet; the judgment is based on the best-case / `post_result` = the actual result is insufficient) `{{ITER}}`

## Inputs (read-only)
- `campaigns/{{SLUG}}/experiments/{{EXPID}}/PERSUASION.json` (if `post_result`) → the `verdict` for each target that did not pass + **`why_not_persuasive`** (which part of the real concern the authoritative judge says remains unmoved) + `judge_advice`.
- `campaigns/{{SLUG}}/experiments/{{EXPID}}/results.json` (if `post_result`) → the actual `derived` (identify exactly where the actual result is weak: effect too small/double-edged/CI crosses 0/sub-axis not_run).
- The current `experiment_request` for `{{EXPID}}` in `campaigns/{{SLUG}}/ledger/experiment_queue.json` (the object to modify).
- `campaigns/{{SLUG}}/ledger/concern_ledger.json` → the concern's **`real_concern` (the real concern)**: the redesign must target this, not follow the momentum of the original experiment.
- `campaigns/{{SLUG}}/ledger/evidence_map.json` → which infrastructure/data/assets are reusable (used to determine `feasible`).
- `harness/shared-assets/experiment-ladder.md` (warrant ladder + experiment-request contract).

## Rules (numbered, follow strictly in order)
1. **First attribute the cause (why it cannot persuade)**: map `why_not_persuasive` + the actual `derived` to one **deficiency class**:
   `wrong_axis` (the measured axis is not the one the reviewer questioned)/ `underpowered` (scale/seed/n is insufficient, CI crosses 0)/ `confounded` (there is a confound/oracle leakage)/ `weak_baseline` (the control is a straw man)/ `off_metric` (the metric does not correspond to the real concern)/ `effect_too_small` (the direction is right, but the magnitude is insufficient to overturn the judgment)/ `other`. State clearly **which subclause of the real concern remains unmoved**.
2. **Then prescribe the remedy (how to redesign)**: for the deficiency class, provide **one stronger `experiment_request`** (all fields from the experiment-request contract in experiment-ladder): specifically change the axis/scale/baseline/metric/isolation design **so that it can genuinely answer the real concern**. Examples: `underpowered` → raise n until the CI excludes 0; `confounded` → add a control arm to isolate the mechanism; `wrong_axis` → switch to the setting explicitly named by the reviewer (e.g., short answers → long free-form CoT).
3. **Feasibility gate (hard, prevents stubbornly burning the budget to nothing)**: return a new request only if it has `feasible=true`. Feasible = **reusable infrastructure/data/code + within the budget/time window** (the five-step experiment-ladder table, Step1). If this cannot be done (data gated / requires human annotation / far exceeds the budget) → `feasible=false` + fill in `pilot_rejected_reason`, **triggering honest concession** (do not fabricate a stronger design to deceive yourself).
4. **Never fabricate**: the redesign is **a different, stronger real experiment**, not relabeling a weak result as strong; the new request's `expected_or_falsifier` must be falsifiable, with a real baseline; `serves` must retain the original (reviewer, concern).
5. **Do not go in circles**: the new design must be **materially stronger** with respect to the deficiency class (not merely changing the wording/changing the seed count while staying on the same weak axis). As iter increases, either genuinely escalate or make an honest concession.

## Output (write this exact file)
`campaigns/{{SLUG}}/experiments/{{EXPID}}/redesign_iter{{ITER}}.json`:
```json
{ "expid":"{{EXPID}}", "basis":"{{BASIS}}", "iter":{{ITER}},
  "why_cannot_persuade":"which subclause of the real concern remains unmoved + where the result is weak (specific)",
  "deficiency":"wrong_axis|underpowered|confounded|weak_baseline|off_metric|effect_too_small|other",
  "feasible": true,
  "pilot_rejected_reason":"(required when feasible=false: why even a stronger pilot is infeasible)",
  "new_experiment_request": {
     "expid":"(leave blank, driver will assign a new id)", "serves":["<original reviewer-concern>"], "priority":"P0",
     "goal":"...", "hypothesis":"falsifiable", "what_to_measure":"metric+data+model",
     "baseline":"real baseline", "expected_or_falsifier":"expected outcome+numerical falsifier",
     "resources":"reusable data/model/code entry point", "budget":"compute/time limit" }
}
```
receipt (return one line):`{expid, deficiency, feasible, new_expid_hint}`.

## DO-NOT (hard)
- Do not read judge internals (`rebuttal_verifier/`, `r7_gate.md`, or the judging implementation in `r4_experiment_persuasion.md`) — use only the `why` given to you by PERSUASION.json.
- When `feasible=false`, **do not fabricate** a request that only pretends to be feasible in order to deceive the loop; honest concession is a legitimate outcome.
- Do not change the (reviewer, concern) in `serves`; do not treat the same weak axis with a different seed count as a "stronger design."
