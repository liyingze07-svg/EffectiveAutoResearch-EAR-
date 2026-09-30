# RESOURCE — {{SLUG}} (Budget Quota)

The rebuttal campaign primarily consumes **API calls** (raise gate + writing + diagnosis) and (optionally) **additional experiment compute**.

## Two Iron Rules
1. **Raise gate calls are the most expensive signal; do not waste them**: invoke them only at the registered gate points (r0 baseline / r7 scoring). Each scoring run = each P0 reviewer × {DeepSeek, Codex} × number of samples. Do not repeatedly score incomplete drafts.
2. **Additional experiments (if CARD.allow_new_experiments=true) must use ExpAuto compute**: push them to remote GPUs for execution, store the results on NFS, and perform only static linting locally. Never run long experiments locally.

## Budget Table (parallelism=1 by default)
| Resource | Per-round cap | How to use it |
|---|---|---|
| Raise gate calls | Number of P0 reviewers × 2 judges × {{N_STRATEGIES}} strategies × samples (3 by default) | Score the full batch once at r7 (`verify_batch` concurrently); do not repeatedly test individual items |
| Writer sub-agent | {{N_STRATEGIES}} (in parallel) | One per strategy, physically isolated to prevent cross-contamination |
| Diagnosis/evidence | Main agent, sequentially | Run r1-r5 on the main path, persisting intermediate artifacts to the ledger as external memory |
| Additional experiments | See CARD.experiment_budget (TBD, disabled by default) | When allowed, reuse the ExpAuto GPU pool; submit-detach without blocking |

## Raise Gate Call Wrapper (Copy Verbatim)
```python
# DeepSeek side (ranking + primary judgment)
from verify_rebuttal import verify_batch   # $AUTOREBUTTAL_ROOT/rebuttal_verifier/
cases = [{"review": r.text, "rebuttal": draft, "initial_rating": r.rating,
          "confidence": r.conf, "soundness": r.s, "presentation": r.p,
          "contribution": r.c, "note_id": f"{slug}-{r.id}"} for r in p0_reviewers]
ds = verify_batch(cases, workers=8)         # -> [{reaction, quality, reasoning}, ...]

# Codex side (deliberation, independent prompt, same persona, never provide the label) → mcp__codex__codex
# Gate cleared ⇔ for every P0, ds.reaction==raise AND codex.reaction==raise
```

## Notes
- **Workers cannot see inside the raise gate**: writer agents cannot access the details of the θ₀ prompt and must not fit their responses to the judging criteria.
- Sample for stability: the gate has ±0.05 noise; take several samples for each (reviewer, judge) and use the majority result. Do not trust a single sample.
- `parallelism=1` by default: process papers sequentially, and do not move to the next paper until the current one has cleared the raise gate by consensus.
