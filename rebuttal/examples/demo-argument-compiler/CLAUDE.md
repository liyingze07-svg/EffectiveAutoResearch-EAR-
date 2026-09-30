# Campaign: demo-argument-compiler

You are Claude Code launched in this folder. You must write a rebuttal for the paper "Learning to Rebut: A First-Principles Argument Compiler" (submitted to ICLR 2026) that is **predicted to raise scores under the frozen raise gate**. **First read `GOAL.md` (task specification), `REBUTTAL_CARD.json`, and `SPEC.md` (frozen acceptance criteria).** The inputs are in this folder under `inputs/` (paper + reviews).

## Reviewers to move
| id | rating | conf | sound | present | contrib | review |
|---|---|---|---|---|---|---|
| R1 | 5 | 4 | 2 | 3 | 2 | inputs/reviews/R1.md |
| R2 | 3 | 4 | 2 | 2 | 2 | inputs/reviews/R2.md |
| R3 | 6 | 3 | 3 | 3 | 3 | inputs/reviews/R3.md |
Goal: Achieve a DeepSeek+Codex cross-family consensus raise(min_delta=1) for P0 reviewer [R1, R2]

## Core beliefs (two; do not forget)
- **Writing is argument compilation, not next-token generation**. Each paragraph has a strategic objective (move the reviewer's belief from X to Y); a paragraph = the compiled artifact of a claim chain (first construct the argument DAG → check logic/redundancy/first principles → render → validate by decompiling).
- **The raise gate is the only zone bar**. It is not "written beautifully"; it is "DeepSeek+Codex both predict that this reviewer will raise their score." You DRIVE; the independent verifier ACQUIT.

## Where things are
- Frozen raise gate: `$AUTOREBUTTAL_ROOT/harness/shared-assets/verifier/` (DeepSeek V4 Pro θ₀ + Codex judge; **never modify/soften/cherry-pick it, and never inspect its internal fitting**).
- Ammunition checklist: `$AUTOREBUTTAL_ROOT/harness/shared-assets/ammunition-checklist.md` (the final draft's grep must have 0 hits).
- rebuttal taxonomy + tips: `$AUTOREBUTTAL_ROOT/harness/shared-assets/rebuttal-tips.md` (concern classification + handling for each type + safeguards against Poor-Response-Pattern).
- Inputs: this folder's `inputs/` (full paper + reviews + existing experiment log + author notes).
- Outputs: `ledger/` (evidence_map / concern_ledger / round*-gate.json / ACQUITTAL.json), `drafts/` (the rebuttal for every strategy in every round), `loop_state.md` + `iteration_log.md`.

## Reusable external infra
- DeepSeek side of the raise gate: `$AUTOREBUTTAL_ROOT/rebuttal_verifier/verify_rebuttal.py` (`verify_one`/`verify_batch`).
- Second judge, Codex: `mcp__codex__codex` (from the OpenAI family and independent of DeepSeek).
- Additional experiments (if allowed): reuse ExpAuto's codegen/runner/recompute.

## Inviolable rules
- **Never fabricate experimental numbers, and never fabricate citations**; every claim must be traceable to real evidence; if that is impossible, write `[TBD]`.
- **You DRIVE; the independent verifier ACQUIT**: do not judge your own work after the run—open a separate VERIFY window, read `VERIFY.md`, and issue the verdict. Never inspect the raise gate's internal fitting.
- Writing must strictly follow argument compilation; every sentence must grow from the paragraph's strategic objective, with no free improvisation.
- The final draft's ammunition grep==0; do not open a new attack surface; do not exceed the word limit.
- Use a DeepSeek+Codex cross-family consensus raise as the stopping criterion; if it is not achieved within 4 rounds → take the honest concession exit; do not fit noise.
