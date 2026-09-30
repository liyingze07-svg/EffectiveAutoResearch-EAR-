# stage b3_ammunition_gate — Ammunition Semantic Gate (Independent Judge, Prevent Self-Sabotage)

> **Executed in a fresh engine context distinct from the writer** (DRIVE/ACQUIT separation). **Semantic judgment, not grep** — regex can only catch literal wording, cannot keep up with the infinite variants of "sharpen/streamline/tighten/polish…", and cannot distinguish an "empty promise" from "providing exact text". This gate understands **sentence meaning**: whether a sentence hands the reviewer an attack surface / exposes one's own weakness / makes an empty promise / over-concedes / engages in performative honesty / commits fabrication. A draft that clears the strength gate (r7) must still clear this gate before it counts as PASS; any hit blocks it and sends it back for rewriting.

## Slots `{{SLUG}}` `{{REVIEWER}}` `{{DRAFT_PATH}}`

## Input (read-only)
- `{{DRAFT_PATH}}`: rebuttal draft to inspect
- `harness/shared-assets/ammunition-checklist.md`: definitions of ammunition categories A–E (source of the criteria)

## Inspect Each Category Semantically (understand sentence meaning; do not match literal wording)
| Category | Ammunition = | Critical semantic distinction (which regex cannot make) |
|---|---|---|
| **A Self-exposed weakness/leakage** | untested/not yet verified/due to time/we did not test; presenting what was not done as a limitation without a turn | Stating a **bounded scope limitation** (with however + evidence) ≠ ammunition; a bare "we have not tested X yet" = ammunition |
| **B Over-concession/accepting the frame** | "we agree this is merely/just a combination"; accepting the frame of a novelty/soundness attack without a turn | Conceding clarity/presentation ≠ conceding that the contribution collapses; **concede one point + immediately reposition the value** ≠ ammunition |
| **B2 Performative honesty (soft ammunition)** | "we honestly concede / will not manufacture / did not spin it / (conceded) label / repeated fair criticism" | Stating a fact once ≠ ammunition; **repeatedly declaring "I am very honest" in the main text** = ammunition |
| **C Empty promise vs legitimate editing promise** | Using a promise to **brush aside the substantive/experimental work requested by the reviewer** | ⚠️**Core distinction (correcting the old criterion)**: "we will run/add **experiments** / provide new results" for a P0 **substantive** concern = **ammunition** (brushing it aside); but `In the camera-ready version, we will define/redraw/add-citation/reorder X` for an **editing request** (define a term/redraw a figure/add a citation/change the order) = **legitimate and correctly tensed** (manuscript edits inherently use the future tense). Determine whether this defers the **substantive/experimental** work requested by the reviewer or promises a single **editing revision** |
| **C2 Pretending an edit is complete (overclaim, newly added)** | Writing an **unmaterialized** manuscript edit as "is now stated / the revised X **reads** / we **have revised** X" | The paper is usually not yet revised at the rebuttal stage; writing about an edit in the present (perfect) tense = falsely reporting it as complete = **overclaim**. An edit must use the future tense `we will`, **not pretend it is already complete** (the old criterion was wrong; this is now corrected) |
| **D Opening a new attack surface / downplaying / over-claiming** | Volunteering a weakness that was not asked about; "another potential issue is…"; **calling a substantive objection "only a clarity issue"**; extending a claim beyond the evidence; asserting real-world universality without support; introducing a new promise/metric/setting/assumption that the answer does not need | Answering what the reviewer asked ≠ ammunition; volunteering a confession / downplaying a substantive objection / making an out-of-bounds claim = ammunition |
| **E Dishonesty (red line)** | Claiming an experiment was performed when it was not / fabricating numbers or citations / reporting FAIL as PASS / exaggerating an improvement | Immediate failure; do not rewrite |

## Rules
1. **Read the entire text sentence by sentence**; for every suspicious sentence, determine which category it belongs to, explain why, and provide a **rewrite recommendation** (remove the ammunition while preserving the facts).
> 🔴 **Your task is exhaustive detection, not adjudication.** The driver will **recompute** `verdict` in code according to the category table in §6,
> and take the **union of hits across N consecutive calls** (default N=3). Therefore:
> · Your self-reported `verdict` is for reference only; missing one hit is the real loss — prefer reporting more suspicious items to missing any.
> · Empirical basis: when the same draft was judged 10 times, the adjudication was faithful to §6 in 10/10 cases (no drift); what drifts is **detection** —
>   the same substantive instance of over-claiming (category D) was detected in only 60% (medium)/ 80% (xhigh) of the runs.
> · Read every sentence; do not sample. Emit one hit for every suspicious sentence; if the category is uncertain, report it under the more severe category.

2. Any A–D hit → `verdict=HAS_AMMO` (block PASS and send it back to be revised according to rewrite). **An E hit → HAS_AMMO and mark `red_line=true`** (fabrication; send it back to be redone without changing the numbers).
3. **Prefer a missed report to harming good wording**: editing language such as `In the camera-ready we will …`, a positively qualified scope boundary, and a one-time factual statement are not ammunition. The criterion is "whether this sentence hands the reviewer a weakness / defers substantive work / falsely reports that an edit is complete", not the sentence pattern.
4. **deletion test (argument compilation)**: additionally mark whether each sentence **performs exactly** one function (answer a slot / define / connect / provide evidence / camera-ready-edit); mark a sentence outside these functions as `deletable` (redundant; recommend deletion) — this does not count as HAS_AMMO, but record it in hits for compression.
5. **direct-answer mirror check**: determine whether the first sentence of each W block **literally mirrors the subject/verb/object of the reviewer's statement** (not reframe/praise); otherwise mark it `not_direct` (recommend changing it to a literal direct answer).
6. If there is any A–D/C2 hit → `verdict=HAS_AMMO`; if the entire text has no hits (deletable/not_direct are recommendations only) → `verdict=CLEAN`.

## Output (write this exact file)
`campaigns/{{SLUG}}/ledger/B3_{{REVIEWER}}_ammunition.json`:
```json
{ "verdict":"CLEAN|HAS_AMMO", "red_line":false,
  "hits":[ {"quote":"original sentence", "category":"A|B|B2|C|C2|D|E|deletable|not_direct", "why":"why (ammunition/redundant/not a literal direct answer)", "rewrite":"how to rewrite it (preserve the facts)"} ] }
```
receipt: `{verdict, n_hits, red_line}`.
