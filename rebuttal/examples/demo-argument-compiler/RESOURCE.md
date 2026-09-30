# RESOURCE — demo-argument-compiler (Budget Quotas)

Rebuttal campaign primarily consumes **API calls** (raise gate + writing + diagnostics) and (optionally) **compute for additional experiments**.

## Two Iron Rules
1. **Raise gate calls are the most expensive signal; never waste them**: Invoke them only at pre-registered gate points (r0 baseline / r7 scoring). Each scoring run = each P0 reviewer × {DeepSeek, Codex} × number of samples. Never repeatedly score unfinished work.
2. **Additional experiments (if CARD.allow_new_experiments=true) must use ExpAuto compute**: Push them to a remote GPU to run and write the results to NFS; perform only static linting locally. Never run long experiments locally.

## Budget Table (parallelism=1 by Default)
| Resource | Per-Round Limit | Usage |
|---|---|---|
| Raise gate calls | Number of P0 reviewers × 2 judges × 3 strategies × samples (default 3) | Score the batch once at r7 (`verify_batch` concurrently); never repeatedly try individual items |
| Writing sub-agent | 3 (in parallel) | One per strategy, physically isolated to prevent cross-contamination |
| Diagnostics/evidence | Main agent, sequentially | Run r1-r5 on the main path; write intermediate artifacts to the ledger as external memory |
| Additional experiments | See CARD.experiment_budget (TBD, off by default) | When allowed, reuse the ExpAuto GPU pool; submit-detach without blocking |

## Raise Gate Call Wrapper (Copy Verbatim)
```python
# DeepSeek side (ranking + authoritative judge)
from verify_rebuttal import verify_batch   # $AUTOREBUTTAL_ROOT/rebuttal_verifier/
cases = [{"review": r.text, "rebuttal": draft, "initial_rating": r.rating,
          "confidence": r.conf, "soundness": r.s, "presentation": r.p,
          "contribution": r.c, "note_id": f"{slug}-{r.id}"} for r in p0_reviewers]
ds = verify_batch(cases, workers=8)         # -> [{reaction, quality, reasoning}, ...]

# Codex side (consensus, independent prompt, same persona, never provide the label) → mcp__codex__codex
# Clear the gate ⇔ for every P0, ds.reaction==raise AND codex.reaction==raise
```

## Notes
- **The worker cannot see inside the raise gate**: The writing agent cannot access the details of the θ₀ prompt and must not fit its output to the evaluation criteria.
- Use sampling for stability: The gate has ±0.05 noise; take several samples for each (reviewer, judge) and use the majority result. Never trust a single sample.
- `parallelism=1` by default: Process papers sequentially, and do not move to the next paper until consensus says to raise the rating for the current paper.
