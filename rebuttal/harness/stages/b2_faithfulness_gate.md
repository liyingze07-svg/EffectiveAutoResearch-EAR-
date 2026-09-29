# stage b2_faithfulness_gate — B2 faithfulness gate (the no_fabrication hard gate)

> Fresh engine context, run on the **selected draft that has already cleared the raise/strength gate**. This is the mechanical implementation of the `no_fabrication` predicate in GOAL.md. **The judge is frozen.** A FAIL here **blocks PASS outright** — this is enforcement of the fabrication red line, not a rewriting suggestion.

## Slots `{{SLUG}}` `{{REVIEWER}}` `{{DRAFT_PATH}}`

## Inputs (read-only)
- `{{DRAFT_PATH}}` — the rebuttal draft under inspection
- `campaigns/{{SLUG}}/ledger/evidence_pool.json` — the real evidence and its `evidence_status`
  🔴 **If this file is missing, do not fall back to `evidence_map.json`.** That file is the **unfiltered** evidence base produced by r1: it has no `evidence_status` and no ACCEPT/PARTIAL filtering, so using it as the evidence source defeats check 3 below. When it is missing, return `verdict=BLOCKED` and write in `reasons` that `evidence_pool.json` is absent, r5 has not run, and acceptance status cannot be verified. Do not return PASS and do not return FAIL.
- The relevant `campaigns/{{SLUG}}/experiments/<expid>/results.json` — the real `derived` numbers

## Checks (numbered, red lines)

1. **Every number has a source**: each quantitative claim or number in the draft traces to a real `derived` value in the evidence pool or in `results.json`. **A number with no source is fabrication.**
   **Tolerance (precision-aware; passing either test is enough)**:
   - **Rounding-compatible (check this first)**: round the real `derived` value to **the precision at which the draft actually writes it** (decimal places or significant figures). If that equals what the draft wrote, it passes.
   - **Relative error < 1%**: use this when the written precision is high enough.
   Failing both means fabrication.
   > Why not a flat 1%: for small values a fixed relative tolerance is **mathematically unsatisfiable**. The most honest one-significant-figure rendering of `0.0075218` in prose is `0.008`, whose relative error is necessarily 6.4%; a flat 1% would **condemn honest rounding as fabrication**. The criterion must punish **invention**, not **rounding**.
2. **Citations are real**: every citation or result genuinely exists in the paper assets or the evidence. **No invented citations.**
3. **Experimental honesty**: no experiment that lacks an ACCEPT or PARTIAL acceptance is described as having been performed.
4. **No `[TBD]` masquerading as fact**: nothing stated as fact may contain a `[TBD]`.
5. **No over-claiming**: no claim exceeds what the evidence supports — no dressing a FAIL up as a PASS, no inflated deltas, no using `unmet` evidence as if it were `met`.

## Output (write exactly this file)
`campaigns/{{SLUG}}/ledger/B2_{{REVIEWER}}_faithfulness.json`
```json
{ "verdict":"PASS|FAIL",
  "checked_numbers":[{"claim":"+2.3% over X","value":"2.3","source":"results.json#derived.delta","ok":true}],
  "invented_citations":[], "unsupported_claims":[], "overstatements":[], "reasons":[] }
```
Receipt (one line): `{verdict, n_unsupported}`.

## Rules (hard)
- **Any unsourced number or invented citation → `verdict=FAIL`**: the draft must not PASS; the loop has to fix it or concede honestly.
- Mechanically check facts against sources only. **Do not judge persuasiveness, do not read the raise gate's internals**, and do not edit the draft.
- A number that does not match its source, or a source that does not point at a real file, makes that item `ok:false`, which means FAIL.
