# stage b1_concern_gate — B1 concern gate (frozen judge on diagnosis quality)

> Fresh engine context, run once after r2 and before r3. **The judge is frozen and does not improvise**: it only assesses the quality of `concern_ledger`, never edits it and never writes a rebuttal. On FAIL the orchestrator sends the work back to r2 for re-diagnosis — **never carry a bad concern map into writing**.

## Slot `{{SLUG}}`

## Inputs (read-only)
- `campaigns/{{SLUG}}/ledger/concern_ledger.json` — the diagnosis to be checked
- `papers/{{SLUG}}/review.md` — the reviewer's original text, the source of truth
- `campaigns/{{SLUG}}/REBUTTAL_CARD.json` — concerns, OA and stance for cross-reference

## Checks (numbered)
1. **atomization**: every reviewer worry is split into **atomic, separately answerable** items; two distinct objections are **not** merged into one.
2. **real_concern**: each item names what the reviewer is **actually worried about**, not a paraphrase of the literal wording.
3. **coverage**: every substantive point in review.md maps to some ledger item (**no concern is missed**).
4. **no_invented_concern**: the ledger does **not** invent worries the reviewer never raised.
5. **severity/stance sanity**: the P0/P1 assignment and the accept/argue/correct stance hold up (P0 is normally the main score-suppressing concern, typically a low score held with high confidence).

## Output (write exactly this file)
`campaigns/{{SLUG}}/ledger/B1_concern_gate.json`
```json
{ "verdict":"PASS|FAIL",
  "atomization":true, "real_concern":true, "coverage":true, "no_invented_concern":true,
  "per_concern":[{"id":"C1","ok":true,"issue":null}],
  "missing_from_review":[], "reasons":[] }
```
Receipt (one line): `{verdict, n_fail}`.

## Rules
- Any failure among checks (1)–(4) → `verdict=FAIL` (back to r2). Check (5) only records an issue; it alone does not FAIL unless the mismatch is severe.
- Judge quality only. **Never read any gate's internal prompt and never read a rebuttal draft.** Do not edit `concern_ledger`.
