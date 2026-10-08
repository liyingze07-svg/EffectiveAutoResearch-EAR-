# Getting started

EAR runs from a complete source checkout. The shared command is `python3 -m ear`; no package-index install is required. Run the commands below from the repository root unless stated otherwise.

## Start with an observable result

For an interactive introduction, run `python3 -m ear demo studio` from a complete
checkout. The bilingual local browser demo uses no model account or extra
dependencies. See [Research Studio](demo-studio.md) for offline execution,
downloads, portable export and a walkthrough.

```bash
git clone https://github.com/liyingze07-svg/EffectiveAutoResearch-EAR-.git EAR
cd EAR
python3 -m ear doctor --offline
python3 -m ear demo report
python3 -m ear demo check
```

These commands require Python 3.10+ and its standard library. `doctor` checks local prerequisites. The report demo recomputes published aggregate metrics; the workflow check generates inspectable temporary artifacts. Neither needs model credentials or network access.

Keep the workflow-check artifacts by supplying a new output directory:

```bash
python3 -m ear demo check --output workspaces/first-check
```

The output path must not already exist. Inspect `SUMMARY.json` and the rebuttal `DRY_RUN.txt`. See [all demonstrations](../examples/README.md) for data provenance and what each run establishes.

## Choose a live workflow

| Workflow | Environment | Inputs to prepare |
| --- | --- | --- |
| AutoVibeIdea | Linux/WSL2, Bash, authenticated Codex CLI; background mode also needs Linux process-control support | A research direction and screening configuration; see the original workflow options |
| AutonomousMath | Authenticated Codex or Claude CLI, `pdflatex`, `bibtex`, `pdfinfo`, `pdftotext`; terminal reviewer prerequisites depend on the backend | A research question and a new workspace |
| AutoRebuttal | Linux/WSL2, Bash, authenticated Codex CLI, Python dependencies and DeepSeek for cross-family mode | Paper source, reviews and an edited task card |

Live calls use your configured accounts and send relevant research inputs to those services. Iteration limits are not dollar, token or elapsed-time caps. See [operation and data-handling details](operations.md).

