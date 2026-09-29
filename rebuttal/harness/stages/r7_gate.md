# stage r7_gate — the raise gate (judge invocation)

> This is not a free-form prompt. It uses the frozen `consensus_gate`. The orchestrator calls it; nothing here is improvised.

## Input: `{review, reviewer_profile (v2 style, carrying OA), initial_overall, rebuttal}`

## Mechanism (see `rebuttal_verifier/consensus_gate.py`)
1. **DeepSeek** side (in-process Python): `deepseek_judge(case, template='auto')` — OA=3 routes to the diagnoser, every other score to v2.
2. **Codex** side (the authoritative judge, run with high reasoning at OA=3): `codex_prompt(case,'auto')` is dispatched to the Codex engine, then parsed with `parse_codex`.
3. `consensus(ds, codex, case)` routes by zone: OA=3 uses authoritative mode (Codex is primary), every other zone uses strict mode (both families must clear).
4. `bar_met` is zone-dependent (see `GOAL.md`).
5. Pre-check: `ammo_hits(rebuttal) == []` (the ammunition gate). The persona is **never** given the ground-truth label.

## Output: `campaigns/{{SLUG}}/ledger/round{{N}}-gate.json` — the DeepSeek and Codex judgments plus the consensus and the pick, for every reviewer and every strategy.

## Rules: the worker never sees this stage's internal prompt; the judge stays frozen; halting always requires cross-family consensus.
