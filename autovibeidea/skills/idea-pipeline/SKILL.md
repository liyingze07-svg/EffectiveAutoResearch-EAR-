---
name: idea-pipeline
description: "Full idea discovery pipeline: literature survey → idea generation → multi-dimensional screening → deep refinement. Use when user says \"find ideas\", \"idea discovery\", \"full pipeline\", \"find a direction from scratch\", \"end-to-end idea discovery\", or wants the complete workflow from research direction to refined proposal."
argument-hint: "[research-direction] [-- venue: ICML|VLDB|NeurIPS]"
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, WebSearch, WebFetch, Agent, Skill, mcp__codex__codex, mcp__codex__codex-reply, mcp__zotero__*, mcp__obsidian-vault__*
---

# Idea Pipeline: Full Idea Discovery Orchestrator

Orchestrate a complete idea discovery workflow for: **$ARGUMENTS**

## Constants

- **REFINE_TOP_N = 2** — Number of top ideas to refine in Phase 4.
- **REVIEWER_MODEL = `gpt-5.4`** — Pass through to child skills. (**Model availability depends on your account**: Codex signed in with a ChatGPT account can use only models available to that account; unsupported models return a 400 error. With `--codex-cli`, **do not pass `--model`**; let Codex use its default model. With `--gpt-only`, the model must be available to your OpenAI API key.)
- **DEFAULT_VENUE = ICML** — Default venue for screening when `-- venue:` is not specified.

> Override defaults by telling the skill, e.g., `/idea-pipeline "topic" -- venue: NeurIPS`.

## Autonomous Operation

This pipeline runs fully autonomously once invoked. No user interaction is required.

**Logging**: All checkpoint decisions are appended to `outputs/PIPELINE_LOG.md` with timestamps. Review this file to understand the pipeline's autonomous decisions.

**Error handling**: If any phase fails, the error is logged and the pipeline attempts graceful degradation (see individual skill documentation). The pipeline will NOT stop to ask the user.

## State Persistence (PIPELINE_STATE.json)

After EACH phase completes, write/update `outputs/PIPELINE_STATE.json` with the current pipeline state:

```json
{
  "direction": "$ARGUMENTS",
  "venue": "[venue]",
  "current_phase": 2,
  "completed_phases": [1],
  "started_at": "[ISO timestamp]",
  "phase_timestamps": {"1_completed": "[ISO timestamp]"}
}
```

At pipeline START, check if `outputs/PIPELINE_STATE.json` exists:
- If exists AND `direction` matches `$ARGUMENTS` → resume from the next incomplete phase (skip already-completed phases).
- If exists but `direction` differs → start fresh (rename old state file to `outputs/PIPELINE_STATE.json.bak`).
- If not exists → start fresh.

Update `current_phase`, `completed_phases`, and `phase_timestamps` after each phase completes, using the Write tool.

## Overview

This skill chains all 4 sub-skills into a single automated pipeline:

```
/idea-pipeline "research direction"

Phase 1: /lit-survey → landscape map + gaps
Phase 2: /idea-gen → 8-12 ideas, filtered to 4-6
Phase 3: /idea-screen → multi-dimensional screening + ranking
Phase 4: /idea-refine → refined proposal for top ideas
Phase 5: Final report aggregation
```

Each phase builds on the previous one's output. Checkpoint results are logged to `outputs/PIPELINE_LOG.md` and the pipeline auto-continues without user interaction.

## Pre-Flight Check

Do NOT probe or test any tools before starting. Proceed directly to Phase 1.

## Pipeline Detail

### Phase 1: Literature Survey

Invoke `/lit-survey "$ARGUMENTS"` via the Skill tool.

**What this does:**
- Searches arXiv, Google Scholar, Semantic Scholar, local PDFs, Zotero, Obsidian
- Builds landscape map with gap identification matrix
- Outputs: `outputs/LANDSCAPE.md`, `outputs/LANDSCAPE.json`

**Checkpoint 1 — Literature Survey (auto-logged):**

Append to `outputs/PIPELINE_LOG.md`:
```
## [Timestamp] Phase 1 Complete: Literature Survey
- Found N papers, identified M research gaps
- Top themes: [list top 3 themes]
- Gap matrix written to outputs/LANDSCAPE.md
- **Auto-decision**: Proceeding to Phase 2 (Idea Generation) with all identified gaps
```

