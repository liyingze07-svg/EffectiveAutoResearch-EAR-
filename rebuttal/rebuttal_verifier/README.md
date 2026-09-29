# Rebuttal-Quality Verifier (DeepSeek V4 Pro)

A self-contained skill that judges **how good an author rebuttal is** by
role-playing the target ICLR reviewer and predicting whether they would revise
their score:

| output `reaction` | `quality` | meaning |
|---|---|---|
| `raise` | `high` | the rebuttal is strong enough to earn a score increase |
| `same`  | `neutral` | the rebuttal does not change the reviewer's mind |
| `lower` | `counterproductive` | the rebuttal backfires (rare — see caveat) |

Backbone = **DeepSeek V4 Pro**, chosen because it won a fair cross-model
benchmark (macro-F1 **0.805**, beating Opus 4.8 / Sonnet 5 / GPT-5.5). Full
numbers and methodology in [`results.md`](results.md).

---

## Folder contents
```
rebuttal_verifier/
├── README.md            # this file
├── results.md           # benchmark table + methodology + caveats
├── prompt_template.py   # the exact θ₀ prompt (system + user builder)
├── verify_rebuttal.py   # callable skill: single case, batch, CLI, importable
├── .env.example         # config template (copy to .env)
└── examples/
    ├── example_case.json
    └── run_example.sh
```

## Install & configure
```bash
pip install openai                       # only dependency
cp .env.example .env                     # then edit: put your DEEPSEEK_API_KEY
```
`.env` keys: `DEEPSEEK_API_KEY` (required), `DEEPSEEK_BASE_URL`
(default `https://api.deepseek.com`), `DEEPSEEK_MODEL` (default `deepseek-v4-pro`).
Env vars override `.env`.

## How to call

**CLI — single case**
```bash
python verify_rebuttal.py --case examples/example_case.json
# or inline:
python verify_rebuttal.py --review "Weaknesses: no baselines..." \
                          --rebuttal "We added 3 baselines in Table 4..." \
                          --initial-rating 5
```

**CLI — batch** (JSONL in, JSONL out; one case per line)
```bash
python verify_rebuttal.py --batch cases.jsonl --out preds.jsonl --workers 8
```

**Python — importable**
```python
from verify_rebuttal import verify_one, verify_batch

verify_one({
    "review": "## Weaknesses\n- no baselines...",
    "rebuttal": "We added 3 baselines in Table 4...",
    "initial_rating": 5, "confidence": 4,          # optional persona fields
})
# -> {"reaction": "raise", "reasoning": "...", "quality": "high"}

verify_batch(list_of_cases, workers=8)             # -> list of dicts
```

Quick end-to-end check: `bash examples/run_example.sh`.

## Input / output schema

**Input case** (dict / JSON). Required: `review`, `rebuttal`. Optional persona
(improves accuracy): `reviewer_profile` (free text) **or** the structured fields
`initial_rating` (1–10), `confidence` (1–5), `soundness`/`presentation`/`contribution`
(1–4); also optional `title`, and any pass-through id (`note_id`, `paper_id`).

**Output** (dict): `reaction` ∈ {raise, same, lower}, `quality` ∈
{high, neutral, counterproductive}, `reasoning` (reviewer-style rationale string).
Batch mode passes through `note_id`/`paper_id` if present.

## The prompt (θ₀)
Lives in [`prompt_template.py`](prompt_template.py) as `SYSTEM_INSTRUCTION` +
`build_messages(case)`. It (1) sets the reviewer persona from the structured
fields, (2) gives review + rebuttal, (3) asks for step-by-step reviewer reasoning
then a JSON `{"reasoning","reaction"}`. It is the **un-optimized zero-shot** prompt
— we verified DSPy MIPROv2 prompt optimization did NOT generalize better (see
results.md), so nothing is fine-tuned; the skill is fully reproducible.

## Serving it to others WITHOUT sharing the DeepSeek key

Distributing the raw `DEEPSEEK_API_KEY` is insecure (leaks, unbounded spend, no
per-user revocation). Instead run the bundled HTTP service — the key stays
server-side; callers use a lightweight, independently revocable **service token**.

```bash
cd rebuttal_verifier
pip install fastapi uvicorn
# server-side secrets (reuses .env): DEEPSEEK_API_KEY required;
# SERVICE_TOKENS=alice-tok,bob-tok  -> callers must present one (omit = open)
SERVICE_TOKENS=alice-tok uvicorn serve:app --host 0.0.0.0 --port 8000
```
Call it (model = `deepseek-v4-pro`, held server-side):
```bash
curl -s http://HOST:8000/verify -H "Authorization: Bearer alice-tok" \
  -H "Content-Type: application/json" \
  -d '{"venue":"emnlp","initial_overall":3,"confidence":4,"soundness":3,
       "review":"## summary_of_weaknesses ...","rebuttal":"We added ..."}'
# -> {"reaction":"raise","quality":"high","reasoning":"..."}
```
`venue`: `"iclr"` (this prompt) or `"emnlp"` (see README_emnlp.md; requires
`initial_overall`). `GET /health` reports the model and whether auth is on.
Teammates never see the DeepSeek key; rotate/revoke access by editing
`SERVICE_TOKENS` and restarting.

## ⚠️ Caveats (read before trusting outputs)
- **`lower` is unreliable.** Reviewers almost never lower a score after a rebuttal
  (~1% of real cases) and no model predicts it. Use this as a **raise-vs-not**
  detector; a `lower` output should be treated as `same`.
- **Persona matters.** Passing `initial_rating` + sub-scores meaningfully helps.
  With no persona the model falls back to a generic reviewer and is weaker.
- **No leakage by construction** — the case never contains the final rating/label.
  Keep it that way when you build new cases.
- Accuracy figures are from small ICLR-2025 eval sets (36 / 57). Expect ~±0.05.

---

## Handoff — how the next agent should take over

Everything needed is in this folder; it does **not** depend on the parent repo.

**To run / integrate as-is:** call `verify_one` / `verify_batch` (above). For a
pipeline, feed it `{review, rebuttal, initial_rating, ...}` per reviewer thread and
gate on `quality == "high"` (i.e. predicted `raise`) to flag "rebuttals likely to
win a score increase."

**To swap the backbone model:** change `DEEPSEEK_MODEL` in `.env`, or for another
provider edit `_client_and_model()` in `verify_rebuttal.py` (it's a thin
OpenAI-compatible client). Re-benchmark with the harness described below before
trusting a new model — do NOT assume a bigger model is better (GPT-5.5 and Opus
lost to DeepSeek V4 Pro here).

**To improve accuracy, in priority order:**
1. **More & balanced data.** The eval sets are tiny. Rebuild from ICLR
   (ProReviewer initial rating ⋈ OpenReview final rating, join on note id) and grow
   train/val/test. This helps more than any prompt tweak.
2. **Edit the θ₀ prompt** in `prompt_template.py` (it's the single source of truth).
3. Only then try automated prompt optimization — but hold out a real test set;
   MIPROv2 overfit our 51-example val and lost on test.

**How to re-benchmark fairly (critical):** score every model **per-example,
isolated** (one call per case, temperature 0) — never batch all cases into one
context, which contaminates via the visible class distribution. Compute **macro-F1
over classes present in the gold**. This is exactly how the `results.md` table was
produced.

**Known open problems to pick up:** (a) the `lower` class — needs either far more
data or a reframing to binary; (b) validate on a second venue/year to test
generalization; (c) calibrate a decision threshold if you need precision/recall
trade-offs on the `raise` class.
