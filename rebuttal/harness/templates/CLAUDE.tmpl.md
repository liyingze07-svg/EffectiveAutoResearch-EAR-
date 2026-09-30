# Campaign: {{SLUG}}

You are Claude Code launched in this folder. You must write a rebuttal for the paper 「{{PAPER_TITLE}}」 (submitted to {{VENUE}}) that is **predicted to raise the score under the frozen raise gate**. **First read `GOAL.md` (task brief), `REBUTTAL_CARD.json`, and `SPEC.md` (frozen acceptance criteria).** The inputs are in this folder's `inputs/` (paper + reviews).

## Reviewer Whose Position Must Be Shifted
{{REVIEWERS_TABLE}}
Target: {{TARGET}}

## Core Beliefs (Two; Do Not Forget)
- **Writing is argument compilation, not next-token generation**. Every paragraph has a strategic objective (shift the reviewer belief from X to Y); a paragraph = the compiled artifact of a claim chain (first build the argument DAG → check logic/redundancy/first principles → render → decompile and verify)..
- **The raise gate is the only zone bar**. The criterion is not "beautiful writing"; it is "DeepSeek+Codex both predict that this reviewer will raise the score." You DRIVE; independent verifiers ACQUIT.

## Where Things Are
- Frozen raise gate: `{{HARNESS_DIR}}/shared-assets/verifier/` (DeepSeek V4 Pro θ₀ + Codex judge, **never alter/soften/cherry-pick it, and never inspect its internal fitting**).
- Ammunition checklist: `{{HARNESS_DIR}}/shared-assets/ammunition-checklist.md` (the final-draft grep must return 0 matches).
- rebuttal taxonomy + tips: `{{HARNESS_DIR}}/shared-assets/rebuttal-tips.md` (concern taxonomy + responses for each type + Poor-Response-Pattern screening).
- Inputs: this folder's `inputs/` (full paper + reviews + existing experiment log + author notes).
- Outputs: `ledger/` (evidence_map / concern_ledger / round*-gate.json / ACQUITTAL.json), `drafts/` (the rebuttal for every strategy in every round), `loop_state.md` + `iteration_log.md`.

## Reused External infra
- DeepSeek side of the raise gate: `$AUTOREBUTTAL_ROOT/rebuttal_verifier/verify_rebuttal.py` (`verify_one`/`verify_batch`).
- Second judge, Codex: `mcp__codex__codex` (OpenAI family, independent of DeepSeek).
- Supplemental experiments (if permitted): reuse ExpAuto's codegen/runner/recompute.

## Iron Rules
- **Never fabricate experimental numbers; never fabricate citations**; every claim must be traceable to real evidence; if that is impossible, write `[TBD]`.
- **You DRIVE; independent verifiers ACQUIT**: after running, never judge the result yourself—open a separate VERIFY window, read `VERIFY.md`, and issue the verdict there. Never inspect the raise gate's internal fitting.
- Writing must strictly follow argument compilation; every sentence must grow from the paragraph's strategic objective, with no free-form improvisation.
- The final-draft ammunition grep must satisfy grep==0; open no new attack surface; do not exceed the word limit.
- Use a raise verdict from the DeepSeek+Codex cross-family consensus gate as the stopping criterion; if it is not achieved within {{MAX_ITER}} rounds → take the honest concession exit; do not fit noise.