Then proceed immediately to the next phase. Do NOT ask the user any questions. Do NOT present options. Do NOT wait for confirmation.

### Phase 2: Idea Generation + Filtering

Invoke `/idea-gen "$ARGUMENTS"` via the Skill tool.

**What this does:**
- Reads `outputs/LANDSCAPE.json` from Phase 1
- Brainstorms 8-12 ideas via external LLM (xhigh reasoning)
- Filters by feasibility, novelty quick-check, impact
- Applies the Researcher-Fit Filter (threshold: 12/20)
- Runs anti-pattern check
- Outputs: `outputs/IDEAS_RAW.md`, `outputs/IDEAS_FILTERED.md`

**Checkpoint 2 — Idea Generation (auto-logged):**

Append to `outputs/PIPELINE_LOG.md`:
```
## [Timestamp] Phase 2 Complete: Idea Generation
- Generated X ideas, filtered to Y after researcher-fit checks (threshold 12/20)
- Top ideas: [list titles with researcher-fit scores and unresolved inputs]
- **Auto-decision**: Screening ALL Y filtered ideas in Phase 3
```

Then proceed immediately to the next phase. Do NOT ask the user any questions. Do NOT present options. Do NOT wait for confirmation.

### Phase 3: Multi-Dimensional Screening

Invoke `/idea-screen` for ALL filtered ideas, with the venue parameter.

Parse `-- venue:` from the original `$ARGUMENTS` and pass through. If not specified, use DEFAULT_VENUE.

**What this does:**
- Module A: Novelty assessment (multi-source search + cross-model verification)
- Module B: Venue reviewer simulation (3 reviewers + meta review)
- Module C: Strategic fit assessment (5 dimensions)
- Composite scoring and ranking
- Outputs: `outputs/SCREENING_REPORT.md`, `outputs/SCREENING_RANKED.md`

**Checkpoint 3 — Idea Screening (auto-logged):**

Append to `outputs/PIPELINE_LOG.md`:
```
## [Timestamp] Phase 3 Complete: Idea Screening
- Screened Y ideas for venue [VENUE]
- Ranking: [list top ideas with composite scores]
- Recommendations: [PROCEED/REVISE/REJECT counts]
- **Auto-decision**: Refining top REFINE_TOP_N ideas in Phase 4
```

Then proceed immediately to the next phase. Do NOT ask the user any questions. Do NOT present options. Do NOT wait for confirmation.

### Phase 4: Deep Refinement

For the top REFINE_TOP_N ideas (by composite score from Phase 3):

Invoke `/idea-refine "[idea description + screening results]"` for each.

**What this does:**
- Freezes Problem Anchor
- Extracts logical skeleton
- Iteratively refines via external LLM (up to 5 rounds)
- 7-dimension scoring, threshold 9/10
- Outputs: `refine-logs/FINAL_PROPOSAL.md`, `refine-logs/REFINEMENT_REPORT.md`

**Checkpoint 4 — Idea Refinement (auto-logged):**

Append to `outputs/PIPELINE_LOG.md`:
```
## [Timestamp] Phase 4 Complete: Idea Refinement
- Refined REFINE_TOP_N ideas
- Idea 1: [title] — Score X/10, Verdict: READY/REVISE/RETHINK, Rounds: N/5
- Idea 2: [title] — Score X/10, Verdict: READY/REVISE/RETHINK, Rounds: N/5
- **Auto-decision**: Generating final report in Phase 5
```

Then proceed immediately to the next phase. Do NOT ask the user any questions. Do NOT present options. Do NOT wait for confirmation.

### Phase 5: Final Report

Aggregate all outputs into `outputs/IDEA_DISCOVERY_REPORT.md`:

