# SPEC — demo-argument-compiler (frozen acceptance contract · third-party · must not be modified after instantiation)

This file is **fully populated and locked by the meta layer** before the first sentence of the rebuttal is written and is the sole basis on which the independent verifier judges ACQUIT/REJECT. **The writer must never edit this file or inspect the internals of the raise gate to fit to it.** Any ambiguity → the verifier interprets it toward "rejection."

- paper: Learning to Rebut: A First-Principles Argument Compiler　venue: ICLR 2026
- Paper claims (evidence base): - C1: We propose mechanism M, which resolves the conflict between A and B; this is the core contribution
- C2: On benchmark X, we improve by 13.6 points over the strongest baseline
- C3: The theoretical analysis provides a convergence guarantee for M (Thm 1)
- Reviewers (criterion anchors): | id | rating | conf | sound | present | contrib | review |
|---|---|---|---|---|---|---|
| R1 | 5 | 4 | 2 | 3 | 2 | inputs/reviews/R1.md |
| R2 | 3 | 4 | 2 | 2 | 2 | inputs/reviews/R2.md |
| R3 | 6 | 3 | 3 | 3 | 3 | inputs/reviews/R3.md |
- Target: for P0 reviewer [R1, R2], achieve a DeepSeek+Codex consensus raise(min_delta=1)
- Length limit: per-reviewer 5000 chars
- Raise gate configuration: `$AUTOREBUTTAL_ROOT/harness/shared-assets/verifier/` (DeepSeek V4 Pro θ₀ + Codex judge, **frozen verbatim and must never be changed**).

## A. Raise (cross-family consensus gate · the bar)
For the rebuttal produced by the optimal strategy, under the frozen raise gate, the following must hold for the reviewers specified in the target “for P0 reviewer [R1, R2], achieve a DeepSeek+Codex consensus raise(min_delta=1)”—that is, for **every P0 reviewer**:
- **DeepSeek V4 Pro** must predict `reaction=raise` (`quality=high`), **and**
- **Codex** (same review + rebuttal + persona, independent prompt) must also predict `raise`.
A passes only if both judges from the two different families raise (a strict conjunction—because goal mode performs hard optimization, the exit must be strict to prevent a single judge from being gamed). persona must include `initial_rating` + soundness/presentation/contribution subscores + confidence (README confirms that including persona significantly improves scores).

## B. Coverage (not one P0/P1 may be missed)
Every P0/P1 concern must be explicitly addressed in the final draft (through a response, a location pointer, additional evidence, or a graceful concession). Missing a P2 is not fatal.

## C. Evidence honesty (failure of any item means failure)
1. **Numbers derived by aggregating experimental data** that enter the main text (means/slopes/ratios…) must be recomputed from raw using `recompute_check` with <1% error; quantities without a raw formula (such as theoretical constants) do not require recomputation.
2. **Every citation must actually exist and be relevant**—it must pass the existence check and be added to the allowlist; fabricated citations are forbidden.
3. **Every claim must be traceable**: a statement that "the paper has proved X" must be locatable to a section/figure/table; a statement that "we ran experiment Y" must be locatable to raw. An unsupported claim → must be `[TBD]` + action item and must never be presented as completed.
4. Evidence may be selected for presentation, but **fabrication/embellishment/claiming unperformed work as completed is forbidden**.

## D. Zero ammunition + no new attack surface
1. Final-draft ammunition grep (`$AUTOREBUTTAL_ROOT/harness/shared-assets/ammunition-checklist.md`) = 0: no self-exposure, no "we do not claim," and no over-concession framing language.
2. Do not admit a new weakness that another reviewer did not raise in order to respond to one reviewer (do not open a new attack surface).
3. Do not exceed per-reviewer 5000 chars; the main text must contain no `[TBD]`.

## E. Independence
The binding ACQUIT is determined by an **independent VERIFY window** (see `VERIFY.md`) that reruns the raise gate + rechecks C/D, **not by the writer's own judgment**; any verdict issued by the writer is invalid. The verifier outputs PASS/FAIL item by item + the gate's returned reaction/reasoning + evidence paths.

**ACQUIT ⇔ A ∧ B ∧ C ∧ D ∧ E all pass.** the bar = the cross-family consensus gate for a raise. The faithfulness gate blocks only concrete fabrication such as "a formula-derived number does not match raw," "a citation does not exist," or "an unsupported claim is presented as completed"; **minor differences in protocol wording must not be treated as fatal—just flag them for correction; do not REJECT the entire submission**.

**Honest concession exit**: if a consensus raise still cannot be achieved after 4 rounds, but the final draft passes B/C/D/E in full (full coverage, evidence honesty, zero ammunition, independence), and it is the "most honest concession-style rebuttal" → `{"verdict":"ACQUIT","track":"honest-concede","raise_achieved":false}`. Not every paper can earn a raise; honestly standing down is preferable to fitting noise.

This file is frozen after instantiation.
