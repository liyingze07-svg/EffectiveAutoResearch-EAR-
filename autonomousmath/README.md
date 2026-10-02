# AutonomousMath — a complete goal-driven research engine

AutonomousMath turns a research direction into an informal mathematical proof,
a complete LaTeX manuscript, and an independently reviewed paper. Its original
research method is preserved as a composed goal prompt and a self-contained skill
pool. Claude and Codex can both coordinate the research loop.

The research model chooses candidates, calls tools, checks proofs, strengthens
claims, writes, and revises. The Python supervisor supplies continuation,
batch execution, checkpoints and a separate terminal reviewer. It does not
replace the research method with a sequence of single-purpose stage scripts.

```text
Direction → Seek / novelty → Prover ↔ Skeptic → Harden → Write / compile
                                                       ↓
                     Revise ← independent terminal review → accepted artifacts

Strategies → identical evaluation tasks → quality / writing / acceptance
     ↑                                            ↓
     └──────── elite + crossover + mutation ───────┘
```

## Inspect the complete loop without model calls

Run commands from the EAR repository root. Python 3.10+ is sufficient for the
offline workflow and dashboard; no third-party Python packages are required.

```bash
python3 -m autonomousmath doctor --offline
python3 -m autonomousmath run --offline --workspace workspaces/math-demo --episodes 1
python3 -m autonomousmath status --workspace workspaces/math-demo
```

This exercises the actual artifact, continuation and independent-review wiring:
the synthetic first draft is rejected, feedback reaches the worker, the proof
and manuscript are revised, and the second fixture review passes. The result is
labelled `offline_demo`, with `accepted=false`. It is not a scientific result.

```bash
python3 -m autonomousmath.optimizer evolve \
  --workspace workspaces/evolution-demo --offline --generations 2
python3 -m autonomousmath.optimizer serve \
  --workspace workspaces/evolution-demo --port 8765
```

The local dashboard shows generation progress, strategy lineage, quality,
writing and acceptance metrics, and the permanent baseline. It provides start,
pause, resume, parameter controls and an emergency stop. Opening the dashboard
does not start research calls. Offline fixture success is displayed separately
from real acceptance. See [evolution details](docs/EVOLUTION.md).

## Run with Codex or Claude

Use your own authenticated CLI installation. Live execution also requires a
LaTeX toolchain (`pdflatex`, `bibtex`) and PDF utilities. The doctor reads local
prerequisites without requesting a model response.

```bash
python3 -m autonomousmath doctor --backend codex
python3 -m autonomousmath run --backend codex \
  --direction "your ML-theory research direction" \
  --workspace workspaces/research --episodes 3

python3 -m autonomousmath run --backend claude \
  --direction "your ML-theory research direction" \
  --workspace workspaces/claude-research --episodes 3
```

Codex mode uses two fresh, independent Codex terminal-review sessions. Claude
mode preserves the original Codex + Claude dual-review route. The two-Codex
route is explicitly a single-family variant, not a claim of cross-family
independence. Select the dual-family route from either coordinator with
`--review-backends codex,claude`.

Research tools run with workspace-write permissions by default. Live calls use
your model account and send research inputs to the selected providers. Shell
network access is configurable; a read-only filesystem setting alone is not a
guarantee of network isolation. Runtime outputs and CLI session history can
contain unpublished research. The checkout contains no credentials or login
state.

For continuous batches, replace `--episodes 3` with `--continuous`. To request a
soft stop, run `python3 -m autonomousmath stop --workspace workspaces/research`.
The next explicit run resumes saved work. Infrastructure or quota failures save
checkpoints and obey retry/backoff limits; they never count as paper rejection.

## What stays fixed, and what evolves

The goal prompt, research skills, tools, worker code and candidate configuration
can evolve. Candidate workspaces contain a mutable copy of those resources.
The terminal reviewer remains in the original parent package, outside candidates.
Its source and rubric fingerprints are checked around execution and review.

The fixed rubric is [SAC_PROMPT.md](referee/SAC_PROMPT.md), extracted from the
original goal. Exactly two fresh reviews must both reach Weak Accept or better.
The full manuscript and proof are submitted; source input is never silently
truncated. Each independent result retains the complete five-part SAC report,
including the three reviewer roles and meta review. A passing result binds to the proof, manuscript sources and assets.
Live final review independently compiles a snapshot and records the compiled
PDF hash. Internal audits and a worker's self-reported verdict are not terminal
acceptance.

The main efficiency signal is producing high-quality papers with fewer failed
attempts and revision loops. The optimizer compares strategies on the same task
set and retains a permanent baseline. Quality, written rate and acceptance drive
selection; ties prefer fewer calls per effective result, then fewer review
revisions. A strategy with equal quality and less repeated work can replace the
elite. It does not implement a dollar-pricing optimizer. Invocation and generation
records make work and failures visible.

## Artifacts and checkpoints

```text
workspace/
  state.json / events.jsonl
  tasks/episode-*/
    PROGRESS.md / proof.md / CANDIDATE.json
    paper/main.tex / main.pdf / sections/ / appendix/
    REVIEW_FEEDBACK.md
  reviews/episode-*/round-*/
    source/ / result.json
  checks/                 # optional final formalization reports
```

Each episode owns its files. Authoritative reviews live outside the research
worker directory. Use an ignored workspace or a directory outside the checkout
for all live runs. Do not commit generated papers, queues, sessions or logs.

The public skill pool retains six original skills and eight optional JavaScript
workflow adapters, plus writing guidance and ICLR templates. Workflow adapters
require a host that provides their runtime API; they are not standalone Node
programs. The portable runner supports the direct-tool path without that host.
See [engine design](docs/ENGINE_DESIGN.md).

## Final Lean checking interface

Natural-language proof comes first. After real terminal acceptance,
`final_check_command` can hand the version-bound paper to an external
autoformalizer. The default is `deferred`, so Lean is not required to start the
research loop. See [the checker contract](docs/FINAL_CHECKING.md).

The optional adapter uses the existing
[LeanSearch-v2 verifier](https://github.com/frenzymath/LeanSearch-v2/tree/main/src/leansearchv2/prove).
It checks an already formalized Lean file; mapping informal paper claims to
Lean statements remains the autoformalizer's responsibility.

## Validation

```bash
python3 -m unittest discover -s autonomousmath/tests -v
python3 scripts/secret_scan.py
python3 scripts/public_source_audit.py
```

The offline tests validate control flow, version binding, fixed-review
separation, checkpointing and dashboard controls. They do not establish the
quality of a real research result. This release has not run paid research
episodes as part of its preparation.