The local doctor checks executable and dependency availability; it does not test login validity, model access or endpoints. CLI setup and workflow-specific options remain documented in [AutoVibeIdea](../autovibeidea/README.md), [AutonomousMath](../autonomousmath/README.md) and [AutoRebuttal](../rebuttal/README.md#install-and-run).

## Develop a research direction

After configuring an authenticated Codex CLI:

```bash
python3 -m ear doctor --component autovibeidea
python3 -m ear idea --workspace workspaces/idea-01 \
  --allow-network --codex-cli "your research direction" NeurIPS
```

`--allow-network` enables shell networking and live web search. `--codex-cli` requests review in separate Codex sessions. Separate sessions do not imply different model families or expert validation. Add `--daemon` before the direction for background execution; the native launcher also supports `--survey`, `--gen`, `--screen` and `--refine`.

The workspace contains its own source/templates and produces:

```text
workspaces/idea-01/
  outputs/LANDSCAPE.md
  outputs/SCREENING_RANKED.md
  refine-logs/FINAL_PROPOSAL.md
```

Without `--workspace`, the command uses the original `autovibeidea/` directory. With a workspace, only source/templates are initialized; login state and output history are not copied. Existing EAR-marked idea workspaces can be reused, while arbitrary existing directories are refused. Each idea workspace retains the source snapshot used at initialization.

## Pursue a mathematical question

Try the artifact and revision loop before using a live account:

```bash
python3 -m ear math run --offline --workspace workspaces/math-demo --episodes 1
python3 -m ear math status --workspace workspaces/math-demo
```

For a live run, use a separate workspace:

```bash
python3 -m ear math doctor --backend codex
python3 -m ear math run --backend codex \
  --direction "your mathematical research question" \
  --workspace workspaces/math-01 --episodes 1
```

Use `--backend claude` for a Claude coordinator; its default terminal-review route also needs Codex. The existing math CLI options pass through unchanged. Codex mode defaults to two fresh Codex terminal-review sessions; `--review-backends codex,claude` chooses the dual-family route. See the [math guide](../autonomousmath/README.md) for configuration.

Inspect `state.json`, `events.jsonl`, `tasks/episode-*/` and `reviews/episode-*/`. Terminal review refers to a specific artifact version. For the optional optimizer and local dashboard, use the documented [evolution commands](../autonomousmath/docs/EVOLUTION.md); opening its dashboard does not start research calls.

## Prepare a rebuttal case

Initialize a new workspace from the synthetic fixture:

```bash
python3 -m ear rebuttal init --from-example \
  --workspace workspaces/rebuttal-01 --paper my-paper
python3 -m ear rebuttal run --workspace workspaces/rebuttal-01 \
  --paper my-paper --from r1 --dry-run
```

Initialization copies the harness and templates, creates five contracts and makes no model calls. The dry-run prints planned stages. It does not validate the scientific content or generate reviewer replies.

Replace all synthetic content before a live task:

```text
workspaces/rebuttal-01/
  papers/my-paper/review.md
  papers/my-paper/Tex/main.tex          # and referenced manuscript sources
  campaigns/my-paper/REBUTTAL_CARD.json
```

Match reviewer IDs and scores between the reviews and task card. The card declares response targets, evidence, constraints and whether new experiments are allowed. See the [card schema](../rebuttal/harness/templates/REBUTTAL_CARD.schema.json). Regenerate the existing contracts after editing the card:

```bash
python3 workspaces/rebuttal-01/harness/instantiate.py \
  --harness workspaces/rebuttal-01/harness \
  --campaigns workspaces/rebuttal-01/campaigns --slug my-paper --force
```

Set up a virtual environment and the main workflow dependencies if you have not already done so:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r rebuttal/requirements.txt
```

Configure DeepSeek through `DEEPSEEK_API_KEY` in your environment, or the initialized workspace's `rebuttal_verifier/.env` using its `.env.example`. Credentials are not copied from the source checkout. The root doctor checks the source-checkout configuration; it does not discover credentials in an arbitrary rebuttal workspace.

Select two distinct model IDs available to your Codex account, then start a bounded first writing run:

```bash
EAR_WRITER_MODEL="REPLACE_WITH_AVAILABLE_WRITER_MODEL"
EAR_JUDGE_MODEL="REPLACE_WITH_AVAILABLE_JUDGE_MODEL"
python3 -m ear rebuttal run --workspace workspaces/rebuttal-01 \
  --paper my-paper --from r1 \
  --model "$EAR_WRITER_MODEL" --judge-model "$EAR_JUDGE_MODEL" \
  --max-iter 1 --mt-rounds 1
```

Keep `allow_new_experiments: false` in the card for the first writing-only case. `--no-deepseek` explicitly selects single-family review and is recorded as such. See the [full rebuttal guide](../rebuttal/README.md) for model configuration and optional experiments.

Reviewer responses appear under `campaigns/my-paper/drafts/`; the final packaging stage writes `AC_COMMENT.md` and delivery records in `ledger/`. No response is submitted externally.

## Workspaces and run control

Use ignored `workspaces/` or a directory outside the checkout. A workspace is the unit of work; it is not a container or an automatic confidentiality boundary.

```bash
python3 -m ear status workspaces/idea-01 --workflow idea
python3 -m ear status workspaces/math-01 --workflow math
python3 -m ear status workspaces/rebuttal-01 --workflow rebuttal

python3 -m ear stop workspaces/idea-01 --workflow idea
python3 -m ear stop workspaces/math-01 --workflow math
```

Idea status/stop manages the native background launcher. Math stop requests a soft stop, and an explicit later run resumes saved work. Rebuttal status summarizes artifacts; it does not establish process liveness. Rebuttal runs in the foreground and has no shared managed-stop command; interrupt the foreground process when necessary.

To invoke EAR from outside its source directory, use the included shell entry point:

```bash
/path/to/EAR/ear.sh demo report
/path/to/EAR/ear.sh math status --workspace /path/to/math-workspace
```

Replace `/path/to/EAR` with your checkout path. Relative workspace paths are resolved from your current directory. No shell alias, system install or relocation of the source is required.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `No module named ear` | Run from the complete checkout, or use its absolute `ear.sh` path. |
| Offline output directory already exists | Choose a new path; the demo preserves existing contents. |
| Idea background launch fails | Run the idea doctor and inspect Linux/WSL2 process-control support. |
| Local doctor passes but live calls fail | Check account authentication, model availability and service quotas. The doctor does not call providers. |
| Math run cannot compile a manuscript | Install the documented LaTeX/PDF tools and rerun the math doctor. |
| Rebuttal sees the wrong inputs | Check the selected workspace, paper slug, reviewer IDs and regenerated contracts. |
| Review says single-family or degraded | Inspect the route markers and service failures before interpreting the score. |

For reproducible problems, follow [Contributing](../CONTRIBUTING.md).