```markdown
# Idea Discovery Report

**Direction**: $ARGUMENTS
**Date**: [today]
**Venue**: [venue]
**Pipeline**: lit-survey → idea-gen → idea-screen → idea-refine

## Executive Summary
[2-3 sentences: best idea, composite score, refinement verdict, recommended next step]

## Literature Landscape
[summary from Phase 1, with link to full outputs/LANDSCAPE.md]

## Ideas Generated and Filtered
| # | Title | Researcher-Fit Score | Feasibility | Status |
|---|-------|----------|-------------|--------|
[all ideas from Phase 2 with their fate]

## Screening Results (venue: [VENUE])
| Rank | Idea | Novelty | Venue | Strategic | Composite | Recommendation |
|------|------|---------|-------|-----------|-----------|----------------|
[ranking table from Phase 3]

## Refined Proposals

### Idea 1: [title] — RECOMMENDED
- Composite score: X.X/10
- Refinement verdict: READY/REVISE (score: X/10, N rounds)
- Method thesis: [one sentence]
- Key strength: [from screening]
- Key risk: [from screening]
- Proposal: `refine-logs/FINAL_PROPOSAL.md`

### Idea 2: [title] — BACKUP
[similar structure]

## Eliminated Ideas
| Idea | Stage | Reason |
|------|-------|--------|
| ... | Phase 2 (feasibility) | Requires unavailable dataset |
| ... | Researcher-Fit Filter | Score 10/20; evidence access or budget blocker |
| ... | Phase 3 (novelty) | Already published by [paper] |
| ... | Phase 3 (venue) | All reviewers: Reject |

## All Output Files
- `outputs/LANDSCAPE.md` — Literature landscape
- `outputs/LANDSCAPE.json` — Structured landscape data
- `outputs/IDEAS_RAW.md` — All generated ideas
- `outputs/IDEAS_FILTERED.md` — Filtered ideas
- `outputs/SCREENING_REPORT.md` — Full screening report
- `outputs/SCREENING_RANKED.md` — Ranked results
- `refine-logs/FINAL_PROPOSAL.md` — Refined proposal
- `refine-logs/REFINEMENT_REPORT.md` — Refinement process
- `outputs/IDEA_DISCOVERY_REPORT.md` — This report
- `outputs/PIPELINE_LOG.md` — Autonomous decision log
- `outputs/PIPELINE_STATE.json` — Pipeline state for resumption
```

#### Writing the Final Report

1. Ensure directories exist: `mkdir -p outputs/ refine-logs/`
2. Read output files from each phase to extract summaries and data.
3. Write `outputs/IDEA_DISCOVERY_REPORT.md` using the Write tool.
4. **Large file fallback**: If Write fails due to file size, immediately retry using Bash:
   ```bash
   cat << 'REPORT_EOF' > outputs/IDEA_DISCOVERY_REPORT.md
   [content]
   REPORT_EOF
   ```
   Do NOT ask the user for permission — just do it silently.

## Key Rules

- **Write all output in English.** Write all reports (IDEA_DISCOVERY_REPORT.md, PIPELINE_LOG.md), checkpoint logs, idea descriptions, and review summaries in English.
- **Log decisions, never ask.** All checkpoint summaries go to `outputs/PIPELINE_LOG.md`. Never ask the user questions, present options, or wait for confirmation.
- **If a sub-skill fails, log the error and continue with degraded quality.** Append the error details to `outputs/PIPELINE_LOG.md` and proceed to the next phase with whatever data is available. Do not stop the pipeline.
- **Always produce a final report, even if some phases failed.** Mark failed phases clearly in the report with `[PHASE FAILED]` and include the error details.
- **Large file handling**: If the Write tool fails due to file size, immediately retry using Bash (`cat << 'EOF' > file`) to write in chunks. Do NOT ask the user for permission — just do it silently.
- **Don't skip phases.** Each phase filters and validates — skipping leads to wasted effort later.
- **Kill ideas early.** It's better to kill 10 bad ideas in Phase 3 than to refine one and fail.
- **Document everything.** Dead ends are valuable for future reference. Eliminated ideas should always include the reason for elimination.
- **Pass venue parameter through.** Parse `-- venue:` from `$ARGUMENTS` and forward to `/idea-screen`. If not specified, use DEFAULT_VENUE.
- **Update PIPELINE_STATE.json after every phase.** This enables resumption if the pipeline is interrupted.

## Composing

This is the top-level workflow. Individual skills can also be used standalone:

```
/lit-survey "topic"           — just the literature survey
/idea-gen "direction"         — just idea generation
/idea-screen "ideas"          — just screening
/idea-refine "idea"           — just refinement
/idea-pipeline "direction"    ← full pipeline (this skill)
```
