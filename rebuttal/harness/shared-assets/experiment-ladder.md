# experiment-ladder.md — Experiment Decision Specification

> Declared as an input by `stages/r3_triage_feasibility.md` and `stages/r4_experiment_redesign.md`.
> This file provides only the **specification** (decision table + contract fields),not the derivation process.

## warrant fallback ladder

| # | move | what the warrant is | when to use it |
|---|---|---|---|
| 1 | **Existing** | an experiment/table already in the paper (overlooked by the reviewer) | the answer is already there → point to its location |
| 2 | **Irrelevant by argument** | logic:E does not test anything within the scope of our claim | E is orthogonal to the claim (**it must be genuinely orthogonal,otherwise=this is evasion**) |
| 3 | **Cheaper proxy E'** | a small experiment E' carries the same evidentiary weight | E is too expensive:a subset/fewer seeds/a smaller model/a single dataset+generalization argument |
| 4 | **pilot+direction** | small-scale pilot results serve as a directional signal | E' is still too expensive:pilot+camera-ready (**the pilot must stand on its own,the promise cannot be everything**) |
| 5 | **Literature** | an existing paper has performed E or an equivalent | someone else has established it → cite it |
| 6 | **honest concession+scoping** | logic:acknowledge that it is a limitation under X,the claim scope is Y | no warrant is obtainable → turn the weakness into scope |
| 7 | **Run E for real** | the raw output of E itself (→ execute §1) | E is feasible and the first 6 moves are all insufficient |

**Most cases of "endless requested additions" fall under 3/5/6,not 7.** Do not default to rushing toward 7.


**Most concern items fall under 3/5/6,not 7.** Do not default to rushing toward 7.

**P0 gate**:when the concern is an explicit reviewer request for an experiment,or questions about 「generalization / insufficient experiments / not validated /
tested only on X」,**before falling back to the move-6 honest concession you must first assess a move-4 pilot**:is there reusable
infrastructure/data/code that can run a small-scale pilot? If it can be run,run it. Concede only when the pilot is clearly infeasible (no infrastructure /
requires human annotation / far exceeds the time budget),and record `pilot_rejected_reason`.

**Time budget**:the bar for move-7 varies with the time remaining in the rebuttal window. If time is tight or E is time-consuming → stop at 3/5/6;
if the window is ample and E is quick to run → favor adding it. Base the decision on `experiment_request.budget` vs the remaining window.

## Experiment Request Contract

### Input:`experiment_request`(written by the rebuttal agent)
```json
{
  "concern_id": "R2-W3",
  "goal": "which reviewer concern to address (one sentence)",
  "hypothesis": "what to verify/demonstrate (falsifiable)",
  "what_to_measure": "metric + on which data/model",
  "baseline": "control (a real baseline,not a straw man)",
  "expected_or_falsifier": "expected result + numerical falsifier (what result counts as failure)",
  "resources": "required dataset / model / code entry point",
  "budget": "compute/time limit"
}
```
