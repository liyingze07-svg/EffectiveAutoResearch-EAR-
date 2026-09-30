# AutoRebuttal — EAR's Rebuttal Drafting Pipeline

Given a paper and its reviews, draft responses for selected reviewers and a comment to the Area Chair.
Built for **EMNLP / ACL Rolling Review (ARR)**, with evidence tracing, model-based review, and
faithfulness checks. These checks can miss errors: authors must verify every claim, number, citation,
and venue-specific submission requirement before using the drafts.

Part of [EAR — Effective Auto Research](../README.md). Use a complete EAR checkout; shared setup
and safety tools live in the repository root.

## Inputs and outputs

Inputs are a LaTeX paper, review text, and a campaign card identifying reviewer scores, target reviewers,
and run limits. Expected deliverables are `campaigns/<case>/drafts/<reviewer>.md` and
`campaigns/<case>/AC_COMMENT.md`, with status and evidence records under `campaigns/<case>/ledger/`.
The first live-run example below is writing-only: it uses existing evidence and does not launch new experiments.

## Install and run

### Try it without credentials

From a fresh checkout (skip cloning if you already have EAR):

```bash
git clone https://github.com/liyingze07-svg/EffectiveAutoResearch-EAR-.git EAR
cd EAR
python3 scripts/doctor.py --offline
python3 scripts/offline_demo.py
```

The demo supplies a clearly synthetic paper, two reviews and a campaign card; it renders all five
contracts and runs the real orchestrator in `--dry-run` mode. Expected:
`PASS: idea validation/report, five contracts, and synthetic rebuttal dry-run.`
The printed temporary directory contains `rebuttal/DRY_RUN.txt`. No model is called, no response is
generated, and no rebuttal quality is measured.

### Requirements

- Linux / WSL2, Bash, and Python 3.10+.
- An authenticated Codex CLI for writing and review; the installation command below assumes Node.js and npm.
- Two distinct Codex model IDs available to your account, chosen explicitly for writing and judging.
- A DeepSeek API key for the second provider, required for cross-family consensus.
- Python dependencies from `requirements.txt`; install these in a virtual environment.

### Configure

Continue from the EAR repository root:

```bash
npm install -g @openai/codex
codex login                          # Skip if already authenticated
cd rebuttal
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
cp -n rebuttal_verifier/.env.example rebuttal_verifier/.env
```

Edit `rebuttal_verifier/.env` to set `DEEPSEEK_API_KEY` and check the configured model/endpoint.
The copy command preserves an existing file. Do not commit this file or put credentials in a campaign card.
Then, from `rebuttal/`:

```bash
python3 ../scripts/doctor.py --component rebuttal
```

The doctor checks local availability only; it does not authenticate or contact model services.
`AUTOREBUTTAL_ROOT` is normally inferred from the checkout; override it only when intentionally using
a different root. Optional dependencies are separate: `requirements-server.txt` for the HTTP verifier
service and `requirements-research.txt` for research/data utilities. Neither is needed by the main harness.

### Adding a paper

All remaining setup and run commands assume you are in `rebuttal/`. Choose a new case name;
the examples use `my-paper`. Create its directories and copy a starting card:

```bash
mkdir -p papers/my-paper/Tex campaigns/my-paper
cp -n examples/offline-demo/REBUTTAL_CARD.json campaigns/my-paper/REBUTTAL_CARD.json
```

Populate the inputs before continuing:

```text
papers/my-paper/
  review.md                 Full review text, preserving reviewer IDs and scores
  Tex/main.tex              Paper source, with any included section files alongside it
campaigns/my-paper/
  REBUTTAL_CARD.json         Your case metadata and run settings
```

The copied card is **synthetic template data**, not a prepared case. Replace its title, claims,
concern seeds, reviewer IDs/scores, target lists, and word limit with your own verified values.
Use [the card conventions](harness/templates/REBUTTAL_CARD.schema.json) as a reference.
Keep `allow_new_experiments: false` for this first writing-only run and `max_iter: 1` for a short
reviewer loop. The live command below also sets the iteration limit explicitly.

Review blocks must use `Official Review of Submission<number> by Reviewer <id>`, matching the
IDs in the card. See [the synthetic review](examples/offline-demo/review.md) for the format.
List the reviewers you want to address in `target.require_raise_on` or `target.maintain`;
do not copy the example's targets or scores unchanged.

### Render the campaign contracts

```bash
python3 harness/instantiate.py --slug my-paper
```

This creates `CLAUDE.md`, `GOAL.md`, `SPEC.md`, `VERIFY.md`, and `RESOURCE.md` under the campaign.
They record the case instructions, goal, constraints, checks, and resources. The legacy filename
`CLAUDE.md` does not mean that the shell pipeline requires Claude.
Existing contracts and their version stamp are preserved; use `--force` only when intentionally
regenerating them, for example after reviewing a change to the card. Drafts and ledgers are preserved.

### Inspect a dry-run

```bash
python3 harness/runner/orchestrate.py --paper my-paper --from r1 --dry-run
```

This prints the planned stages without model calls or changes to campaign artifacts. It is a wiring inspection,
not a comprehensive input validator or a model-access check. We start at `r1` because the card has
already been prepared and reviewed; the default `r0a` entry point is for model-assisted card extraction.

### Run with explicit writer and judge models

