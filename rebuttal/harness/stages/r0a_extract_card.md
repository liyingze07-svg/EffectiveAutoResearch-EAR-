# stage r0a_extract_card — extract the card

> Fresh engine context. paper + reviews → `REBUTTAL_CARD.json`.

## Slot `{{SLUG}}`
## Inputs (read-only): `papers/{{SLUG}}/review.md`, `papers/{{SLUG}}/Tex/main.tex` plus `sections/*.tex`, and a scan of the code and experiment index (to judge whether a concern is addressable).

## Rules
1. Take each reviewer's `initial_overall` (out of 5), `soundness` and `confidence` **verbatim from review.md — do not guess**.
2. `paper_claims` must come from the paper body; `concern_seeds` must come from the review text and must be **atomised** (one weakness or question per entry).
3. Tag every concern with a `type`, with `likely_needs_experiment` (be honest: only true when the reviewer explicitly asks for a new experiment, dataset or baseline **and** the code could plausibly support it), and with a `note` (what to run if an experiment is needed; otherwise which existing evidence, clarification or concession applies).
4. `target.require_raise_on` = reviewers with OA≤3; `maintain` = reviewers with OA≥4. Never invent these.

## Output: `campaigns/{{SLUG}}/REBUTTAL_CARD.json` (schema in `templates/REBUTTAL_CARD.schema.json`). Receipt: `{slug, n_reviewers, n_concerns, n_need_experiment, target}`.
