# AutoRebuttal

**A pipeline that writes conference rebuttals.** Give it a paper and its reviews; it produces one response per reviewer plus a comment to the Area Chair.

Built for **EMNLP / ACL Rolling Review (ARR)**. It never invents numbers or citations. Experiments run on a separate engine and must pass an independent acceptance audit before any result can be cited.

---

## Two components

| | What it is |
|---|---|
| **`harness/`** | The pipeline. 18 materialized stages, two nested goal loops, an MoE strategy ladder, four gates. Currently `v0.8` |
| **`rebuttal_verifier/`** | A self-developed prompt judge plus a cross-family consensus gate. **Developed for EMNLP/ARR**: a general template and a dedicated diagnoser for borderline (OA=3) reviewers. An earlier ICLR template ships as a predecessor but is not used by the pipeline |

---

## Pipeline

```
r0a extract card → r1 evidence map → r2 diagnose → B1 concern gate → r3 triage
                                                        │
     ┌──────────────────────────────────────────────────┘
     ├─ Experiment loop: S-ante gate → r4 run → code audit → S-exp persuasion gate
     │                   not persuasive → redesign and rerun, or concede honestly
     ↓
  r5 evidence merge (accepted experiments only)
     ↓
     ├─ Reviewer loop: write along the strategy ladder → r7 consensus gate
     │                 → B2 faithfulness gate → B3 ammunition gate
     │                 blocked → judge feedback drives a rewrite;
     │                 iterations exhausted → honest concession
     ↓
  mt multi-turn exchange (pre-delivery stress test) → ac package
```

### The four gates

| Gate | What it decides |
|---|---|
| **B1** concern | Whether the diagnosis caught what the reviewer is actually worried about |
| **r7** consensus | Whether the response is persuasive enough for this reviewer's zone — judged by two models from different vendors |
| **B2** faithfulness | Whether every number and citation is traceable, and whether any unaccepted experiment is being presented as evidence |
| **B3** ammunition | Whether the draft harms itself: self-exposure, empty promises, over-claiming. Judged semantically, not by regex |

### Zone-dependent stopping criterion

The bar depends on the reviewer's pre-rebuttal score:

| Zone | Bar |
|---|---|
| OA ≤ 2 | The response should move the reviewer up |
| **OA = 3** (borderline) | Judged on **rebuttal quality and raise potential**, not on predicted outcome |
| OA ≥ 4 | The response should hold the score, not raise it |

---

## Install and run

**Requirements**

- Python 3.10+, `pip install openai`
- [Codex CLI](https://github.com/openai/codex) — the writer engine and the authoritative judge
- A DeepSeek API key — the second judge family, required for cross-family consensus

**Configure**

```bash
cp rebuttal_verifier/.env.example rebuttal_verifier/.env   # set DEEPSEEK_API_KEY
export AUTOREBUTTAL_ROOT=$(pwd)                            # optional; inferred from repo layout
```

**Run**

```bash
# Inspect the wiring first — no side effects
python3 harness/runner/orchestrate.py --paper <case> --dry-run

# Real run. The writer and the judge must be different models.
python3 harness/runner/orchestrate.py --paper <case> \
        --model gpt-5.5 --judge-model gpt-5.6-sol
```

Useful flags:

| Flag | Effect |
|---|---|
| `--from r6r7` | Start from a given stage |
| `--max-iter N` | Cap on reviewer-loop rounds |
| `--mt-rounds N` | Rounds of multi-turn exchange |
| `--fanout-all` | Write every strategy each round instead of stopping at the first that passes |
| `--no-deepseek` | Single-family fallback. Cross-family consensus no longer holds; outputs are marked accordingly |

**Using the judge on its own**

```bash
cd rebuttal_verifier
python3 verify_rebuttal.py --case case.json --template auto
```

The input must carry a persona. For EMNLP, `initial_overall` (out of 5) is required — without it the model performs at chance.

---

## Layout

```
harness/
  HARNESS.md                 pipeline overview
  GOAL.md LOOP.md EXPERIMENT_LOOP.md   stopping criterion and the two loops
  stages/*.md                18 materialized stage prompts (engine-agnostic)
  strategies/                MoE strategies: shared CRAFT.md, s1/s2/s3, routing ladder
  shared-assets/             ammunition checklist, experiment ladder, strategy notes
  templates/                 contract templates and the REBUTTAL_CARD schema
  runner/orchestrate.py      thin driver
  runner/cost.py             per-call cost ledger

rebuttal_verifier/
  prompt_template_emnlp.py       EMNLP general
  prompt_template_emnlp_oa3.py   OA=3 borderline diagnoser
  prompt_template.py             ICLR predecessor
  consensus_gate.py              cross-family consensus gate
  verify_rebuttal.py             single/batch verify CLI
  serve.py                       HTTP service

scripts/
  cost_report.py        cost profile from the ledger
  cascade_replay.py     offline replay of judge cascades
  test_orchestrate.py   pure-function unit tests
  secret_scan.sh        pre-commit credential scan

examples/demo-argument-compiler/   rendered contract set for a synthetic case
                                   (card, GOAL, SPEC, VERIFY, RESOURCE).
                                   Illustrative only — the review files it
                                   points at are not included, so it is not
                                   a runnable demo.
```

---

## Adding a paper

1. Write `campaigns/<case>/REBUTTAL_CARD.json` (schema in `harness/templates/`)
2. Put the paper and the reviews under `papers/<case>/`
3. Check the wiring with `--dry-run`, then run for real

Switching papers means writing a new card. The harness itself does not change.

---

## Known limits

- For **borderline (OA=3)** reviewers the judge assesses rebuttal quality and raise potential. It does **not** predict the final score change.
- Criteria tuned on ICLR **do not transfer** to EMNLP; each venue needs its own template.
- Cross-family consensus requires two models from different vendors. With only one available the pipeline degrades and marks its output `cross_family=false`; such output is not a valid acquittal.
- Strategy selection follows a fixed ladder (stop at the first draft that clears the gate). It does not route by paper or concern type.
- The bundled example is a **rendered contract set**, not a runnable demo: it shows what a campaign's
  contracts look like, but ships no reviews, evidence or drafts.

---

## License

MIT. Copyright (c) 2026 Yingze Li, Dong Wang, Ben Wu. See [LICENSE](../LICENSE).
