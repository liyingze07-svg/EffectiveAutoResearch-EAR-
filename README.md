# EAR — Effective Auto Research

> **Turn research directions into proposals and mathematical papers, and reviewer feedback into responses.**

EAR is an automated research workbench for **research planning, mathematical research, and rebuttal drafting**. It preserves the materials behind each result: literature surveys, critical analysis, proofs, manuscripts, independent reviews, and response drafts.

Choosing a research direction is only the beginning: you still need to understand existing work, identify gaps, compare candidate ideas, and develop a concrete proposal. After receiving reviews, you need to organize responses grounded in the paper, connecting each reviewer's concerns with the information the Area Chair needs to see.

EAR provides a dedicated entry point for each stage:

| Workflow | Input | Core process | Main outputs |
| --- | --- | --- | --- |
| [**AutoVibeIdea**](autovibeidea/) | Research direction and target venue | Literature survey → critical analysis → idea generation → screening → refinement | Literature landscape, research gap matrix, ranked candidate ideas, and a research proposal draft |
| [**AutonomousMath**](autonomousmath/) | Research direction or proposal | Goal-driven tool loop → proofs → manuscript → independent terminal review → revision; optional genetic optimization | Proofs, LaTeX/PDF papers, version-bound review reports, resumable batches, and strategy evolution |
| [**AutoRebuttal**](rebuttal/) | Paper and its reviews | Staged drafting and review | Response drafts for selected reviewers and a comment to the Area Chair (AC) |

Use AutoVibeIdea to develop a proposal, AutonomousMath to pursue mathematical research and write a paper, and AutoRebuttal to organize responses after reviews arrive. All three can run independently from a complete EAR checkout.

---

## How EAR Works

### Break a goal into actionable research steps

EAR goes beyond a single prompt asking a model to suggest a research direction or write a response. It divides the task into stages: organize the materials, analyze them, generate candidates, and then screen, review, or refine them.

For research planning, an explicit analysis step connects the literature survey to candidate ideas. For rebuttals, drafting is part of a multistage process with review gates. Each workflow follows the structure of its task rather than combining everything into one long conversation.

### Keep the supporting materials, not just the final draft

A research proposal matters not only for what it says, but also for the prior work and questions it builds on. AutoVibeIdea saves the literature landscape, research gap analysis, candidate rankings, and final proposal as separate artifacts, making it possible to trace conclusions back to the analysis.

These artifacts support different conversations: a literature report helps you understand the field, a ranking helps you compare approaches, and a proposal draft gives you a basis for refining the research plan.

### Configure generation and review as separate roles

AutoVibeIdea supports review through separate Codex sessions. AutoRebuttal's cross-family consensus mode combines Codex and DeepSeek.

Run logs and degradation markers record the review route used. When review calls fail or fallbacks occur, markers for self-evaluation or single-family review help explain how the result was produced.

---

## AutoVibeIdea: From Research Direction to Proposal Draft

Given a research direction and a target venue, AutoVibeIdea develops a research plan through five stages:

```text
Research direction → Literature survey → Critical analysis → Idea generation → Screening and ranking → Proposal refinement
```

### 1. Literature survey: Understand where the field stands

The workflow begins by surveying literature relevant to the research direction and mapping related work to establish a foundation for analysis.

These materials help you understand the problem setting, how related studies connect, and what to read next. The survey is not merely a source of references for the final proposal; it is the starting point for identifying a research angle.

### 2. Critical analysis: Turn existing work into research questions

Building on the literature survey, the workflow conducts critical analysis and organizes research gaps into a matrix.

The literature landscape answers “What is existing work doing?” Gap analysis asks “What remains worth exploring?” Together, they give candidate ideas a concrete context, keeping discussion grounded in specific questions and prior work rather than a title that simply sounds novel.

### 3. Idea generation: Develop research angles you can compare

Using the survey and analysis, the workflow generates candidate research ideas, offering several possible approaches within the same direction.

This stage opens up the space of choices. Alongside the literature materials, you can compare the problems each idea addresses and decide which candidates deserve further screening and development.

### 4. Screening and ranking: Compare candidates together

The workflow screens candidate ideas, produces a model-generated ranking, and saves it to `outputs/SCREENING_RANKED.md`.

The ranking report provides a single place to compare candidates. Read it alongside the literature landscape and gap matrix to examine how each idea relates to the earlier analysis and decide where to focus further discussion.

### 5. Proposal refinement: Turn an idea into a structured research plan

After screening, the workflow refines the research idea and produces `refine-logs/FINAL_PROPOSAL.md`.

