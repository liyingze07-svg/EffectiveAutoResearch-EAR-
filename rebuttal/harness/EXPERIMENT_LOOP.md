# EXPERIMENT_LOOP.md — The experiment goal loop (first-class)

> Symmetric to `LOOP.md` (the reviewer MoE loop). That loop iterates the **rebuttal text** until it clears the r7 raise gate;
> **this loop iterates a single experiment until it clears the S-exp persuasion gate (STRENGTH), or concedes honestly.**
> The stopping criterion is S-exp. Writing and planning are DRIVE, judging is ACQUIT, they are physically separated, and both reuse the frozen `bar_met`.

## Goal (one sentence)

For each experiment to be added: make its **real result** clear the **zone bar** of the (reviewer, concern) it serves, under cross-family consensus (that is, `STRENGTH`).
If it clears, the result enters the evidence pool. If it does not, state **why** and **how to redesign**, then run a stronger real experiment. At `max_experiment_iter` (default 3), or when no feasible redesign exists, **concede honestly** and emit the **best real result obtained** — **never relabel it as STRENGTH**.

## The loop (`orchestrate.experiment_loop`)

```
Input: one experiment_request (with serves[] and expected_or_falsifier)
──────────────────────────────────────────────────────────────
ANTE gate (r3b, before spending anything; only a consensus blocks):
   NOT_NEEDED → a cheap warrant already suffices → exit (status=NOT_NEEDED)
   REDESIGN   → even the best case would not move the reviewer → redesign first;
                if infeasible, concede honestly
   GREENLIGHT → enter the loop below
──────────────────────────────────────────────────────────────
for it in 1..max_experiment_iter:
   r4_run(remote host, danger-full-access, timeout) → results.json
   r4_accept(a different engine runs the code audit) → ACCEPTANCE.json
      REJECT = an honesty or execution failure, not a persuasion failure
               → close out with an honest concession (does not count as a persuasion iteration)
   S-exp persuasion gate (zone-routed; Codex is primary at OA=3) → PERSUASION.json
      STRENGTH → halt, WON (enters the evidence pool as hard evidence)   ← the only halting condition
      not STRENGTH →
         r4_experiment_redesign (planner, DRIVE engine) produces:
            why_cannot_persuade (which part of the concern was not moved)
            + deficiency (wrong axis / scale / confound / baseline / metric / effect too small)
            + a stronger new_experiment_request + feasible?
         feasible → adopt the new request (new expid) → rerun next iteration
         infeasible → concede honestly (warrant ladder move 6) with the best real result so far
max_iter reached without STRENGTH → concede honestly with the best-so-far
```

## Halting and exits

- **WON** ⟺ some iteration's S-exp reports `overall == STRENGTH` (cross-family consensus cleared that zone's bar).
- **HONEST_CONCEDE** ⟺ no feasible redesign, or acceptance REJECT, or `max_iter` reached. Carries `final` (the best iteration's expid), `why`, and `chain` (a trace of every iteration).
- **NOT_NEEDED** ⟺ the ANTE gate judged that a cheap warrant already suffices.
- Trace: `experiments/<base>/loop.json` (the ANTE decision, each iteration's acceptance and persuasion results, and the redesign chain) and `ledger/experiment_loop_results.json` (a summary over all experiments).

## Inviolable (breaking any of these voids the round)

1. **Only STRENGTH halts, and nothing is ever faked to reach it.** Reaching STRENGTH is only allowed by **designing a stronger real experiment**; a weak or double-edged result must never be relabelled as strong. If that is not possible, concede honestly and carry the real lower-bound result with its true label.
2. Every iteration runs on real data and passes the acceptance audit. Negative results are reported as they are. `feasible=false` is a legitimate outcome.
3. The judge (ACQUIT: S-exp and acceptance) is never the writer or planner (DRIVE: run and redesign). The judge runs `JUDGE_MODEL`; the planner runs the writer engine.
4. The stopping criterion is cross-family consensus on the frozen `bar_met`, never a single judge.
5. **Bounded persistence**: `max_experiment_iter` plus a feasibility check on every redesign. If it is infeasible, concede immediately rather than burning compute.

## Relationship to the reviewer loop

The experiment loop produces **evidence** (in the evidence pool: STRENGTH marks a concern `met`, a concession marks it `unmet` and attaches a `framing_hint`). The reviewer loop (`LOOP.md`) then uses that evidence to iterate the rebuttal until it clears r7. The two loops are decoupled: evidence converges to "persuasive" first, then text converges to "clears the gate".
