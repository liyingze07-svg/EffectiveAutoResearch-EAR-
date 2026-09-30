# ammunition-checklist.md — ammunition grep checklist (the final draft must have 0 matches)

"ammunition" = phrasing in the rebuttal that **hands the reviewer an attack surface / exposes one's own weaknesses / frames an excessive concession**. Handing the reviewer a ready-made attack is itself a failure. Before invoking any Type-B gate (especially a raise gate), the final draft must pass this checklist with grep == 0.

> **⚠️ Authoritative judgment = semantic gate `b3_ammunition_gate.md` (independent judge, not grep).** The regex (`coach_loop.AMMO_PATTERNS`) is too static to keep up with the endless variants of "sharpen/streamline/tighten…", and it cannot distinguish "we will revise X" (ammunition) from "the revised X reads:'…'" (not ammunition). Therefore, the regex **has been downgraded to a free ranking hint in cheap_eval** and no longer serves as a clearance gate; **before PASS, the B3 semantic judge must read the full text sentence by sentence and classify type A–E ammunition according to each sentence's meaning**. This checklist is the **definition of the judgment criteria** for the B3 judge (provided for it to read), not a pattern table for grep.

grep is a **signal**, not truth: a match is only a ranking hint; the real judgment is in B3. Prefer rephrasing the sentence over leaving a self-attack for the reviewer.

## A. Exposing one's own weaknesses / revealing one's hand (prohibited in the main text)
- not tested / not yet verified / did not have time yet / due to time / we did not test
- leave for follow-up / future work will / we plan / we plan to (unless it is a sincere action item and not a core claim)
- we do not claim / we do not claim / no assurance / no guarantee that
- honestly speaking / to be honest / frankly / admittedly (turning a concession into a display of weakness)
- there may be a problem / might be flawed / uncertain whether / it is unclear whether (about one's own method)
- this is indeed a limitation / this is indeed a limitation (ending without a pivot)

## B. Excessive concession / accepting the framing (prohibited)
- we acknowledge this is merely / we agree this is merely / indeed just a combination / just a combination (accepting the framing of the novelty attack)
- the reviewer is right; our method [weakness] (accepting it without a pivot)
- we agree [core claim] is problematic / we agree that [C1] is problematic

## B2. Performative honesty / excessive concession (soft ammunition — newly added, encountered in an actual run this time)
Honesty means **not misrepresenting facts**, not **repeatedly declaring one's honesty in the main text**. Writing "I am very honest" explicitly = appearing guilty + handing over a vulnerability + making the paper look weaker. Rewrite any match (remove the declaration, retain the facts):
- we honestly concede / we disclose ... honestly / we did not spin it / honest scope / honest caveat
- we will not manufacture (results) / we prefer to concede ... rather than assert / we are careful not to over-claim
- attaching a `(conceded)` label to every concession / this is a fair criticism (repeatedly)
- repeatedly explaining the same caveat/proxy ("we are explicit that ... not synthetic") — stating the fact once is sufficient
- expanding a concession into a long paragraph (should be: mention it in one sentence + immediately pivot back to strength/scope/compensating evidence)
**Correct formulation**: state the limitation once → immediately provide scope or compensating evidence → close. Do not turn honesty into a performance.

## C. Empty promise vs legitimate editing commitment (distinguish them; do not treat them indiscriminately)
**Prohibited (= ammunition)**: using a promise to **fob off the substantive/experimental work requested by the reviewer** —
- we will additionally run experiment X / we will run/add experiments / provide new results (for a P0 substantive concern)
- if accepted, we will / if accepted we will
- cannot due to space limitations (used as an excuse for not doing it)

**Legitimate (not ammunition)**: for **editing requests** (define terminology/redraw a figure/add a citation/reorder subsections), use the camera-ready future tense —
- `In the camera-ready version, we will define/redraw/add-citation/reorder X` (manuscript edits naturally use the future tense; this directly answers "please define/add X")

## C2. Pretending a change has already been made (prohibited, overclaim)
Describing a manuscript edit that **has not been materialized** as already completed — rewrite any match back into the future tense:
- "is now stated / the revised X reads: '…' / we have revised X to '…'" (at the rebuttal stage, the paper often has not yet been revised → falsely reporting completion)
- Correct: `In the camera-ready version, we will …`

## D. Opening a new attack surface (prohibited)
- proactively mentioning a weakness not raised by R_j in order to respond to R_i
- "another possible problem is…" (finding fault with oneself)
- introducing a new claim that is absent from the paper and unsupported by evidence (an assertion without warrant)

## E. Dishonesty (red line, direct failure rather than a rewrite)
- claiming an unperformed experiment was performed / presenting [TBD] as completed
- fabricated numbers / fabricated or irrelevant citations
- reporting FAIL as PASS / exaggerating the magnitude of improvement

---
grep implementation: perform a regex scan of `drafts/final_rebuttal.md` for the phrasing above (Chinese and English), and output the matching line numbers. A–D match → rewrite; E match → campaign failure (fabrication), go back and redo it.