The result is a structured research proposal draft that can support group meetings, discussions about research topics, and further planning. The starting point is no longer just a broad direction, but a concrete proposal supported by intermediate analysis and ready for discussion and revision.

### Main outputs

```text
autovibeidea/
├── outputs/
│   ├── LANDSCAPE.md
│   └── SCREENING_RANKED.md
└── refine-logs/
    └── FINAL_PROPOSAL.md
```

| File | Contents | How to use it |
| --- | --- | --- |
| `outputs/LANDSCAPE.md` | Literature landscape and research gap matrix | Understand the background and the questions behind the candidate ideas |
| `outputs/SCREENING_RANKED.md` | Model-generated ranking of candidate ideas | Compare research angles and choose a focus for further discussion |
| `refine-logs/FINAL_PROPOSAL.md` | Refined, structured research proposal draft | Discuss, revise, and develop the research plan |

We recommend reading them in this order: **literature landscape → candidate ranking → final proposal**. This gives you both the result and the analysis that informed the final direction.

AutoVibeIdea is useful when entering a research area, comparing possible research topics, or turning a broad idea into a research proposal.

[Read the full AutoVibeIdea documentation →](autovibeidea/README.md)

---

## AutonomousMath: From Direction to Reviewed Mathematical Paper

AutonomousMath preserves the complete original engine as a composed goal prompt,
six research skills, and eight optional workflow adapters. Claude or Codex
coordinates the loop, chooses tools and research actions, develops natural-language
proofs, writes and compiles the paper, and revises from independent review feedback.
A portable supervisor provides batches, continuation and checkpoints.

The genetic optimizer can change research prompts, skills, worker code and
configuration while keeping the final reviewer fixed. It compares strategies on
the same task set, prioritizes paper quality and successful completion, and exposes
progress and controls through a local dashboard. Lean is an optional final-checking
interface after terminal acceptance.

Try the complete control flow without model calls:

```bash
python3 -m autonomousmath doctor --offline
python3 -m autonomousmath run --offline --workspace workspaces/math-demo
python3 -m autonomousmath.optimizer evolve \
  --workspace workspaces/evolution-demo --offline --generations 2
```

Offline reviews are synthetic fixtures and never count as real paper acceptance.
For live Claude/Codex runs, continuous operation and the dashboard, see
[the AutonomousMath guide](autonomousmath/README.md).

---

## AutoRebuttal: From Reviewer Feedback to Response Drafts

AutoRebuttal is designed for rebuttal workflows in **EMNLP / ACL Rolling Review**. Given a paper and its reviews, it drafts responses for selected reviewers and a comment to the Area Chair (AC).

```text
Paper + Reviews
       ↓
18 stage prompts · 4 review gates
       ↓
Reviewer response drafts + AC comment
```

### Organize responses around the paper and its reviews

Prepare a paper and its reviews, specify the reviewers you want to address, and enter the rebuttal workflow.

The task involves more than wording. The paper provides the research content on which responses must be grounded, while the reviews identify the questions to answer. The workflow drafts responses from these inputs and uses subsequent review stages to check and refine them.

### Develop drafts through stages and review gates

AutoRebuttal contains **18 stage prompts and 4 review gates**, organizing drafting and review into a multistage process.

This structure gives drafts multiple opportunities for checking and revision. The workflow covers both responses to individual reviewers and the AC comment, allowing the needs of these different audiences to be addressed separately.

### Use Codex and DeepSeek for cross-family review

Cross-family consensus mode combines Codex and DeepSeek so that different model families participate in review.

When the workflow falls back to a single model family, the results are explicitly marked. Single-family fallback and passing cross-family review are distinct states and are not treated as equivalent.

### Deliver two kinds of response materials

| Deliverable | Audience | Purpose |
| --- | --- | --- |
| Reviewer response drafts | Selected reviewers for the current round | Organize answers to each review as a basis for further revision |
| AC comment | Area Chair | Present the information that needs to be communicated to the AC, separately from reviewer responses |

AutoRebuttal is useful after reviews arrive and you need to organize response materials. It works directly with an existing paper and reviews, without depending on AutoVibeIdea outputs.

[Read the full AutoRebuttal documentation →](rebuttal/README.md)

---

## Repository Structure

Clone the complete EAR repository once, then use the workflow you need. Root-level scripts provide shared checks and an offline demo.

