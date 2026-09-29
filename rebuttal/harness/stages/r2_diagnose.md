# stage r2_diagnose — diagnose the concerns

> Fresh engine context. review + card → `concern_ledger.json`.

## Slot `{{SLUG}}`
## Inputs (read-only): `papers/{{SLUG}}/review.md`, `campaigns/{{SLUG}}/REBUTTAL_CARD.json`, `harness/shared-assets/rebuttal-tips.md` (the taxonomy).

## Rules (for each atomic concern)
1. **Diagnose the real concern**: what the reviewer wrote versus what they are actually worried about. Is it a **misreading** (the paper does contain it) or a **real gap**? Is there a **frame lock** — a case where answering point by point will not help because the framing has to be broken first?
2. Classify it (`type`) and assign a **priority** of P0/P1/P2 (P0 = the main reason the score is low, typically a low score held with high confidence).
3. Cluster across reviewers: the same worry maps to one piece of evidence, recording which reviewers raised it.

## Output: `campaigns/{{SLUG}}/ledger/concern_ledger.json`, one entry per concern: `{id, cluster, reviewers[], type, surface, real_concern, misread_or_gap, frame_lock, priority}`. Receipt: `{n_concern, n_P0, n_frame_lock}`.
