# EAR — Effective Auto Research

An automated research idea discovery pipeline. Provide a research direction and run the full pipeline in the background to produce a venue-ready proposal after critical analysis, multidimensional screening, reviewer simulation, and theory–experiment alignment checks.

All outputs are in English.

---

## Capability Levels

This table classifies capabilities by their implementation status. **Implemented = code is present and executes in the pipeline; Experimental = implemented but not evaluated through controlled comparisons; Roadmap = not implemented.** Do not treat Roadmap items as current capabilities.

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

## Quick Start

```bash
git clone <this-repo> EAR && cd EAR/autovibeidea
./run.sh --daemon "your research direction" NeurIPS  # Full pipeline in the background (recommended)
./run.sh --status                                  # Check progress
tail -f outputs/pipeline.log                       # Follow logs
```

In an agent environment supporting slash commands, such as Codex REPL:

```
/start "sample-efficiency bottlenecks in offline RL with image observations" -- venue: NeurIPS
```

---

## Slash Commands

This repository does not bundle private configuration directories for agent tools. If your agent supports mounting Markdown as slash commands, run the following once from this subproject's directory, substituting its command directory for `<CMD_DIR>`:

```bash
mkdir -p <CMD_DIR>
for d in skills/*/; do
  n=$(basename "$d")
  ln -sf "../../skills/$n/SKILL.md" "<CMD_DIR>/$n.md"
done
```

Use symlinks rather than copies so changes to `SKILL.md` take effect immediately without synchronization drift.
Mounting is optional: each skill is self-contained Markdown whose contents can be supplied directly to a model.

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

## Pipeline

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
  PIPELINE_STATE.json               Resumption checkpoint

refine-logs/
  skeleton.md                       State A → State B argument skeleton
  round-N-review.md / -refinement.md Per-round review and revision
  round-N-expanded.md               Deep Expansion output
  FINAL_PROPOSAL.md                 Final proposal
  REFINEMENT_REPORT.md / score-history.md
```

`./clean.sh` archives current outputs under archive/. Use `./clean.sh` --name "MyRun_v1" to specify the archive name.

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

`./run.sh` and `./batch_codex.sh` invoke Codex through `tools/run_codex_skill.sh` using:

```
codex exec --dangerously-bypass-approvals-and-sandbox
```

**Codex runs without a sandbox or step-by-step approval**, allowing unattended reads and writes to `outputs/` and `refine-logs/` and retrieval-tool calls. It can therefore execute arbitrary shell commands on your machine.

If you do not accept this premise, use either alternative:

1. **Run inside a container or disposable VM**, mounting the repository.
2. **Invoke skills individually in an agent REPL**, such as /lit-survey or /idea-gen, instead of using the shell entry points. Your REPL's permission policy governs execution; the repository does not bypass it.

The separate `tools/codex_call.sh` wrapper, used for individual external-model calls in `--codex-cli` mode, **does not use** this flag. It is a question-and-answer call and does not execute commands.

## Prerequisites

**One of the following is required:**

```bash
# Option A (recommended): local Codex CLI, using its own login; no API key needed
npm install -g @openai/codex@latest
codex login                       # Skip if already logged in
./run.sh --codex-cli "direction" NeurIPS

# Option B: direct OpenAI API
export OPENAI_API_KEY=...          # Or save it in ~/.openai_key
./run.sh --gpt-only "direction" NeurIPS

# Option C: Codex MCP (older Codex versions only; see below)
claude mcp add codex -s user -- codex mcp-server
```

> ⚠️ **Codex CLI removed the `mcp-server` subcommand in 0.158.0**. Option C fails with
> `Connection closed` on newer versions. Use Option A instead: `tools/codex_call.sh`
> provides equivalent functionality through `codex exec`, including resume and token
> usage capture, and has been tested.

**Optional:** Zotero MCP for a local paper library and Obsidian MCP for notes. When unavailable, retrieval falls back to WebSearch.

When an external-model call fails, skills fall back to local-agent self-evaluation and automatically relax scoring thresholds; the pipeline continues without waiting for input.

---

## Known Limitations

The pipeline's critiques, novelty judgments, simulated review scores, and refinement scores all come from language-model judgments rather than real experiments. Therefore:

- **Scores are not peer review.** Scores in `refine-logs/score-history.md` evaluate proposal text and do not predict acceptance.
- **Not finding similar work means only that no collision was found within the current search scope.** Read the concrete differences from the closest work in `SCREENING_REPORT.md` rather than relying only on the Novelty score.
- **Feasibility is a static estimate.** The Theory-Experiment Alignment Matrix uses domain priors to approximate the validation cost of theoretical claims. This low-cost estimate does not mean experiments have been run.

---

## Acknowledgments

The engineering structure was influenced by [ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep). The Novelty Assessment module in `idea-screen` adapts its novelty-check skill.
The Researcher-Fit Filter in `idea-gen`, covering Longevity / Passion / Application / Uniqueness, adapts a publicly available research-topic selection methodology; see [openbs](https://github.com/HeBingsheng/openbs).

## License

MIT. Copyright (c) 2026 Yingze Li, Dong Wang, Ben Wu. See [LICENSE](../LICENSE).
