# CRAFT.md — rebuttal Shared Brain (Required Reading for Every Strategy and Every Writing Pass)

> This is the core of "whether the rebuttal is well written." All 3 MoE stances (s1/s2/s3) are **built on this file**; stances determine only differentiated tradeoffs, while the underlying craft must follow this file without exception. Distilled from the paper-rebuttal skill's `strategy_playbook.md` + `stance_playbook.md` (for more comprehensive cases, see the skill's `examples/case_library.md`).

## 0. Five Governing Rules (Apply to Every concern)
1. **Address the real concern, not the literal wording (Jiu-Jitsu)**: Resolve the `real_concern` diagnosed by r2, not the reviewer's original sentence. Answering the literal wording while leaving the real concern untouched will not move the score.
2. **Combine Clarify + Justify**: Do not concede throughout the entire response (it makes the contribution look indefensible), and do not defend throughout the entire response either (it makes the authors look unreceptive). Pair "acknowledge the reasonable part + directly present evidence" in every response.
3. **Provide a face-saving path**: Changing a score carries a psychological cost for the reviewer. Word the response so the reviewer can naturally say "the authors clarified my concern"; frame the misunderstanding as "we did not explain this clearly," even if the reviewer did not read carefully.
4. **Answer first, then substantiate**: The first sentence is the answer → evidence (section/table/numbers) → impact → what will change.
5. **data beats arguments**: If numbers can resolve it, do not use adjectives. No numbers → `[TBD]` + action; fabrication is never allowed.

## 1. Three-Way Stance Routing (Classify First, Then Write)
| Situation | Stance | Discipline |
|---|---|---|
| **① Factual error** (the reviewer claims something the paper does not say or says the opposite) | Correct firmly: "We respectfully clarify/note that ..." + page-level evidence | Do not dilute "the reviewer is wrong" into "we did not explain this clearly" merely to avoid conflict (unless we genuinely did not explain it clearly) |
| **② Valid criticism** (a real issue) | Make a professional honest concession: concede only that point + attach a concrete fix, turning "conceded" into "resolved" | Acknowledging a clarity issue ≠ conceding that soundness has collapsed; acknowledging one limitation ≠ conceding that the contribution is invalid |
| **③ Gray area** (design choice/scope/preference) | Defend first: defend when evidence is available; defense is standard academic practice | respectfully disagree is legitimate; do not retreat at the first pushback, and only if persuasion truly fails, fall back to "state in the paper that this is not the only choice" |

## 2. 🔴 No Groveling, No Self-Sabotage (= Honesty in Substance, Not Performative Honesty; Hard Writing Discipline)
- ✗ **Do not respond to weaknesses the reviewer did not raise**—a rebuttal is a defense, not a confession.
- ✗ **Do not escalate a small issue**—do not turn clarity into soundness, or a typo into a methodological flaw.
- ✗ **Do not use self-incriminating language**—`major weakness / fundamental limitation / our method fails` (a genuine fatal flaw should have caused a BLOCK at the gate; do not write it into the rebuttal).
- ✗ **No performative honesty**—`we honestly concede / will not manufacture / we did not spin it / (conceded) tag / repeated fair criticism`. Honesty means not misrepresenting facts, not writing "I am very honest" (which signals insecurity and hands the reviewer ammunition).
- ✓ **Every concession must contain its safeguard in the same sentence**: "we acknowledge X, **however** [evidence shows that its impact is limited/it has been mitigated/it belongs to future work]"; never leave a bare "we acknowledge X".
- ✓ **One acknowledge is enough**; do not apologize in every paragraph.

