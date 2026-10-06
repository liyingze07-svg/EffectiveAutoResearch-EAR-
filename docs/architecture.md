# Architecture and workflow boundaries

EAR combines three independently usable research workflows with a shared launcher, demonstrations and local checks. The shared launcher delegates execution to the existing engines. It does not turn their different research processes into one generic prompt.

## Idea discovery: retain the reasoning behind a direction

AutoVibeIdea develops a direction and target venue through literature survey, critical analysis, candidate generation, screening and refinement. The search tools also support UCT-guided best-first candidate expansion and explicit pruning; that interface does not claim a simulated-rollout stage.

| Artifact | Purpose |
| --- | --- |
| `outputs/LANDSCAPE.md` | Literature landscape and research gaps |
| `outputs/SCREENING_RANKED.md` | Candidate comparisons and recommendations |
| `refine-logs/FINAL_PROPOSAL.md` | A proposal draft to discuss and develop |

Read the landscape, then the rankings, then the proposal. Novelty judgments remain limited by retrieval coverage. The public [rescreening example](../autovibeidea/examples/judge-run/README.md) shows a judgment overturned by later evidence. Full operation and artifact details are in the [AutoVibeIdea guide](../autovibeidea/README.md).

## Mathematical research: two loops with different responsibilities

```text
Research direction → seek / novelty → prove ↔ challenge → write / compile
                                              ↑                  ↓
                                              └── revise ← terminal review

Research strategies → evaluation tasks → quality and completion records
         ↑                                         ↓
         └──────── selection / crossover / mutation ┘
```

The research worker chooses actions through a composed goal prompt and skill pool. The supervisor supplies continuation, batches and checkpoints. The terminal reviewer runs separately and binds its verdict to the manuscript version. The current portable terminal gate requires two fresh reviews to reach Weak Accept or better; a worker's self-reported success is insufficient.

The optimizer can vary prompts, skills, worker code and configuration while keeping its terminal reviewer fixed. The current engine exposes a broader strategy interface than the historical report campaign. The report's historic one-of-three Accept rule and selection batches do not measure the current gate's performance.

Natural-language proofs are the main output. Optional final checking can hand an accepted artifact to an external formalizer; a formal proof is not implied by a model-assessor pass. See [engine design](../autonomousmath/docs/ENGINE_DESIGN.md), [evolution](../autonomousmath/docs/EVOLUTION.md) and [final checking](../autonomousmath/docs/FINAL_CHECKING.md).

## Rebuttal: connect each concern to evidence

AutoRebuttal targets EMNLP / ACL Rolling Review workflows. Its 18 stage prompts organize evidence mapping, concern diagnosis, drafting, review and delivery. Four main gates check concern identification, cross-family persuasion, fidelity to evidence and wording that undermines the response. An optional experiment loop has separate pre-experiment and result checks.

The writing loop uses the available evidence by default. New experiment results enter drafting only after passing their checks. Reviewer drafts, the AC comment and the delivery ledger remain distinct artifacts; unresolved concerns remain visible. Cross-family mode uses Codex and DeepSeek, while explicitly selected single-family review is marked separately. The workflow creates local drafts and does not submit them to a conference.

See the [AutoRebuttal guide](../rebuttal/README.md) for the input schema, review gates and complete commands.

## What is shared, and what remains workflow-specific

| Shared | Workflow-specific |
| --- | --- |
| `python3 -m ear` source-checkout entry point | Model setup and research controls |
| Offline demos and environment checks | Output schemas, research state and review semantics |
| Evidence navigation and report release | Restart/continuation behavior |
| Guidance for independent workspaces | Optional tools, integrations and dependencies |

A proposal can inform a math research direction, and a manuscript can supply rebuttal inputs. These are **manual handoffs** today. EAR does not claim a fully automatic pipeline from topic to conference submission.

The technical report's primary objective is to conserve researchers' active time subject to quality and machine-budget constraints. Released measurements concern model judgments and partial machine-work counts. Human-time savings remain a prospective measurement, described in the [report protocol](../docs/technical-report/v6/data/protocol.json).
