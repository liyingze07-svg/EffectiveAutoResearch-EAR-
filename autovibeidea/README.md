# AutoVibeIdea — EAR's Research Idea Pipeline

Turn a research direction into a structured proposal draft through literature retrieval, critical analysis,
candidate screening, and iterative refinement. Outputs are in English and are intended for researchers
to verify and develop, not as submission-ready work or a substitute for experiments.

Part of [EAR — Effective Auto Research](../README.md). Use a complete EAR checkout; shared setup
and safety tools live in the repository root.

## Inputs and outputs

Provide a direction such as `sample-efficiency bottlenecks in offline RL with image observations`
and a target venue such as `NeurIPS`. The workflow aims to produce a literature map, ranked ideas,
and `refine-logs/FINAL_PROPOSAL.md`. See [sanitized run excerpts](examples/judge-run/README.md)
for the form of intermediate outputs, and [Output Files](#output-files) for the full list.

Scores are model judgments, not peer-review outcomes. Verify references, novelty claims, and feasibility
before investing in a proposal; see [Known Limitations](#known-limitations).

## Prerequisites

- **Offline demo:** Python 3.10+ only; no model account or third-party Python packages.
- **Live pipeline:** Linux / WSL2, Bash, Python 3.10+, and an authenticated Codex CLI.
  The installation command below assumes Node.js and npm are already available.
- **Background control:** `flock` (util-linux), `nohup`, and Linux pidfd support (Linux 5.3+).
  The local doctor checks these and the other launcher utilities.

Python tools use the standard library. Every `run.sh` execution mode uses Codex as the driver,
including `--gpt-only`; a separate OpenAI API key is needed only for the optional API review route.
Zotero and Obsidian MCP integrations are optional. Without them, retrieval can use public web sources
when network access is enabled.

## Quick Start

### Try the offline demo

From a fresh checkout (skip cloning if you already have EAR):

```bash
git clone https://github.com/liyingze07-svg/EffectiveAutoResearch-EAR-.git EAR
cd EAR
python3 scripts/doctor.py --offline
python3 scripts/offline_demo.py
```

Expected: `PASS: idea validation/report, five contracts, and synthetic rebuttal dry-run.`
The printed temporary directory contains an idea search report and synthetic rebuttal artifacts.
This checks installation and wiring only; it neither generates new research nor evaluates its quality.

### Run with separate-session review

Continue from the EAR repository root. Live calls use account quota and may incur charges.
Read the [data-handling notice](../README.md#execution-safety-and-data-handling) before supplying inputs.

```bash
npm install -g @openai/codex
codex login                                      # Skip if already authenticated
python3 scripts/doctor.py --component autovibeidea
cd autovibeidea
./run.sh --allow-network --codex-cli --daemon "your research direction" NeurIPS
./run.sh --status
```

`--allow-network` enables fresh retrieval and nested model calls; it does not disable the sandbox.
`--codex-cli` requests additional review in separate Codex sessions using the local login, without
a separate API key. Those sessions may use the same model as the generator and are not cross-family
validation. The doctor checks local prerequisites, not authentication or model availability.

### Monitor, stop, or start another run

From `autovibeidea/`, use `tail -f outputs/pipeline.log` to follow progress (`Ctrl-C` stops only
the log viewer), and `./run.sh --stop` to cancel the background task.

Background runs keep `DONE` only for a successful executor exit and `FAILED` with the exit code
otherwise. `--status` returns nonzero for a recorded failure. A workspace lock rejects overlapping
background launches; use separate checkouts for parallel runs. A successful exit is not a quality verdict.
The stop command verifies the saved process identity, terminates
the task and its descendants (including detached children), and escalates to SIGKILL after two seconds
if needed. Status and the workspace lock are finalized only after cleanup. SIGTERM to the launcher
PID follows the same cleanup path; SIGKILL cannot run cleanup and should not be used on the supervisor.
`batch.sh` now delegates to `batch_codex.sh`; provide directions with `--task-file` instead of editing
the old launcher's embedded task array. A batch continues to archive each task, but exits nonzero
if any task failed; only an entirely successful batch returns zero.

Before a new direction, finish or stop the current run and archive its results as described under
[Output Files](#output-files).

### Review routes and fallback

| Route | Additional review behavior |
|---|---|
| `--codex-cli` (recommended) | Separate Codex sessions through `tools/codex_call.sh`; may use the same model/provider |
| `--gpt-only` | Text-only OpenAI API calls through `tools/gpt_call.sh`; requires `OPENAI_API_KEY` or `~/.openai_key`; the driver still uses Codex |
| No explicit route | The shell compatibility workflow may perform evaluation in the generating session |
| Host-provided MCP | Depends on the agent and integrations; not required by the shell launchers |

Choose only one of `--codex-cli` and `--gpt-only`. For the API route, after configuring your key:

```bash
# From autovibeidea/; do not overlap this with an existing run.
./run.sh --allow-network --gpt-only "your research direction" NeurIPS
```

When external review is unavailable, skills can fall back to self-evaluation and relax scoring thresholds.
Inspect `outputs/PIPELINE_LOG.md`, review artifacts, and `scores.degraded` where recorded; such scores
are not equivalent to separate-session review. Model routing is instructed through the skills, not
a guarantee that every requested review call succeeded. See [CODEX_COMPAT.md](CODEX_COMPAT.md).

## Pipeline

This is the intended skill workflow. Retrieval coverage, model availability, and instruction following
can affect which artifacts are produced; consult the run logs for missing or degraded stages.

```
(Optional) /idea-filter — lock a direction when it has not yet been chosen
    │
    ▼
Phase 1: Literature survey (/lit-survey)
    Four source tiers: Zotero MCP → Obsidian MCP → local PDFs → WebSearch/arXiv
    → outputs/LANDSCAPE.md + LANDSCAPE.json (including Gap Identification Matrix)
    │
    ▼
Phase 2: Two-stage idea generation (/idea-gen)
    2a: External model critiques four structural weaknesses of the landscape
        → outputs/CRITICAL_ANALYSIS.md
    2b: Every idea must anchor a CRITIQUE-ID and provide a Theorem/Conjecture Scaffold
    Filters: feasibility → novelty → impact → Researcher-Fit Filter → anti-pattern checks
    → outputs/IDEAS_RAW.md + IDEAS_FILTERED.md (4-6 ideas)
    │
    ▼
Phase 3: Multidimensional screening (/idea-screen)
    Module A: novelty  Module B: reviewer simulation  Module C: strategic assessment
    Composite = 0.25×Novelty + 0.35×Venue + 0.20×Strategic + 0.20×Feasibility
    → outputs/SCREENING_REPORT.md + SCREENING_RANKED.md
    │
    ▼
(Optional) /idea-search — allocate expansion budget:
    prior pruning → UCT selection → generate mechanistically distinct children
    │
    ▼
Phase 4: In-depth refinement (/idea-refine)
    Freeze Problem Anchor → extract Skeleton → Theoretical Grounding
    → Theory-Experiment Alignment Matrix → review loop (≤3 rounds or Socratic dialogue)
    → Deep Expansion Pass (complete formulas/pseudocode/interface dimensions/hyperparameter ranges)
    → refine-logs/FINAL_PROPOSAL.md
    │
    ▼
Phase 5: Summary report → outputs/IDEA_DISCOVERY_REPORT.md
```

---

## Output Files

```
outputs/                            ← Empty means clean and ready for a new run
  LANDSCAPE.md / .json               Literature map + Gap Matrix
  ENTROPY_MAP.json                   High-entropy regions + failure modes (optional)
  IDEA_NODES.jsonl                   Structured ideas: pruning masks / lineage / cost
  COST_LOG.jsonl                     Token and wall-clock usage (--gpt-only / --codex-cli)
  SEARCH_STATE.json                  Search parameters: budget / alpha / UCT constant
  SEARCH_REPORT.md                   Search tree + reward provenance + pruning statistics
  CRITICAL_ANALYSIS.md               Landscape critiques (CRITIQUE-01...N)
  IDEAS_RAW.md / IDEAS_FILTERED.md    All generated / surviving ideas
  SCREENING_REPORT.md / _RANKED.md    Multidimensional scores and ranking
  IDEA_DISCOVERY_REPORT.md           Full-pipeline summary
  PIPELINE_LOG.md                    Autonomous decisions at each stage
  PIPELINE_STATE.json                Resumption checkpoint

refine-logs/
  skeleton.md                       State A → State B argument skeleton
  round-N-review.md / -refinement.md Per-round review and revision
  round-N-expanded.md               Deep Expansion output
  FINAL_PROPOSAL.md                 Final proposal
  REFINEMENT_REPORT.md / score-history.md
```

After a run has finished or been stopped, `./clean.sh --list` previews the files to archive.
`./clean.sh --name "MyRun_v1"` then moves current outputs into a timestamped directory under
`archive/`. Do not clean a running workspace.

---

## Capability Levels

These labels describe implementation, not demonstrated research quality. **Implemented** means the workflow is specified in skill prompts and/or supported by tools; model compliance is not guaranteed. **Experimental** marks mechanisms or heuristics still being refined without controlled outcome evaluation. **Roadmap** items are not implemented. An implemented workflow can still have unvalidated benefits.

### Implemented

| Capability | Entry point |
|---|---|
| Literature survey across four source tiers + Gap Identification Matrix with gap types and confidence | /lit-survey |
| Two-stage generation: critique the landscape along four dimensions, then anchor each idea to a `CRITIQUE-ID` | /idea-gen Phase 2a/2b |
| Layered filtering: feasibility → novelty → impact → Researcher-Fit Filter (12/20) → anti-pattern checks | /idea-gen Phase 3-5 |
| Novelty verification + venue review simulation (3 reviewers + meta review) + strategic fit, ranked by composite score | /idea-screen |
| Problem Anchor freezing and drift detection | /idea-refine Phase 0 |
| Skeleton (State A→B) and per-round skeleton gap checks | /idea-refine Phase 0.5 / 3.3 |
| Theory-Experiment Alignment Matrix: claim type → validation protocol → minimum scale → feasibility verdict | /idea-refine Phase 1.4.TE |
| Deep Expansion Pass: formulas, pseudocode, interface dimensions, and hyperparameter ranges | /idea-refine Phase 5.5 |
| Socratic dialogue mode, requiring a statement of understanding before scoring | /idea-refine -- mode: socratic-* |
| Three external-model paths: local Codex CLI without an API key / OpenAI API / Codex MCP, with automatic fallback | `--codex-cli` → `tools/codex_call.sh`; `--gpt-only` → `tools/gpt_call.sh` |
| Checkpoint resumption, unattended execution, and fallback when external models are unavailable | `PIPELINE_STATE.json` / each skill's fallback |

### Experimental

These capabilities are being refined; interfaces and defaults may change.

| Capability | Tool / entry point | Notes |
|---|---|---|
| `IDEA_NODES.jsonl`: auditable idea objects with generator, evidence anchors, falsifier, pruning mask, cost, and lineage | `tools/idea_nodes.py`; schema in `docs/IDEA_NODE_SCHEMA.md` | A unified candidate format supporting pruning statistics and lineage |
| Duplicate-candidate flagging through concept normalization, lexical/structural overlap, lineage exclusions, and boilerplate filtering | `tools/dedup_ideas.py` | Pairs require model adjudication; the threshold is empirical, so prioritize the `--top` ranking |
| High-entropy regions: stance entropy for a claim × **comparability penalty**, excluding spurious conflict from different settings | `tools/entropy_map.py` | Comparability weights can be adapted to the subfield |
| Failure-mode discovery through shared failure conditions across papers | Same tool | Conditions are clustered by text normalization; human review is recommended |
| Token-cost instrumentation | `tools/gpt_call.sh` → `outputs/COST_LOG.jsonl` | Covers `--gpt-only` and `--codex-cli`; Codex MCP does not return usage |
| Prompt-level diversity constraints: ≥50% of ideas anchor different critiques, at most 3 ideas per critique, and risk tiers | `idea-gen` Phase 2b | Applied during generation and checked with `dedup_ideas.py` |
| Researcher-Fit Filter threshold of 12/20 | `idea-gen` Phase 4 | Adjustable to researcher preferences |
| Benefits of the Deep Expansion Pass | `idea-refine` Phase 5.5 | Separates evaluating a direction from filling in implementation details |
| **UCT-guided candidate expansion + prior mask pruning**: Selection / Expansion / Backup, with **no random rollout**, replaced by value estimates | /idea-search, `tools/mcts_search.py`; design in `docs/SEARCH_DESIGN.md` | Standard UCT constant `c=1.414`, adjustable as needed |
| Reward mixes verifiable signals: retrieval / feasibility_rule / falsifiability / cost_efficiency / distinctness; default `alpha=0.5` | Same tool; report `--provenance` prints each source | Available components are averaged equally; alpha controls the LLM-score share |
| Trajectory Analysis | lit-survey -- trace: true | Disabled by default; enable with -- trace: true |

### Roadmap

**Not implemented.** These describe directions rather than current capabilities:

| Item | Current status |
|---|---|
| Full MCTS with random rollouts | Not planned: research ideas cannot be simulated randomly to terminal outcomes. The current design substitutes value estimates; see `docs/SEARCH_DESIGN.md` |
| Outcome-based reward signals | Current verifiable components describe proposal properties; pilot experiment outcomes are the next step |
| Scaling-regime discovery perspective | Absent. Phase 2a still has four dimensions; high-entropy discovery partly covers contradictions |
| A formal pilot-experiment pipeline stage | Absent. Pilots are currently run manually and are the only step accessing actual experimental outcomes |
| Innovation-pattern library with orthogonal gap × pattern axes | Only the critique-dimension axis exists, with 4 operators |
| Evolutionary trajectories as the main generation representation | Absent. Trajectory Analysis is only an optional landscape subsection |
| Complete token-cost baseline | The Codex MCP path does not return usage |

---

## Slash Commands

Slash-command mounting is optional and depends on the host agent; the shell quick start does not need it.
This repository does not bundle private agent configuration. If your agent supports Markdown command
files, run the following from `autovibeidea/` after replacing `EAR_COMMAND_DIR` with its command directory:

```bash
EAR_SKILL_ROOT="$(pwd -P)"
EAR_COMMAND_DIR="/absolute/path/to/your/agent/commands"  # Replace this path
mkdir -p "$EAR_COMMAND_DIR"
for skill_dir in "$EAR_SKILL_ROOT"/skills/*/; do
  skill_name="$(basename "$skill_dir")"
  command_file="$EAR_COMMAND_DIR/$skill_name.md"
  if [ -e "$command_file" ] || [ -L "$command_file" ]; then
    printf 'Keeping existing command: %s\n' "$command_file"
  else
    ln -s "${skill_dir}SKILL.md" "$command_file"
  fi
done
```

Absolute targets work regardless of command-directory depth. Existing files and links are left untouched;
inspect them separately if they point to an older checkout. Symlinks reflect subsequent skill edits,
but must be updated if the checkout moves. Skills can also be supplied directly as Markdown.

After mounting in a compatible agent, for example:

```text
/start "sample-efficiency bottlenecks in offline RL with image observations" -- venue: NeurIPS
```

| Command | Purpose |
|------|------|
| /start "direction" -- venue: ICML | **Start the complete pipeline in the background** (most common) |
| /idea-filter "constraints and interests" | Before choosing a direction, narrow vague interests to 1-3 locked directions |
| /idea-pipeline "direction" -- venue: ICML | Run the complete pipeline in the foreground |
| /lit-survey "direction" | Literature survey only |
| /idea-gen "direction" | Idea generation, including critical analysis |
| /idea-screen "idea" -- venue: ICML | Multidimensional screening only |
| /idea-refine "idea" | In-depth refinement only |
| /idea-refine "idea -- mode: socratic" | Socratic dialogue refinement |
| /idea-search -- budget: 8 | Allocate expansion budget among existing candidates through prior masks, UCT expansion, and backup |
| /fossil-hunt "field" | Find longstanding, unquestioned components in a field |
| /exp-design "method description" | Design paper experiments from first principles |
| /experiment-audit "code directory" | Audit experimental code for academic-integrity problems |

---

## Supported Venues

| Venue | Type |
|------|------|
| ICML / NeurIPS | ML methods and theory / broad ML and interdisciplinary work |
| EMNLP | NLP |
| VLDB / SIGMOD | Databases and data systems |

To add a venue, copy `venue-profiles/_template.md` and fill in calibration tiers and reviewer profiles. Profiles are subjective interpretations of public review criteria; adapt them to your target venue.

---

## Tools

| Tool | Purpose |
|---|---|
| `tools/arxiv_fetch.py` | Fetch arXiv metadata, with backoff for 406/429/5xx. **Fall back to WebSearch when arXiv throttles; do not wait indefinitely** |
| `tools/gpt_call.sh` | OpenAI API wrapper with thread semantics; records tokens in `outputs/COST_LOG.jsonl` |
| `tools/codex_call.sh` | Local Codex CLI (`codex exec`) as an external model, using the gpt_call.sh interface; **no API key required**, with session resumption and token capture |
| `tools/idea_nodes.py` | Manage `IDEA_NODES.jsonl`: init / add / update / validate / stats / tree |
| `tools/dedup_ideas.py` | Flag candidate duplicate pairs; adjudicate before using mark |
| `tools/entropy_map.py` | Compute high-entropy regions and failure modes from LANDSCAPE.json |
| `tools/mcts_search.py` | UCT search driver: init / mask / select / expand / backup / report |
| `scripts/selfcheck.sh` | Pre-commit self-check |

## Documentation

| File | Contents |
|---|---|
| `docs/IDEA_NODE_SCHEMA.md` | Idea-node field definitions |
| `docs/SEARCH_DESIGN.md` | UCT, mask semantics, and reward components |
| `docs/WORKFLOW.md` | Detailed workflow |
| `examples/judge-run/` | Sanitized excerpts from a real run, including the complete record of a novelty score revised from 8 to 4 after a second retrieval pass |

## ⚠️ Execution Safety

`./run.sh`, `./batch_codex.sh`, and the compatibility entry point `./batch.sh`
use a shared execution policy. By default:

```
codex exec -c 'sandbox_mode="workspace-write"' -c 'approval_policy="never"' \
  -c sandbox_workspace_write.network_access=false -c 'web_search="disabled"'
```

Commands run unattended inside the CLI sandbox. Out-of-policy actions are denied, not automatically
escalated. `--allow-network` explicitly enables shell network access and live search, which are needed
for fresh literature retrieval and nested API/CLI calls. CLI-to-model traffic remains enabled even
without this flag. A sandbox limits writes but does not hide all host files or constrain every MCP tool.

Use `--unsafe` only when you intentionally need unrestricted execution in an externally isolated
environment. It is never an automatic fallback. The equivalent environment variables for wrappers are
`EAR_ALLOW_NETWORK=1` and `EAR_UNSAFE=1`; both default to `0`.

For a verified **offline** isolation path, run `bash ../scripts/isolated_demo.sh` on Linux with
`bubblewrap`. For live research, prefer a disposable VM with only the required checkout and credentials;
the offline runner intentionally does not expose credentials or networking. Skills invoked manually
in an agent REPL are governed by that REPL's policy, not these launchers.

`tools/codex_call.sh` explicitly selects a read-only sandbox with no approvals and disabled web search,
including when resuming a thread. Read-only does not mean tool-free: permitted read commands can still run.
`tools/gpt_call.sh` is a text-only API client; neither prompts nor model responses are executed as code.

### Data handling

Before live runs, read [EAR's data-handling notice](../README.md#execution-safety-and-data-handling).
Prompts, retrieved text and relevant files can be sent to model services. Local output/log directories,
API conversation JSON files and Codex session history may preserve them. Logs are not automatically
safe to publish. The launcher prints a reminder before starting live execution.

---

## Known Limitations

The pipeline's critiques, novelty judgments, simulated review scores, and refinement scores all come from language-model judgments rather than real experiments. Therefore:

- **Outputs still need human verification.** Prompts prohibit fabricated citations and numbers, but model errors remain possible. A successful run is not proof of correctness or novelty.
- **Scores are not peer review.** Scores in `refine-logs/score-history.md` evaluate proposal text and do not predict acceptance.
- **Not finding similar work means only that no collision was found within the current search scope.** Read the concrete differences from the closest work in `SCREENING_REPORT.md` rather than relying only on the Novelty score.
- **Feasibility is a static estimate.** The Theory-Experiment Alignment Matrix uses domain priors to approximate the validation cost of theoretical claims. This low-cost estimate does not mean experiments have been run.

---

## Acknowledgments

The engineering structure was influenced by [ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep). The Novelty Assessment module in `idea-screen` adapts its novelty-check skill.
The Researcher-Fit Filter in `idea-gen`, covering Longevity / Passion / Application / Uniqueness, adapts a publicly available research-topic selection methodology; see [openbs](https://github.com/HeBingsheng/openbs).

## License

MIT. Copyright (c) 2026 Yingze Li, Dong Wang, Ben Wu. See [LICENSE](../LICENSE).