## 3. 14 concern Types → Canonical Plays (Defaults; Follow the r2 Diagnosis of the real concern in Practice)
| concern | The real concern | Response skeleton |
|---|---|---|
| Novelty/contribution | Novelty/Substance | First acknowledge that the nearest neighbor X is relevant → list **3 substantive differences** (task/assumption/evaluation, each with a location). Avoid "X irrelevant"/"we are first" |
| Missing Related Work | Novelty/Evidence | If genuinely omitted → add it candidly + state the differences immediately; if not omitted → cite its location. Verify every citation first; fabrication is never allowed |
| Motivation/significance | Substance/Scope | Rebuild the motivation with a **specific scenario/number**; avoid a pile of adjectives |
| Soundness/correctness (often P0) | Soundness | **Address it head-on; no evasion**: spell out the derivation + worked example + lemma/citation. Ambiguity means the reviewer is right by default |
| Method Clarity | Surface Clarity often conceals Soundness | Acknowledge the presentation issue + **provide the revised snippet immediately**; if the underlying issue is soundness, add the direct argument |
| Experiment/evaluation | Evidence (often a particular component remains unproven) | Diagnose what the reviewer actually needs (often a key ablation, not more data) → provide real numbers or explain the design rationale |
| Missing Baseline | Evidence/Novelty | If it can be run, run an apples-to-apples comparison and put it in the main text; win → main text, no win → pivot to robustness/efficiency; if it cannot be completed, use `[TBD]`; if incomparable → explain why, but acknowledge its relevance first |
| Ablation/analysis | Evidence/Substance | Provide **component-level** evidence (change in the metric when that component is removed); if it already exists, cite the exact location and repeat the numbers |
| Reproducibility | Reproducibility | Cite the exact location of the details (hyperparameter table/pseudocode/code link); promise only what can be delivered |
| Limitation/Scope | Scope | Make an honest concession + evidence that "the impact is limited" + extension=future work. Acknowledging a boundary ≠ conceding failure of the core contribution; narrow an over-broad claim immediately |
| Writing/formatting | Clarity | Be humble + provide a concrete edit list. **P2, handle briefly in one short paragraph**; do not spend main-text firepower on it |
| Ethics/compliance | Process | Treat it seriously, cite the checklist location, and if missing, immediately provide the statement text + specific basis |
| Reviewer misreading | Any | Be polite but firm + provide a face-saving path: set stage → cite the location → frame it as a presentation problem. Keep the evidence hard (page-level) and the tone soft. Avoid "clearly stated" (which is confrontational) |
| The Review itself is problematic | — | Publicly provide only restrained clarification; never accuse. If too vague → request specifics; use a confidential AC comment only when a trigger is satisfied. Disagreement/requests for experiments/a weak-novelty judgment **do not** qualify |

## 4. Response action Wording Skeletons (Evidence Slots Must Come from evidence_map; Fabrication Is Forbidden)
Clarify: "We respectfully clarify that ... (Sec X)" · Correct: "We respectfully note [fact] + page-level evidence" · Concede&Fix: "We agree this deserves improvement; we have revised ... to '...'" · Provide Existing: "This is in Table 3, where ... shows ..." (must say where it is + what it shows) · Add Experiment: "We have run ...: [table]. This shows ..." (if it has not been run, use `[TBD]`) · Compare: "We agree X is related. We differ in (1)..(2)..(3).." · Narrow Claim: "We have revised the claim to '...'" · Reframe Scope: "A full treatment of X warrants a separate study; our scope is ..., because ..." · Defend: "We chose ... because ...; empirically Table Y shows ..." (avoid the unsupported phrase "standard practice") · Acknowledge Limitation: "We acknowledge ...; results suggest impact is limited (evidence); future work: ..." · **Defer to Revision: Do not use this when the work can be done now**.

## 5. The real concern → Pattern Quick Reference
Substance→show the existing evidence of substance (scale/depth/ablation) + add the single most persuasive key experiment when necessary. Soundness→spell out the direct argument; never evade. Novelty→distinguish along task/assumption/evaluation; acknowledge relevance first. Evidence→provide the data directly. Clarity→acknowledge the presentation issue + revised snippet + set stage. Scope→acknowledge the importance of the broader direction + justify why this paper's scope is reasonable + extension=future. Reproducibility→cite the exact location of the details.

## 6. External Presentation = Argument Compilation (Primary Method: `strategies/write-direct-rebuttals.md`)
> §0–5 are **internal logic** (determine the real concern to answer, the evidence to use, and the stance to take). **The final reviewer-facing draft must follow the argument compilation paradigm in `write-direct-rebuttals.md`**: rebuttal = compilation of a **minimal, literal, honestly direct response** for every reviewer slot; **directness overrides all rhetoric**. Core principles for external presentation (read the method file for details):
- **Do not write a paragraph thanking the reviewer or restating positive feedback**; go directly to W1. Provide a face-saving path through **positive framing** inside the answer ("we did not state this upfront; in the camera-ready we will state it"), not through flattering opening remarks.
- **W numbering quotes the reviewer's original sentence verbatim** (do not paraphrase); for each item, **answer the literal slot directly in the first sentence** and mirror the subject-verb-object structure (`What is X?`→`X is…`); put mechanism/evidence afterward.
- **Answer every clause in a multipart question**; politeness does not constitute a separate question.
- **Three-way tense discipline**: present tense for theory / perfect tense for completed experiments / **future tense for manuscript edits: "In the camera-ready we will…"**; ⚠️ **never pretend an edit has already been made** ("is now stated" / "the revised X reads"). Editorial `we will` is legitimate; what is forbidden is "using a promise to brush off substantive/experimental work requested by the reviewer."
- **Express boundaries as positive technical conditions**, not as apology/limitation; do not volunteer unasked-for weaknesses, and do not describe a substantive objection as "only a clarity issue."
- **deletion test**: every sentence must serve one of answer-slot / definition / connection / evidence / camera-ready-edit; otherwise delete it. Use tables only for **multi-column comparisons**; inline numbers when possible, and do not optimize for word count.
- (The spirit of the original "humility/provide a face-saving path" is preserved in §0.3 and §1, but **implemented through positive framing inside the answer, not through flattering opening remarks**; §2 no groveling, no self-sabotage = ammunition test.)
