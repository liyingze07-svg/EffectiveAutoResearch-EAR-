# stage r3b_experiment_ante — the ANTE gate (decide *before* running whether to run at all)

> **Not a free-form prompt.** It reuses the frozen `consensus_gate` and is executed in Python by the orchestrator (`orchestrate.experiment_ante`).
> **Before any GPU time is spent**, it answers the first half of the question: **when is a new experiment needed**, and **would adding one actually persuade**.
> Policy: **only a consensus blocks.** This is deliberately conservative and biased towards "if it is cheap, just run it": NOT_NEEDED or REDESIGN require a clear cross-family agreement.

## What it judges (per experiment request, per concern served)

Using **the same** `bar_met`, it judges two counterfactual stubs (same machinery and same zone routing as S-exp):

1. **Cheap-warrant stub**: "reviewer concern X; the best available warrant *without* a new experiment (a pointer into the paper, an existing asset, literature, or a scoped concession)" — does it clear the bar?
2. **Experiment best-case stub**: "reviewer concern X; we intend to run E, and the best-case real result equals the pre-registered success criterion" — does it clear the bar?

## Decision (aggregated to the experiment level)

| Situation | decision | Loop action |
|---|---|---|
| **Every** concern served already clears on the cheap warrant | **NOT_NEEDED** | No experiment needed — drop it from the queue; r3 uses clarification or existing evidence |
| The cheap warrant is not enough, but **at least one** concern clears on the best case | **GREENLIGHT** | Proceed to run (enters the run → accept → persuade loop) |
| Not even the best case clears for any concern | **REDESIGN** | Do not burn GPU — go straight to the redesign planner (adopt a stronger design if feasible, otherwise concede honestly) |

- **Why the best case uses the pre-registered criterion**: it doubles as the experiment's **pre-registered falsifier**. After the real run, POST compares the real result against it; missing it yields CONCEDE. This is the anti-p-hacking mechanism.
- **Only a consensus blocks**: STRENGTH means both families agree under zone routing (Codex is primary at OA=3). One judge saying no is not enough to declare NOT_NEEDED or REDESIGN. Off-distribution, stay conservative.

## Inputs (read-only)
`campaigns/{{SLUG}}/ledger/experiment_queue.json` (request, serves, expected_or_falsifier), `evidence_map.json` (the source of cheap warrants), `REBUTTAL_CARD.json` (reviewer OA), and `rebuttal_verifier/consensus_gate.py`.

## Output: an in-memory decision plus the ANTE section of `experiments/<expid>/loop.json`: `{decision, per_concern:[{reviewer, concern, cheaper_clears, bestcase_clears}]}`.

## DO-NOT
- Do not add a new bar (only `bar_met`). The best-case stub is a **hypothetical**: it gates the decision to run, and is **never** a citable claim.
- Do not kill an experiment on one judge's false negative, and do not dress up "this is easier" as NOT_NEEDED — that verdict comes from the cross-family consensus, not from the driver.