```text
EAR/
├── autovibeidea/          # Research planning workflow
├── autonomousmath/       # Complete math engine, genetic optimizer and dashboard
├── rebuttal/              # Rebuttal drafting workflow
└── scripts/
    ├── doctor.py          # Local environment and dependency checks
    ├── offline_demo.py    # Offline demo with no model calls
    ├── isolated_demo.sh   # Isolated offline demo on Linux
    ├── secret_scan.py     # Shared secret scanner
    └── public_source_audit.py # Portable source and private-material audit
```

Detailed configuration and operation instructions live in each subproject's README. This root README provides the project overview and shared entry points.

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/liyingze07-svg/EffectiveAutoResearch-EAR-.git EAR
cd EAR
```

Start with the offline demo to inspect the workflow checks and output structure before configuring live model calls.

### 2. Run the zero-cost offline demo

The offline demo requires only **Python 3.10+**. No API key, Codex installation, or third-party Python packages are needed.

```bash
python3 scripts/doctor.py --offline
python3 scripts/offline_demo.py
```

Expected output:

```text
PASS: idea validation/report, five contracts, and synthetic rebuttal dry-run.
```

This checks idea validation and reporting, five contract files, and a dry-run of a synthetic rebuttal case. The program prints a temporary directory containing the demo results:

| Artifact | Contents |
| --- | --- |
| `SUMMARY.json` | Offline demo summary |
| Idea search report | An example of the report structure |
| Synthetic rebuttal case | Dry-run artifacts, including `DRY_RUN.txt` |

The demo makes no model calls. It checks workflow wiring and artifact structure, not the quality of an actual research proposal or rebuttal.

To keep the results at a chosen path:

```bash
python3 scripts/offline_demo.py --output outputs/first-demo
```

The path must be a **new directory that does not already exist**. If it exists, the program refuses to run rather than overwrite previous materials.

### 3. Configure the live environment

AutoVibeIdea and AutoRebuttal share these live requirements. AutonomousMath also
supports a Claude coordinator; see its guide for the LaTeX and reviewer prerequisites.

| Component | Requirement |
| --- | --- |
| Operating system | Linux or WSL2 |
| Shell | Bash |
| Python | 3.10 or later |
| Shared model driver | Authenticated Codex CLI |
| Codex installation tools | Node.js and npm |

Install and authenticate Codex CLI:

```bash
npm install -g @openai/codex
codex login
```

Live runs use account quota and may incur charges. The doctor checks local prerequisites and dependencies, not authentication, model access, or endpoint availability.

AutoRebuttal also requires its Python dependencies and DeepSeek configuration. See its subproject documentation for the setup steps.

### 4. Start AutoVibeIdea

Run these commands from the EAR repository root:

```bash
# Check local prerequisites for AutoVibeIdea
python3 scripts/doctor.py --component autovibeidea

# Enter the subproject
cd autovibeidea

