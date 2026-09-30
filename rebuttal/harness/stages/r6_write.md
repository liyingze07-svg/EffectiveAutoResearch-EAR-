# stage r6_write — Write one rebuttal draft for a (reviewer, strategy)

> The engine runs this file in a **fresh context**. Use only the inputs declared below, with no conversation history. The artifact is **one reviewer-facing rebuttal body**.

## Slots (filled by the orchestrator)
`{{SLUG}}` `{{REVIEWER}}` `{{STRATEGY_FILE}}` (`strategies/<s>.md`) `{{STRATEGY_ID}}` `{{N}}` (round) `{{SEED}}` (carry-forward seed or None)

## Inputs (read only these exact files)
- `campaigns/{{SLUG}}/REBUTTAL_CARD.json` → extract the concerns + OA + stance for `{{REVIEWER}}`
- `campaigns/{{SLUG}}/ledger/concern_ledger.json` → each concern's **`real_concern` (the real concern)** + severity + stance (r2 diagnosis; the writer must use it to choose the approach)
- `campaigns/{{SLUG}}/ledger/evidence_pool.json`
  🔴 **If this file is missing, falling back to `evidence_map.json` is forbidden; stop immediately and report an error**. `evidence_map.json` is the **unfiltered** evidence base produced by r1: it has no `evidence_status` and **does not remove experiments with a REJECT verdict**. Using it for writing = writing unaccepted/REJECTed experiments into the draft as completed evidence (this happened in an actual 01-wdData/37ch run: the draft said "our overlap stress test measured" for `01-E-overlap`, even though that experiment's ACCEPTANCE verdict was REJECT). The correct action when it is missing: **do not write a draft**; report "evidence_pool.json is missing; run r5_evidence_merge first". → evidence bound to each concern + `evidence_status` (met/partial/unmet) + `persuasion_verdict` + **`framing_hint`**. **Use only real evidence with `evidence_status != unmet`; for unmet evidence, use the warrant fallback ladder to concede, and never fabricate.**
  - **You must follow `framing_hint` (the verdict from the r4_experiment_persuasion persuasion gate, already compiled for response according to v0.4)**: `met/STRENGTH` → write the evidence as a **literal direct answer** (when completed, mirror the subject/verb/object); `partial/LOWER_BOUND` → write only the **honest lower bound**, and **never** generalize it to 'stable/robust/in general' (overclaim = ammunition); `unmet/CONCEDE` (even if the experiment actually ran and passed X1-X6) → **it must not be used as a strong point**; use move-6 of the warrant fallback ladder to state the limitation once as a positive scope condition, then close.
- `papers/{{SLUG}}/review.md` → the original review text from `{{REVIEWER}}`
- relevant `campaigns/{{SLUG}}/experiments/<expid>/results.json` → use only the real numbers in `derived` + `interpretation`
- **`harness/strategies/CRAFT.md` → internal logic (general rules + three-way routing by stance + no cringing capitulation or self-sabotage + 14 concern playbooks + the real concern quick reference): reason through** what the real concern is, what evidence to use, and what stance to take. **Read this first.**
- **`harness/strategies/write-direct-rebuttals.md` → primary method for external presentation (response compilation): how to write the final reviewer-facing draft. Literal direct answer for each slot / `verbatim` labels / no pleasantries / three-way tense split / deletion+ammunition.**
- `harness/{{STRATEGY_FILE}}` → this strategy's posture (differentiated tradeoffs layered on top of CRAFT)
- the general rules in this file (below)

## Writing = internal logic (CRAFT + argument compilation) → external response compilation (write-direct-rebuttals)
1. **Reason it through internally**: for each concern, use **CRAFT §3/§5** to select the playbook for the r2-diagnosed `real_concern` (the real concern) + use **CRAFT §1** to set the stance; perform the argument compilation below to guarantee rigorous logic and traceable warrants.
2. Make tradeoffs according to the posture in `{{STRATEGY_FILE}}` (what to address, ordering, depth of concession).
3. **Produce the external draft according to `write-direct-rebuttals.md` (response compilation)**: two passes—first provide a literal direct answer for each reviewer slot (mirror the subject/verb/object), then compile each W into one continuous prose paragraph. **Use `verbatim` quote labels, write no acknowledgment paragraph, apply the three-way tense split (edits=future tense; never pretend an edit is already made), frame boundaries as positive conditions, and pass deletion+ammunition**. Logic stays in a separate internal English `Logic:` file; directness goes into the external-facing text. See "Output Format."

## Argument compilation (4 passes, strictly in order; this is a reasoning task, not next-token)
1. **Pass 1 Build the argument DAG**: set a strategic objective for each concern (move the reviewer from X to Y) → work backward to derive the claim chain → attach one warrant to each claim (pointing to real evidence in evidence_map). The chain's endpoint = the strategic objective. **Do not write prose yet.**
2. **Pass 2 Semantic checks**: every claim must follow from its predecessors+warrant (no gaps) · every warrant must link to real evidence (link failure=fabrication→demote to `[TBD]`/delete) · no redundancy · endpoint=objective.
3. **Pass 3 Render**: DAG→prose, with one claim node=one sentence and connectives encoding the logical edges. **The next sentence must be the next node; generating content outside the DAG is forbidden.**
4. **Pass 4 Reverse-compilation validation**: re-parse the prose into a claim set; it must be ⊇ the DAG (no semantics dropped/added).

## 🔴 Honesty rule (substantive honesty, not performative honesty — important)
Honesty means **not misrepresenting facts**, not **repeatedly declaring one's honesty in the body**. The latter appears insecure, hands the reviewer a vulnerability, and makes the paper look weaker.
- **Do**: every number/claim must be traceable to real evidence; use `[TBD]` when that is impossible; concede when no warrant can genuinely be obtained.
- **Do not (these are soft ammunition and will lose points/be blocked)**:
  - Performative honesty formulations: `we honestly concede / we will not manufacture / we did not spin it / we prefer to concede rather than assert / we are careful not to over-claim / we disclose ... honestly`.
  - Tag every concession with `(conceded)`, or repeatedly say "this is a fair criticism."
  - Over-concede: answer confidently with evidence when a confident answer is available; make the concession **in one sentence + immediately return to strength**, without elaborating or repeating it.
- **The correct form for a concession**: state the limitation once (briefly) → immediately give its scope or compensating evidence → close. Example: do not write "we honestly have no long-CoT infrastructure and will not manufacture results"; write "Long-form CoT is outside our current scope; the tradeoff already persists at 27B (0.248/0.402), and we mark it as future work."
- **State a caveat/proxy fact only once** (for example, "junk is a proxy for the authenticity-detector"); do not add self-professions such as "we are explicit that ... not synthetic."

## carry-forward (if `{{SEED}}` is not None)
Revise `SEED.prior_best_rebuttal`: retain what works, supplement it according to `SEED.apply_advice`, and delete `SEED.avoid_phrases`. Do not rewrite from scratch.

## DO-NOT (hard)
- Do not fabricate numbers/citations; do not present experiments that were not run as completed; make no empty promise (`"we will run/add"` for P0 = ammunition).
- Do not generate content outside the DAG (Pass 3 is locked).
- Do not use the performative honesty formulations above / do not over-concede.
- **Physical isolation of DRIVE/ACQUIT (hard): never read judge internals** — do not read `rebuttal_verifier/` (`consensus_gate.py`/`prompt_template.py`/`verify_rebuttal.py`), do not read `harness/stages/r7_gate.md`, `b1_concern_gate.md`, `b2_faithfulness_gate.md`, `b3_ammunition_gate.md`, and do not read `AMMO_PATTERNS` in `harness/runner/coach_loop.py`. Read only the exact files listed under "Inputs" above. Seeing the criteria = fitting to the criteria = the entire round is invalid.

## Output Format (hard constraints — **response compilation paradigm**; read `strategies/write-direct-rebuttals.md` for the primary method)
> Directness overrides rhetoric: rebuttal = a compilation of the **minimal, literal, honest direct answer** to each reviewer slot. CRAFT §0–5 provides the **internal logic** (the real concern/stance/playbook); this section + write-direct-rebuttals governs **external presentation**.
1. **Write no acknowledgment/restatement-of-praise paragraph — go directly to W1.** Provide an off-ramp through **positive framing** inside the answer (for example, "we did not state this upfront; in the camera-ready we will state it before first use"), not through opening flattery.
2. **W label = a `verbatim` quotation of the reviewer's original sentence**, not a summary of the real concern. If it is too long, retain the complete key clause and do not insert fabricated ellipses. (Keep summaries of the real concern in the internal English `Logic:` file.)
3. **First sentence = the literal direct answer to the slot**, mirroring the reviewer's subject/verb/object (see the mapping table in the method file: `What is X?`→`X is…`; `Is it A/B/both?`→`It is…`). Put mechanism/evidence from the second sentence onward. **A reframe or pleasantry must not be the first sentence.**
4. **Answer every clause of a multipart question**; do not answer a polite expression ("Can you speak to this?") as a standalone question; merge it into the substantive question that follows.
5. **Three-way tense split**: existing theory=present tense; completed experiment=past/present perfect; **manuscript edit=future tense, `In the camera-ready version, we will <specific change>`**. ⚠️ **Never describe an edit that has not been made as "is now stated / the revised X reads" (=pretending it is already changed=overclaim).** Editorial `we will` (define terminology/redraw a figure/add citations/reorder material) is **legitimate**; what is forbidden is only "using a promise to **fob off the substantive/experimental work requested by the reviewer**."
6. **Table demotion**: use a markdown table only for **multi-column comparisons**; for a single quantity/a sequence of like-valued numbers → use inline prose. **Do not chase a word count**—length is determined by the **deletion test** (every sentence must serve one of answer-slot / definition / connection / evidence / camera-ready-edit; otherwise delete it); do not worry about a minimum. Only shorten when overly long + use cross-references.
7. **Boundary = a positive technical condition, not an apology/limitation** ("The theorem applies when …", not "we did not test X"). Do not volunteer unasked-for weaknesses, and do not characterize a substantive objection as "only a clarity issue."

## Output (write this exact file)
`campaigns/{{SLUG}}/drafts/round{{N}}/{{REVIEWER}}__{{STRATEGY_ID}}.md` — reviewer-facing rebuttal body, **strictly following the 6 hard constraints in "Output Format" above** (labels + conclusion first + table + humble opening + no future-tense empty promises + use the full 4000–5000 characters).
receipt (return one line): `{reviewer, strategy, draft_path, char_count, concerns_covered}`. If char_count exceeds 5000 → shorten; if below 3000 → increase evidence density before submitting.
