<div align="center">

<img src="assets/ear-banner.svg" alt="EAR — Effective Auto Research. Research agents. Checkable results." width="100%">

<p><a href="#core-philosophy"><img src="assets/readme-highlight.svg" alt="EAR design principle · #1 Priority: Human Time" width="250" height="55"></a></p>

<a href="docs/technical-report/v10/reports/EAR_Technical_Report_EN.pdf"><img src="assets/readme-paper.svg" alt="Paper" width="104" height="32"></a>
<a href="https://liyingze07-svg.github.io/EffectiveAutoResearch-EAR-/"><img src="assets/readme-demo.svg" alt="Demo" width="104" height="32"></a>
<a href="docs/getting-started.md"><img src="assets/readme-docs.svg" alt="Docs" width="104" height="32"></a>

[中文](README.zh-CN.md) · [Examples](examples/README.md) · [Contributing](CONTRIBUTING.md)

[![GitHub](https://img.shields.io/badge/GitHub-EAR-181717?logo=github&logoColor=white)](https://github.com/liyingze07-svg/EffectiveAutoResearch-EAR-) [![License: MIT](https://img.shields.io/badge/License-MIT-2ea44f)](LICENSE) [![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776ab?logo=python&logoColor=white)](docs/getting-started.md)

</div>

EAR combines retrieval, critique and revision to produce research proposals, mathematical manuscripts and evidence-linked reviewer responses. **The three workflows run independently.**

![EAR inputs and outputs: research direction → AutoVibeIdea → proposal; research problem → AutonomousMath → paper and proof; paper and reviews → AutoRebuttal → responses and evidence.](assets/ear-workflows.svg)

<a name="core-philosophy"></a>

## <img src="assets/readme-icons/philosophy.svg" width="28" height="28" alt=""> Core philosophy

**Spend human time on direction and judgment.** EAR is designed to reduce active human effort subject to research-quality and compute-budget constraints.

- **Challenge ideas early.** Retrieval and critique expose overlap and help narrow a candidate before further investment.
- **Learn from feedback.** Revise the research artifact within a task; evolve the research strategy across tasks.
- **Keep the evidence.** Save literature, proofs, manuscript snapshots and reviews so the work can be inspected and continued.

<a name="modules"></a>

## <img src="assets/readme-icons/modules.svg" width="28" height="28" alt=""> Three research modules

| Module | Start with | Deliverables |
| --- | --- | --- |
| [**AutoVibeIdea**](autovibeidea/) | A research direction and constraints | Literature landscape, ranked candidates and proposal draft |
| [**AutonomousMath**](autonomousmath/) | A mathematical question | Proof attempts, LaTeX/PDF manuscript, version-bound reviews and checkpoints |
| [**AutoRebuttal**](rebuttal/) | A paper and reviewer comments | Evidence-linked replies, AC comment and unresolved-concern ledger |

Use each module independently, with its own workspace. File handoffs between modules are currently manual.

<a name="results"></a>

## <img src="assets/readme-icons/results.svg" width="28" height="28" alt=""> Results and evidence

**AutonomousMath** · **64** attempts · **28** completed manuscripts · **15** selected-best historical passes.

### Manuscript revision

Current-version passes increased **3 → 12** across three revision rounds on the same 28 completed manuscripts.

[![Current-version passes: 3, 10, 10, 12 out of 28 manuscripts; mean model-assessor score: 4.65, 5.25, 5.50, 5.67.](assets/readme-figures/en/inner_progress.png)](assets/readme-figures/en/inner_progress.svg)

### Strategy evolution

In the selected G3 comparison, research calls per historical pass decreased **20.50 → 9.67 (−52.8%)**.

[![Selected G3 versus baseline: research calls per historical pass decrease by 52.8%; the reconstructed research, review and revision proxy decreases by 42.6%.](assets/readme-figures/en/cost_comparison.png)](assets/readme-figures/en/cost_comparison.svg)

“Pass” means at least one Accept among three historical model-assessor sessions. The G3 comparison uses four unpaired attempts per strategy, with self-selected targets; counts cover partial machine work. Human-time savings remain unmeasured. [Report →](docs/technical-report/v10/README.md) · [Source data →](docs/technical-report/v6/data/README.md)

<details>
<summary>Full evaluation protocol · A recorded idea decision</summary>

The 28-manuscript revision comparison is conditional on completed writing and excludes unwritten attempts. Current-version passes and selected-best passes use different retention rules. The comparison does not isolate the effect of feedback from re-assessment.

The G3 batch was selected retrospectively: the selected strategy passed 3/4 attempts versus the baseline's 2/4. A stricter retained-vote diagnostic gives 1/4 for both. Invocation counts are partial work proxies, not total API cost, elapsed time or active human time. These historical model judgments do not establish conference acceptance. The current portable engine uses a different terminal review gate. [Full protocol →](docs/technical-report/v6/data/protocol.json)

In one released AutoVibeIdea trace, deeper retrieval found close prior work, lowered a candidate's novelty score **8/10 → 4/10**, and changed its recommendation to **ABANDON**. Public excerpts omit full proposals and identifying technical details. This is one historical model judgment, not a novelty benchmark. [Annotated trace →](autovibeidea/examples/judge-run/README.md)

</details>

<a name="quickstart"></a>

## <img src="assets/readme-icons/quickstart.svg" width="28" height="28" alt=""> Quickstart

Launch the project page and interactive demo:

```bash
git clone https://github.com/liyingze07-svg/EffectiveAutoResearch-EAR-.git EAR
cd EAR
python3 -m ear demo studio
```

Open **<http://127.0.0.1:8765/>**. The demo needs only Python 3.10+ and its standard library—no GPU, API key or model account. English is the default; `?lang=zh` opens the Chinese counterpart.

For live research, configure authenticated Codex or Claude and module-specific dependencies using the [setup guide](docs/getting-started.md). Once the math backend is configured:

```bash
python3 -m ear math run --backend codex \
  --direction "your mathematical research question" \
  --workspace workspaces/math-01 --episodes 1
```

[Idea discovery →](docs/getting-started.md#develop-a-research-direction) · [Mathematical research →](docs/getting-started.md#pursue-a-mathematical-question) · [Reviewer responses →](docs/getting-started.md#prepare-a-rebuttal-case)

<a name="interactive-demo"></a>

## <img src="assets/readme-icons/demo.svg" width="28" height="28" alt=""> Demo

**Explore a research process. Inspect and download its output.**

![EAR Studio: input, idea search and a downloadable proposal on one canvas.](assets/readme-studio.en.png)

| Module | Try it in EAR Studio |
| --- | --- |
| **AutoVibeIdea** | Search the idea tree, inspect a critique and download a proposal. |
| **AutonomousMath** | Check a proof, change the error level and download the corresponding paper. |
| **AutoRebuttal** | Select a reviewer, trace the evidence and download the response. |

The demo uses authored examples; numerical checks execute locally. [Demo guide and provenance →](docs/demo-studio.md)

<details>
<summary>Export a single HTML · Run offline examples</summary>

Export the demo for a presentation or recording, then open it directly in a browser:

```bash
python3 -m ear demo studio --export workspaces/ear-demo.html
```

Recompute the released metrics and check the example workflows:

```bash
python3 -m ear demo report
python3 -m ear demo check
```

`demo report` verifies the report arithmetic; `demo check` validates the idea trace and synthetic rebuttal wiring. To exercise rejection, revision and saved math artifacts:

```bash
python3 -m ear math run --offline --workspace workspaces/math-demo --episodes 1
python3 -m ear math status --workspace workspaces/math-demo
```

The fixture remains labeled `offline_demo`, `accepted=false`. [All examples →](examples/README.md)

</details>

<a name="architecture"></a>

## <img src="assets/readme-icons/workflow.svg" width="28" height="28" alt=""> Workflow and architecture

### AutoVibeIdea · Search, critique, refine

Literature retrieval and critique update candidate values. UCT-guided expansion prioritizes promising branches; evidence and feasibility checks prune others. The retained direction becomes a proposal and validation plan.

![AutoVibeIdea: direction, retrieval, candidate expansion, evaluation and refinement; evidence feeds back into search.](assets/readme-figures/en/idea-architecture.svg)

[Search tools and proposal artifacts →](autovibeidea/)

### AutonomousMath · Revise the work, evolve the strategy

The research worker investigates, proves, checks and writes. A supervisor preserves checkpoints; a fixed referee reviews the manuscript snapshot and returns feedback for revision. The optional outer loop selects and evolves strategies while retaining the baseline and fixed reviewer.

![AutonomousMath: research worker, supervisor and fixed referee in the inner loop; selection and strategy evolution in the outer loop.](assets/readme-figures/en/math-architecture.svg)

The current terminal gate requires two fresh reviews ≥ Weak Accept. [Engine design →](autonomousmath/docs/ENGINE_DESIGN.md) · [Strategy evolution →](autonomousmath/docs/EVOLUTION.md)

### AutoRebuttal · Connect concerns to evidence

Reviewer concerns are mapped to paper evidence before drafting. Staged checks examine concern coverage, persuasion, faithfulness and wording risks. The output keeps replies, the AC comment and unresolved concerns distinct.

![AutoRebuttal: concern diagnosis, evidence mapping, response drafting, staged review and delivery.](assets/readme-figures/en/rebuttal-architecture.svg)

[Inputs, review gates and outputs →](rebuttal/) · [Execution and review routes →](docs/operations.md)

<a name="repository-structure"></a>

## <img src="assets/readme-icons/structure.svg" width="28" height="28" alt=""> Repository structure

```text
EAR/
├── ear/                      # Shared launcher and local demo server
├── autovibeidea/              # Idea discovery and proposal development
├── autonomousmath/            # Research engine, evolution and dashboard
├── rebuttal/                  # Reviewer responses and evaluation
├── examples/                  # Interactive studio and reproducible examples
├── assets/                    # README visuals
├── docs/                      # Setup, architecture and operations
│   └── technical-report/      # v10 report and preserved v6 evidence
└── scripts/                   # Environment checks and source audits
```

<a name="documentation"></a>

## <img src="assets/readme-icons/docs.svg" width="28" height="28" alt=""> Documentation

| Start here | What you will find |
| --- | --- |
| [Getting started](docs/getting-started.md) | Inputs, dependencies and live commands |
| [Architecture](docs/architecture.md) | Module boundaries and saved artifacts |
| [Strategy evolution](autonomousmath/docs/EVOLUTION.md) | Outer loop and research dashboard |
| [Operations](docs/operations.md) | Network access, review routes and checkpoints |
| [Report release](docs/technical-report/v10/README.md) | Bilingual PDF, data and recomputation |

<a name="contributing"></a>

## <img src="assets/readme-icons/contributing.svg" width="28" height="28" alt=""> Contributing

Bug reports, reproducible cases and focused improvements are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) for checks and pull request guidance, or [open an issue](https://github.com/liyingze07-svg/EffectiveAutoResearch-EAR-/issues).

<a name="citation"></a>

## <img src="assets/readme-icons/citation.svg" width="28" height="28" alt=""> Citation

If EAR supports your research, cite the technical report and record the repository revision you used. GitHub's **Cite this repository** menu reads [CITATION.cff](CITATION.cff).

```bibtex
@techreport{li2026ear,
  title       = {{EAR}: Advance research through feedback. Improve strategies through results.},
  author      = {Li, Yingze and Wang, Dong and Wu, Ben and Liu, Xianglong and Wang, Hongzhi},
  institution = {Harbin Institute of Technology},
  year        = {2026},
  month       = oct,
  note        = {Technical report, version 10},
  url         = {https://github.com/liyingze07-svg/EffectiveAutoResearch-EAR-}
}
```

[MIT License](LICENSE) · Copyright (c) 2026 Yingze Li, Dong Wang, Ben Wu.
