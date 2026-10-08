# EAR project page and research demo

```bash
python3 -m ear demo studio
```

Python 3.10+ and its standard library are sufficient. Open `http://127.0.0.1:8765/` for English; `?lang=zh` provides the Chinese counterpart. No model account, GPU, Node.js or third-party Python package is needed. `--no-open` prints the address; `--port 0` chooses a free port.

The launcher verifies the 48 original report files, recomputes aggregate results and runs the actual synthetic math fixture and rebuttal dry-run. It does not start live research.

## Project page

A static figure presents the three independent workflows together:

| Input | Workflow | Deliverable |
| --- | --- | --- |
| Research direction and constraints | AutoVibeIdea | Proposal, literature and validation plan |
| Research problem and assumptions | AutonomousMath | Manuscript, proof, code and reviews |
| Paper and reviewer concerns | AutoRebuttal | Replies and an evidence ledger |

The method section contains downloadable English and Chinese SVG figures drawn from the module contracts and the published v10 report. The mathematical diagram separates the research worker, supervisor, fixed referee and outer strategy loop. Idea search and rebuttal have their own diagrams. The Paper link opens v10. Historical chart inputs remain pinned to the preserved v6 evidence; v10 includes identical aggregate data.

The main page keeps only necessary labels and actions. Example provenance, historical evaluation limits and original source records are expandable.

## Interactive EAR Studio

The Mac-style window has three workflow tabs. Each uses one canvas: **input on the left, process in the middle, output on the right**. Clicking an action draws the process connections and reveals the artifact without replacing the scene. Process nodes expose the relevant reasoning in place. The layouts stack on phones; tab selection also supports arrow keys.

- **AutoVibeIdea:** choose accuracy or compute budget, then **Search ideas**. The UCT tree retains a scoped candidate and prunes overlap and overbroad branches. Inspect retrieval or critique and download the example proposal with its validation plan.
- **AutonomousMath:** choose persistent or vanishing error, then **Build paper**. Seek, Prover, Skeptic and Write remain beside the paper, proof and computed curve. Inspect the failed candidate through Skeptic. Adjust ε to 0.05, 0.10 or 0.20; the browser recomputes 81 numerical states and matches PDF/ZIP downloads to that parameter.
- **AutoRebuttal:** **Draft responses** reveals separate replies to two reviewers. Click a reviewer to highlight the concern, supporting evidence and corresponding response. Download the responses and evidence ledger. Faithfulness and loophole checks illustrate the released B2/B3 roles.

These are **authored illustrations**, not recorded model runs. The example proposals do not claim verified novelty; the replies do not claim a live quality evaluation. The math case is inexact gradient descent on a positive-definite quadratic, grounded in Boyd and Vandenberghe's [Convex Optimization](https://web.stanford.edu/~boyd/cvxbook/), chapter 9. Numerical checks actually execute in the browser. The three workflows remain independently usable in EAR; the consistent examples do not imply an automatic chain between them.

The ZIP preserves the brief, plan, proof, CSV, v1 and v2 manuscripts, LaTeX, PDF, prepared review, evidence ledger, provenance and `verify.py`. The verifier recomputes every numerical state using Python's standard library. Numerical agreement is not a formal proof certificate.

The UI does not pretend to accept arbitrary directions without model execution. **Get started** creates a shell-quoted live-workflow command for a visitor's own direction and links the setup guide.

## Recorded and executable evidence

The expandable AutoVibeIdea case preserves IDEA-06's recorded novelty change from 8 to 4 and CAUTION → ABANDON after closer prior work. Public excerpts omit full proposals and identifying literature details; the page does not invent them.

Two supplementary panels expose actual offline artifacts. The math fixture exercises rejection, revision, independent-review wiring and version snapshots; its status remains `offline_demo`, `accepted=false`. Rebuttal produces five contracts and a dry-run, without a response-quality result. The HTTP preview can rerun only these fixed offline actions.

Historical charts preserve current-version passes `[3,10,10,12]`, best-version passes `[3,10,12,15]`, denominator 28 completed manuscripts, full population 64 attempts and 630 research calls. The selected G3 slice compares 20.50 against 9.67 calls per historical pass. These unpaired observations have self-selected targets; the stricter retained-vote diagnostic is 1/4 for both strategies. Call counts cover partial machine work. Human-time savings remain unmeasured.

## Portable export

```bash
python3 -m ear demo studio --export workspaces/ear-demo.html
```

Open the single HTML directly in a browser. Figures, data, PDF downloads and ZIP creation are embedded; no external script or model service is used. Existing export files are never overwritten. Rerun controls are available only in the local HTTP preview.

## GitHub Pages

The [Pages workflow](../.github/workflows/pages.yml) exports the same single HTML
into an isolated `workspaces/pages/` directory. Only that directory is published;
private workspaces, source files and local previews are not part of the website.
Pull requests verify and build the export. Deployment runs only on `main`.

A maintainer enables **Settings → Pages → Build and deployment → Source →
GitHub Actions** once. The first successful deployment makes the project page
available at <https://liyingze07-svg.github.io/EffectiveAutoResearch-EAR-/>, with
`?lang=zh` for Chinese. An Actions badge or README link does not by itself confirm
that Pages is enabled.

GitHub Pages serves the static interactions and embedded downloads. Fixed
Python fixture reruns remain available in the local preview. Model-dependent
research continues through the documented CLI workflows.

## Two-minute walkthrough

Show the static inputs and outputs, then the module architecture. In EAR Studio, search for an idea and inspect why branches stop. Switch to math, build the paper, inspect Skeptic and adjust the error level while watching the curve. Finally draft the reviewer responses and click Reviewer 2 to trace its evidence. Download a proposal, PDF and reply to make the outputs tangible. Use the expandable provenance and chart protocol when discussing evidence.
