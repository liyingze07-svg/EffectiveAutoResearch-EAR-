# Benchmark results — why DeepSeek V4 Pro

## Task
Predict how an ICLR reviewer revises their overall score after reading an author
rebuttal: **raise / same / lower**. `raise` = the rebuttal was strong enough to
earn a score increase (a "high-quality" rebuttal).

## Data
- Source: **ICLR 2025** public peer review, via OpenReview + the
  [ProReviewer](https://huggingface.co/datasets/UKPLab/ProReviewer-Dataset) dataset.
- Label = sign(final_rating − initial_rating), where **initial_rating** comes from
  ProReviewer (scraped before the discussion phase) joined by review **note id** to
  the **final** rating from OpenReview's current note. This sidesteps OpenReview's
  hidden edit history (initial ratings are unreadable for ~64% of notes).
- True class distribution over ~2,800 reviews: **same 78.5% / raise 20.6% / lower 1.0%**.

## Evaluation protocol (fair, contamination-free)
- **Per-example, isolated**: every model classifies each case in its OWN context
  (temperature 0). No model ever sees the batch distribution or other cases —
  this matters; a batch/all-at-once pass lets a model calibrate to the class
  balance and is NOT comparable.
- Metric: **macro-F1 over classes present in the gold** (so an absent class does
  not dilute the average).
- Reported set below: a **balanced 36-case subset** (18 raise + 18 same; `lower`
  omitted because no model ever predicts it and it has ~1% support).

## Cross-model zero-shot comparison (balanced 36-subset, identical prompt)

| Rank | Model | macro-F1 | acc | raise F1 | same F1 | pred raise/same |
|-----:|-------|:--------:|:---:|:--------:|:-------:|:---------------:|
| 1 | **deepseek-v4-pro** | **0.805** | 0.806 | 0.80 | 0.81 | 17/19 |
| 2 | Sonnet-5            | 0.777 | 0.778 | 0.79 | 0.76 | 20/16 |
| 3 | Opus-4.8            | 0.721 | 0.722 | 0.71 | 0.74 | 16/20 |
| 4 | deepseek-v4-flash   | 0.694 | 0.694 | 0.69 | 0.70 | 17/19 |
| 5 | Codex / GPT-5.5     | 0.682 | 0.694 | 0.62 | 0.74 | 11/25 |

(True labels: 18 raise / 18 same. "pred raise/same" shows calibration.)

### Full 57-case test set (realistic distribution), DeepSeek V4 Pro
| framing | macro-F1 |
|---|---|
| 3-class incl. lower (lower support 6, F1 0.00) | 0.503 |
| raise + same only | 0.755 |

## Cross-model on EMNLP/ARR (5 models × 2 tasks, per-example isolated)

Two tasks: **EMNLP-v2** = raise/same outcome, macro-F1 on `emnlp_test` (n=56);
**OA=3** = rebuttal-quality separation on `oa3_all` (n=54) = raise-rate on genuinely-
good rebuttals minus on clearly-weak ones (higher = better quality discrimination).

| Model | EMNLP-v2 macro-F1 | OA=3 RAISE-recall / weak-raise / **separation** |
|---|:--:|:--:|
| **deepseek-v4-pro** | **0.730** | 0.78 / 0.67 / +0.13 |
| Sonnet-5 | 0.677 | 0.81 / 0.75 / +0.07 |
| deepseek-v4-flash | 0.696 | 0.89 / 0.83 / +0.06 |
| Opus-4.8 | 0.661 | 0.89 / 0.83 / +0.04 |
| **GPT-5.5 (xhigh)** | 0.624 | 0.93 / 0.67 / **+0.28** |

- **deepseek-v4-pro** is the best all-rounder (top EMNLP-v2, 2nd OA=3) → default backbone.
- **GPT-5.5** has the best OA=3 quality discrimination (+0.28) but worst outcome-fit →
  we route **OA=3 to GPT-5.5**. Caveats: GPT-5.5 ran at **xhigh reasoning** (not
  apples-to-apples with the temp-0 single-pass others), and OA=3 n=54 CIs are ~±0.15,
  so the +0.28 vs +0.13 gap is suggestive, not conclusive. Access: `scripts/oa3_gpt5_batch.py`
  (remote Codex) or `--template route` with an OpenAI key.

## Takeaways
1. **DeepSeek V4 Pro wins** and beats every flagship (Opus 4.8, Sonnet 5, GPT-5.5)
   on this task, with the best calibration → chosen as the packaged backbone.
2. Backbone strength dominates; prompt optimization (DSPy MIPROv2) overfit the tiny
   val set and did **not** beat the zero-shot θ₀ prompt on held-out test. So the
   shipped skill uses the **θ₀ zero-shot prompt**, no fine-tuning.
3. **`lower` is effectively unpredictable** — reviewers almost never drop a score
   after a rebuttal (~1%), and no model predicts it. Treat the skill as a strong
   **raise-vs-not** detector; do not trust a `lower` output.
4. Absolute numbers are on small eval sets (36 / 57); treat gaps < ~0.03 as noise.
