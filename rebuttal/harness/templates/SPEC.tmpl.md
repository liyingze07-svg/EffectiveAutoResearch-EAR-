# SPEC — {{SLUG}} (Frozen Acceptance Contract · Third Party · Must Not Be Modified After Instantiation)

This file is **hard-coded by the meta layer** before the first sentence of the rebuttal is written and is the sole basis on which the independent verifier judges ACQUIT/REJECT. **The writer must not edit this file and must not inspect the internals of the raise gate to fit to it.** Any ambiguity → the verifier must interpret it toward "rejection."

- paper: {{PAPER_TITLE}}　venue: {{VENUE}}
- Paper claims (evidence basis): {{PAPER_CLAIMS}}
- Reviewers (criterion anchors): {{REVIEWERS_TABLE}}
- Target: {{TARGET}}
- Word limit: {{WORD_LIMIT}}
- Raise gate configuration: `{{HARNESS_DIR}}/shared-assets/verifier/` (DeepSeek V4 Pro θ₀ + Codex judge, **frozen verbatim and must not be changed**).

## A. Clear the Bar (Cross-Family Consensus Gate · the bar · **Score-Aware**)
The optimal rebuttal strategy must, for **every P0 reviewer** specified in {{TARGET}}, use the **same frozen prompt** to pass the judges from **both the DeepSeek V4 Pro and Codex families** (see `../rebuttal_verifier/consensus_gate.py`); **A passes only if both clear the bar** (conjunction, strict—the goal mode performs hard optimization to prevent a single judge from being gamed).

**The zone bar is routed by the reviewer's starting score** (empirical finding in README §4/§5: the raise outcome for borderline cases cannot be predicted from text; chasing it = chasing noise = Goodhart):
- **borderline (overall assessment = 3)**: bar = **STRENGTH**—the diagnostic returns `veto='none'` and `raise_potential='high'`. **Do not hard-require a prediction of `raise`** (that outcome is unpredictable). Use the diagnostic's `advice` field as the judge feedback for the loop.
- **Predictable zone (a low starting score or another non-borderline case)**: bar = `reaction='raise'` (the raise signal genuinely exists here).

**Route the authoritative judge by zone (README §7)**: for non-borderline cases, DeepSeek is the primary judge (0.805) + Codex consensus (strict); **for borderline OA=3, Codex/GPT-5.5 is the primary judge** (quality separation +0.28, optimal; **invoke Codex with high reasoning**), and DeepSeek is downgraded to a soft check (`mode='authoritative'`, with no hard requirement for consensus from the weaker DeepSeek). `consensus_gate.primary_judge` decides automatically.

The persona includes `initial_rating` (ICLR /10) or `initial_overall` (EMNLP /5) + subscores + confidence. **Note**: for EMNLP, do not put the raw score into the persona (it causes over-anchor, README §4.3)—route with `--template auto`, which already handles this.

## B. Coverage (No P0/P1 May Be Omitted)
Every P0/P1 concern must be explicitly addressed in the final draft (by responding, pointing to a location, adding evidence, or making an honest concession). Omitting P2 is not fatal.

## C. Evidence Honesty (Failure of Any Item Means Failure)
1. **Numbers aggregated from experimental data** and included in the main text (means/slopes/ratios…) must be recomputed from raw data with `recompute_check` to an error of <1%; quantities without a raw-data formula (such as theoretical constants) do not require recomputation.
2. **Every citation must actually exist and be relevant**—it must pass the existence check and be entered into the allowlist; fabricated citations are forbidden.
3. **Every claim must be traceable**: a statement that "the paper has proved X" must be locatable to a section/figure/table; a statement that "we ran experiment Y" must be locatable to raw data. An unsupported claim → it must be `[TBD]` + action item and must not be presented as completed.
4. Evidence may be selected for presentation, but **fabrication, embellishment, and presenting unfinished work as completed are forbidden**.

## D. No Ammunition + No New Attack Surface
1. The final-draft ammunition grep (`{{HARNESS_DIR}}/shared-assets/ammunition-checklist.md`) = 0: no self-disclosed weaknesses, no "we do not claim," and no over-concession framing phrases.
2. Do not admit a new weakness that no other reviewer raised in order to respond to one reviewer (do not open a new attack surface).
3. The word count must not exceed {{WORD_LIMIT}}; the main text must contain no `[TBD]`.

## E. Independence
Binding ACQUIT must be issued by an **independent VERIFY window** (see `VERIFY.md`) after rerunning the raise gate + rechecking C/D; it is **not judged by the writer**. Any verdict issued by the writer is invalid. The verifier must output PASS/FAIL for every item + the gate's reaction/reasoning + evidence paths.

**ACQUIT ⇔ A ∧ B ∧ C ∧ D ∧ E all pass.** the bar = clearing the cross-family consensus gate for a raise. The faithfulness gate blocks only genuine fabrication such as "a calculated number does not match raw data," "a citation does not exist," or "an unsupported claim is presented as completed"; **minor differences in protocol wording are not fatal—just prompt a correction; do not REJECT the entire response**.

**Honest concession exit**: if {{MAX_ITER}} rounds still cannot achieve a consensus raise, but the final draft passes B/C/D/E in full (full coverage, honest evidence, zero ammunition, independence) and is the "most honest concession-style rebuttal" → `{"verdict":"ACQUIT","track":"honest-concede","raise_achieved":false}`. Not every paper can earn a score increase; an honest concession is better than fitting noise.

This file is frozen after instantiation.
