# stage ac_package — AC meta-comment and delivery package

> Fresh engine context, run after every targeted reviewer has converged. Produces the confidential Area Chair comment and the campaign delivery index. **Based only on the real per-reviewer rebuttals and accepted evidence** — it introduces no new claim and no new number.

## Slot `{{SLUG}}`

## Inputs (read-only)
- `campaigns/{{SLUG}}/REBUTTAL_CARD.json` — paper metadata and targeted reviewers
- `campaigns/{{SLUG}}/ledger/loop_results.json` — status, strategy and round for each reviewer
- Each final draft at `campaigns/{{SLUG}}/drafts/<reviewer>.md`
- `campaigns/{{SLUG}}/ledger/ACQUITTAL.json` if present
- `campaigns/{{SLUG}}/ledger/evidence_pool.json` — the evidence that was merged in

## Rules (numbered)
1. The **AC comment** summarises across reviewers: what substantive evidence or revision was added, and how the main worries were resolved. Use **only** content that already appears in the individual rebuttals plus accepted evidence. **Add no new claim and no number that is not already in a rebuttal.**
2. **Label honestly**: for every reviewer with `status=HONEST_CONCEDE`, state what was conceded and what remains open.
3. **No soft ammunition**: no performative honesty, no empty promises (the same ammunition rules as in writing).
4. **Package index**: list each reviewer's final draft path, status, winning strategy and round count.

## Output (write exactly these two files)
- `campaigns/{{SLUG}}/AC_COMMENT.md` — the confidential meta-comment to the Area Chair (prose, concise).
- `campaigns/{{SLUG}}/ledger/package.json`
```json
{ "paper":"{{SLUG}}",
  "per_reviewer":[{"id":"WaDR","status":"PASS","strategy":"s1_evidence_locked","rounds":1,"draft_path":"campaigns/.../drafts/WaDR.md"}],
  "experiments_used":["02-E-downstream (ACCEPT)"],
  "open_items":["<what remains open after an HONEST_CONCEDE>"],
  "generated_by":"ac_package" }
```
Receipt (one line): `{reviewers, passed, conceded, ac_comment_path}`.

## DO-NOT
- Do not introduce a new claim or a new number; only restate what is already in a rebuttal.
- Do not dress up an HONEST_CONCEDE; do not write empty promises or performative honesty.