# Start the research planning workflow
./run.sh --allow-network --codex-cli --daemon "your research direction" NeurIPS
```

Replace `"your research direction"` with the question you want to explore and `NeurIPS` with your target venue.

| Argument | Meaning |
| --- | --- |
| `--allow-network` | Allow shell network access and enable live web search |
| `--codex-cli` | Use the locally authenticated Codex CLI to request review in separate sessions |
| `--daemon` | Start the workflow in the background |
| `"your research direction"` | Research direction for this run |
| `NeurIPS` | Target venue |

After starting, check progress from `autovibeidea/`:

```bash
./run.sh --status
```

To stop the run and clean up its child processes:

```bash
./run.sh --stop
```

We recommend the `--codex-cli` review route. It requests generation and review in separate Codex sessions; see [Review Mechanisms and Process Records](#review-mechanisms-and-process-records) for session separation and fallback behavior.

Outputs appear under `outputs/` and `refine-logs/`, as described above. These contain the literature analysis, candidate rankings, and final proposal draft.

### 5. Start AutoRebuttal

From the EAR repository root, enter `rebuttal/` and follow its setup instructions to prepare the environment and a case. If you just followed the AutoVibeIdea example, return to the repository root first.

```bash
cd rebuttal
```

The complete workflow includes these steps:

| Step | What to do |
| --- | --- |
| Prepare the environment | Install Python dependencies and configure Codex and DeepSeek |
| Prepare a case | Supply a paper and its reviews |
| Generate contracts | Generate the workflow's contract files as described in the documentation |
| Inspect a dry-run | Follow the documented dry-run steps |
| Run with live models | Execute the rebuttal workflow using the configured model services |
| Inspect the results | Locate the reviewer response drafts and AC comment, then continue editing |

The [AutoRebuttal quick start](rebuttal/README.md#install-and-run) covers input preparation, contract generation, dry-run and live commands, and where to find the outputs.

---

## Review Mechanisms and Process Records

### Separate sessions and different model families are distinct configurations

AutoVibeIdea's `--codex-cli` route uses the local login to request review in separate Codex sessions. Separate sessions can reduce shared context between generation and review, but they do not imply different models or providers, nor fully independent judgments.

AutoRebuttal's cross-family consensus mode combines Codex and DeepSeek. The distinction is not merely between sessions: different model families participate in review.

### Review fallbacks are marked

In AutoVibeIdea's shell workflow, evaluation may take place in the same session that generates ideas when no review route is explicitly selected. Failed review calls may also trigger a fallback to self-evaluation.

Run logs and degradation markers distinguish these cases. When reading rankings or review outcomes, consult these records to understand which review path was actually used, rather than relying only on a final score or pass status.

### Connect key claims to evidence

EAR's workflows require key claims to be linked to literature, code, or experimental records. Literature analysis, research proposals, and rebuttals should be organized around the available materials.

Prompts and checks instruct models to reject unsupported numbers and citations. Missing evidence should be recorded explicitly rather than filled in with invented content. Evidence tracing and missing-evidence markers preserve the basis of the text, helping readers trace drafts back to their sources.

### Degradation does not expand execution permissions

When some dependencies are unavailable, the workflow can use a documented fallback. Self-evaluation and single-family review provide weaker assurance and should remain distinguishable from the intended review configuration.

A safety denial from a model or tool does not automatically trigger unrestricted execution and is not a reason to expand permissions.

---

## Advanced Execution and Configuration

### Isolated offline checks on Linux

To run the offline demo with operating-system-level isolation, install `bubblewrap`, then run this from the EAR repository root:

```bash
bash scripts/isolated_demo.sh
```

The script mounts the checkout read-only, clears the environment, hides the host home directory, and disables networking. Only the printed output directory is writable on the host.

This is an **offline demo runner** for isolated workflow checks, not a container environment for live model calls.

<a id="execution-safety-and-data-handling"></a>

### Model services and network access

Live runs send prompts and relevant input and tool content to the configured services.

| Workflow | Services used |
| --- | --- |
| AutoVibeIdea | Codex / OpenAI, with the OpenAI API as an optional route |
| AutonomousMath | Codex / OpenAI or Claude / Anthropic; terminal-review route is configurable |
| AutoRebuttal | Codex / OpenAI and DeepSeek, or explicitly configured endpoints |
| Enabled web search and MCP integrations | May contact additional external services |

The default agent shell policy for AutoVibeIdea and AutoRebuttal is:

| Setting | Default behavior |
| --- | --- |
| Sandbox mode | `workspace-write` |
| Unattended approval policy | `never` |
| Shell network access | Disabled |

AutoVibeIdea's `--allow-network` also enables live web search. Shell network restrictions do not block CLI-to-model API traffic or direct verifier/API calls.

AutonomousMath's Codex research worker defaults to `workspace-write` with shell
network access enabled for literature and novelty checks; its JSON configuration
can set `network_access=false`. Terminal Codex reviews use fresh read-only sessions.
Claude execution uses its CLI tool permissions; see the AutonomousMath guide.

`workspace-write` limits writes, but it is not a confidentiality boundary: the CLI may still read host files that its permissions allow, and MCP tools have their own permissions.

`--unsafe` allows unrestricted execution and should be used only in a disposable, externally isolated environment.

[Read the official configuration reference →](https://learn.chatgpt.com/docs/config-file/config-reference)

### Local outputs and session records

`outputs/`, `refine-logs/`, rebuttal campaign directories, archives, API conversation JSON files, and CLI session history may contain input materials and model responses.

API conversation files are retained to support resuming a conversation; temporary response and event files are cleaned up. New output files created by the launchers use private permissions. Provider-side retention depends on the account and service provider settings.

### Pre-commit checks

EAR provides a shared secret scanner covering all subprojects.

After `git add` and before committing, run this from the repository root:

```bash
python3 scripts/secret_scan.py --staged
```

This scans the contents of Git's staged files. Omit `--staged` to inspect tracked and unignored worktree files:

```bash
python3 scripts/secret_scan.py
```

The older `rebuttal/scripts/secret_scan.sh` command delegates to the same scanner. Reports do not display matched contents. Detection uses heuristics and is not equivalent to a complete security audit.

---

## License

MIT License. Copyright (c) 2026 Yingze Li, Dong Wang, Ben Wu.

See [LICENSE](LICENSE).
