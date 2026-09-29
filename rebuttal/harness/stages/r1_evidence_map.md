# stage r1_evidence_map — evidence base

> Fresh engine context. paper + card → `evidence_map.json`: everything that can be cited honestly.

## Slot `{{SLUG}}`
## Inputs (read-only): `papers/{{SLUG}}/Tex/`, `campaigns/{{SLUG}}/REBUTTAL_CARD.json`, and a scan of existing experiment result directories.

## Rules
1. Anchor every `paper_claim` to a real section, figure, table or theorem (`claim_anchors`).
2. Give every `concern_seed` a `response_mode` (clarify / existing / experiment / concede / literature, following the feasibility ladder), the `evidence` behind it (a real location, a path to an existing result file, or the expid that would be needed), and `ready` (available now, or waiting on an experiment).
3. **Anchor only evidence that actually exists — never invent one.** If you cannot anchor it, concede.

## Output: `campaigns/{{SLUG}}/ledger/evidence_map.json` (`{claim_anchors:[], concern_evidence:[]}`). Receipt: `{n_anchors, n_concern, n_ready, n_wait_experiment}`.