Read the [data-handling notice](#data-handling) first. Replace **both** model placeholders below with
distinct model IDs available through your Codex account. Availability depends on the account; the
repository's built-in judge default is not a guarantee of access.

```bash
EAR_WRITER_MODEL="REPLACE_WITH_AVAILABLE_WRITER_MODEL"
EAR_JUDGE_MODEL="REPLACE_WITH_AVAILABLE_JUDGE_MODEL"
python3 harness/runner/orchestrate.py --paper my-paper --from r1 \
    --model "$EAR_WRITER_MODEL" --judge-model "$EAR_JUDGE_MODEL" \
    --max-iter 1 --mt-rounds 1
```

The two Codex models separate writing from judging; DeepSeek provides the second provider for
cross-family consensus. These limits cap reviewer-loop and multi-turn rounds, **not** total tokens,
elapsed time, or spending. A live run can still make many paid or quota-consuming calls.

### Inspect the results before submission

| Path under `campaigns/my-paper/` | What to inspect |
|---|---|
| `drafts/<reviewer>.md` | Final draft for each targeted reviewer; verify all factual claims |
| `AC_COMMENT.md` | Area Chair comment, if the packaging stage completed |
| `ledger/loop_results.json` | Per-reviewer outcomes, including unresolved or conceded concerns |
| `ledger/package.json` | Delivery index and remaining open items, if packaging completed |
| `ledger/evidence_map.json` | Links between paper claims and supporting evidence |

Check that every targeted reviewer has a draft and inspect the gate/evidence records in `ledger/`.
A completed process or a draft file does not establish that every gate passed.
`HONEST_CONCEDE` means concerns remain; `PASS_SINGLE_FAMILY` / `cross_family=false` is not
cross-family approval. Even a passing model verdict does not guarantee accuracy or acceptance.
Review and submit the text yourself; the pipeline does not submit it to the conference.

### Other run options

| Flag | Effect |
|---|---|
| `--from r6r7` | Resume at the reviewer loop when the necessary upstream artifacts already exist |
| `--max-iter N` | Cap reviewer-loop rounds; not a total cost limit |
| `--mt-rounds N` | Limit rounds of multi-turn exchange |
| `--fanout-all` | Write every strategy each round instead of stopping at the first that passes |
| `--no-deepseek` | Explicit single-family mode; outputs no longer establish cross-family consensus |
| `--allow-network` | Allow generated shell commands to use the network and enable live search; model/API traffic is separate |
| `--unsafe` | Explicitly allow unrestricted experiment stages; externally isolated environments only |

The default CLI stages use their declared read-only/workspace-write sandbox, no approval prompts,
and no shell networking. This does not disable direct DeepSeek API calls or Codex model traffic.
New experiments are optional and require a separate execution setup; stages requesting unrestricted
host access are blocked unless `--unsafe` was explicitly provided. Do not enable it merely to make a
first run proceed. The writing-only example keeps `allow_new_experiments` false.

### Data handling

Papers, reviews, drafts and relevant tool results can be sent to Codex/OpenAI and DeepSeek, or to
explicitly configured provider endpoints. Use only material you are authorized to send. Campaigns,
receipts, logs and CLI session history may retain that material locally; never publish raw logs or
private reviews without inspecting them. Provider-side retention depends on the provider/account.
See [EAR's full notice](../README.md#execution-safety-and-data-handling).

## Two components

| | What it is |
|---|---|
| **`harness/`** | The pipeline. 18 stage prompts, an experiment loop and a reviewer loop, a fixed strategy ladder, and four gates. Currently `v0.8` |
| **`rebuttal_verifier/`** | Model-based review prompts plus a cross-family consensus gate. **Developed for EMNLP/ARR**: a general template and a dedicated diagnoser for borderline (OA=3) reviewers. An earlier ICLR template ships as a predecessor but is not used by the pipeline |

---

## Pipeline

The diagram shows the full workflow, including the optional experiment loop. In the writing-only
quick start, the prepared card replaces `r0a`, and `allow_new_experiments: false` skips new experiments.
Gates are automated judgments, not guarantees of factual correctness or reviewer agreement.

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

## Using the judge on its own

From `rebuttal/`, with the same virtual environment and DeepSeek configuration:

```bash
cd rebuttal_verifier
python3 verify_rebuttal.py --case /path/to/your/case.json --template auto
```

This command's `case.json` is a verifier input, **not** the campaign's `REBUTTAL_CARD.json`.
It includes the review, a candidate rebuttal, and reviewer context. For EMNLP, supply
`initial_overall` (the pre-rebuttal overall score out of 5). See the
[input format and evaluation context](rebuttal_verifier/README_emnlp.md) for an example and limitations.

---

## Layout

```
harness/
  HARNESS.md                 pipeline overview
  GOAL.md LOOP.md EXPERIMENT_LOOP.md   stopping criterion and the two loops
  stages/*.md                18 materialized stage prompts (engine-agnostic)
  strategies/                writing strategies: shared CRAFT.md, s1/s2/s3, fixed ladder
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
examples/offline-demo/             complete synthetic inputs for the root offline demo
```

---

## Known limits

- Faithfulness and evidence checks are fallible model judgments. Human verification remains necessary; no output is guaranteed free of fabricated or unsupported content.
- For **borderline (OA=3)** reviewers the judge assesses rebuttal quality and raise potential. It does **not** predict the final score change.
- ICLR calibration is not evidence of EMNLP performance; each venue needs its own template and evaluation.
- Cross-family consensus requires two models from different vendors. With only one available the pipeline degrades and marks its output `cross_family=false`; such output is not a valid acquittal.
- Strategy selection follows a fixed ladder (stop at the first draft that clears the gate). It does not route by paper or concern type.
- `demo-argument-compiler` is a **rendered contract set**, not a runnable demo. The new `offline-demo`
  contains complete synthetic inputs for installation/dry-run checks, but no paid-model evaluation.

---

## License

MIT. Copyright (c) 2026 Yingze Li, Dong Wang, Ben Wu. See [LICENSE](../LICENSE).
