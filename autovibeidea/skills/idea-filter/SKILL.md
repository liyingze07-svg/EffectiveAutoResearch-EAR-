---
name: idea-filter
description: "Pre-filter and crystallize research directions before running the full idea-pipeline. Narrows broad interests into 1-3 concrete, well-scoped ideas through constraint-driven exploration, direction deep-dive, and idea crystallization. Use when user says \"filter ideas\", \"narrow directions\", \"choose a direction\", \"screen directions\", \"settle on a topic\", \"help me choose a direction\", \"what should I work on\", or wants to go from vague research interests to a focused, pipeline-ready idea."
argument-hint: "[constraints-and-interests] [-- venue: ICML|NeurIPS|ICLR|AISTATS|all] [-- top: N]"
allowed-tools: Bash(*), Read, Write, Grep, Glob, WebSearch, WebFetch, Agent, mcp__codex__codex, mcp__codex__codex-reply
---

# Idea Filter — Constraint-Driven Direction Discovery & Crystallization

Pre-filter research directions for: **$ARGUMENTS**

## Constants

- **REVIEWER_MODEL** = `gpt-5.4` — External model for exploring directions and narrowing down ideas. (**Model availability depends on your account**: Codex signed in with a ChatGPT account can use only models available to that account; unsupported models return a 400 error. With `--codex-cli`, **do not pass `--model`**; let Codex use its default model. With `--gpt-only`, the model must be available to your OpenAI API key.)
- **DEFAULT_VENUE** = `NeurIPS` — Default target venue when none is specified.
- **MAX_DIRECTIONS** = `5` — Maximum number of broad directions to explore in Phase 1.
- **SURVIVING_DIRECTIONS** = `3` — Number of directions that survive into Phase 2 deep-dive.
- **TOP_IDEAS** = `2` — Number of crystallized ideas to output (overridable via `-- top: N`).

## Overview

This skill is the **pre-step before `/idea-pipeline`**. Its purpose is to prevent the pipeline from wasting time on poorly scoped or ill-fitting directions.

The core insight: running `/idea-pipeline` on a broad direction produces diverse but often unfocused results. This skill first locks down a concrete, well-understood idea — including its main theorem shape, minimal experiments, and risk profile — then generates a **focused pipeline prompt** that constrains each pipeline phase to work on the pre-filtered idea rather than diverging.

```
/idea-filter "constraints"  →  crystallized idea(s)  →  /idea-pipeline "focused prompt"
```

**When to use this skill vs. `/idea-pipeline` directly:**
- Use `/idea-filter` when you have **constraints and interests** but no concrete idea yet (e.g., "low-resource, theory-oriented, CPU-friendly")
- Use `/idea-pipeline` directly when you already have a **specific research topic** (e.g., "ICL generalization bounds under prompt shift")

## Input

1. **`$ARGUMENTS`** — The user's constraints, interests, and preferences. Examples:
   - "An AI topic with substantial theory and equations, CPU-friendly, with top-venue potential"
   - "low-resource theory work on Transformer mechanisms, no GPU needed"
   - "I want to work on conformal prediction: reliable, fast, and easy to take through a complete research cycle"
   - "something publishable at NeurIPS in 6 months, theory-heavy, small experiments"
2. **`-- venue:` directive** — Target venue. Default: `NeurIPS`.
3. **`-- top: N` directive** — Number of crystallized ideas to output. Default: `2`.

### Parsing Logic

1. Extract the user's core constraints from `$ARGUMENTS`. Look for:
   - **Resource constraints**: CPU-only, no GPU, low-resource, single-person, limited compute
   - **Style preferences**: theory-heavy, formula-dense, proof-driven, empirical, systems
   - **Timeline**: fast/quick (< 3 months), medium (3-6 months), long (6-12 months)
   - **Scope**: specific sub-area interests, things to avoid, prior experience
   - **Venue target**: from `-- venue:` or mentioned in text
2. Parse `-- venue:` and `-- top:` from arguments.
3. If constraints are too vague (e.g., just "AI research"), auto-expand by asking the external LLM to propose constraint dimensions the user should consider. But do NOT ask the user — infer reasonable defaults and log the assumptions.

---

## Phase 1: Constraint-Driven Direction Discovery

**Goal**: Given the user's constraints, discover 3-5 broad research directions that are the best fit.

### Step 1.1: Direction Generation via External LLM

Call REVIEWER_MODEL via Codex MCP (`mcp__codex__codex`) with xhigh reasoning effort:

```
mcp__codex__codex:
  config: {"model_reasoning_effort": "xhigh"}
  prompt: |
    You are a senior ML research advisor. The user has the following constraints and preferences:

    === User Constraints ===
    [INJECT PARSED CONSTRAINTS FROM $ARGUMENTS]
    === END ===

    Target venue: [VENUE]

    Recommend [MAX_DIRECTIONS] research directions that best suit the user. Every direction must satisfy all user constraints.

    For each direction, provide:
    1. **Direction Name**: A concise English name
    2. **Why It Fits**: Explain the fit against each user constraint
    3. **Current Activity**: Have top-venue papers advanced this direction in the past 1-2 years (2024-2026)? List 2-3 representative works
    4. **Room for Innovation**: Which theoretical or methodological problems remain unresolved?
    5. **Equation/Theory Density**: How many theorems/proofs does a typical paper contain? (low/medium/high)
    6. **Minimum Resources**: What minimum setup is needed for a submission-ready result?
    7. **Typical Paper Structure**: What does a strong paper in this direction look like? (e.g., "main theorem + lower bound + toy experiments")
    8. **Risks**: What are the most common pitfalls?
    9. **Fit Score**: 1-10 recommendation score considering all constraints

    Rank directions by fit, from highest to lowest.

    Important:
    - Do not recommend directions requiring large-scale GPU training if the user specifies low resources
    - Do not recommend overcrowded directions unless the user has a clear differentiating advantage
    - Every direction must be supported by active papers from the past 2 years; do not recommend inactive niches
    - Prefer directions where small models, synthetic data, or pure theory can yield results
```

**Save the threadId** for follow-up in later phases.

### Step 1.2: Active Research Validation

For each recommended direction, verify its activity with targeted web searches:

1. For each direction, run 2-3 WebSearch queries:
   - `"[direction keywords]" ICML OR NeurIPS OR ICLR 2025 2026`
   - `"[direction keywords]" survey OR tutorial 2024 2025`
   - `"[direction keywords]" open problem OR future work`
2. For the top results, use WebFetch to read abstracts and confirm the direction is genuinely active.
3. Flag any direction where no recent (2024+) top-venue papers are found: "⚠️ Activity not confirmed — may be cooling down."

### Step 1.3: Direction Ranking & Narrowing

Rank all directions by a composite of:
- External LLM's fitness score (50%)
- Confirmed activity from web search (25%)
- Constraint alignment verified by the local agent (25%)

Keep the top SURVIVING_DIRECTIONS (default 3) directions. Log eliminated directions with reasons.

**Codex MCP failure handling**: If `mcp__codex__codex` is unavailable:
1. Fall back to the local agent performing direction discovery directly
2. Use the same prompt structure
3. Augment with additional WebSearch queries to compensate for reduced knowledge breadth
4. Log: "⚠️ Codex MCP unavailable. Direction discovery performed by the local agent (single-model mode)."
5. Continue pipeline — do NOT stop or ask the user.

---

## Phase 2: Direction Deep-Dive & Topic Generation

**Goal**: For each surviving direction, generate 3-5 concrete, publishable topic ideas. Then narrow across all directions to the best ideas overall.

### Step 2.1: Per-Direction Topic Generation

For EACH surviving direction, call the external LLM via `mcp__codex__codex-reply` (continuing the thread from Phase 1):

```
mcp__codex__codex-reply:
  threadId: [threadId from Phase 1]
  config: {"model_reasoning_effort": "xhigh"}
  prompt: |
    Analyze the direction "[DIRECTION NAME]" in depth and generate 3-5 concrete paper topics ready to pursue.

    For each topic, provide:
    1. **Paper Title**: A credible English title resembling an actual paper title
    2. **One-Sentence Description**: What will this paper prove, discover, or solve?
    3. **Core Problem**: Explain the research problem in 1-2 paragraphs
    4. **Main Theorem/Result Shape**: Sketch the theorem statement (informal equations are acceptable)
    5. **Equations and Mathematical Tools**: List the required mathematical toolkit
    6. **CPU-Friendly Approach**: How can experiments run efficiently on CPUs?
    7. **Top-Venue Potential**: Why would reviewers consider this topic valuable?
    8. **Closest Related Work**: 2-3 directly related papers
    9. **Risks and Difficulties**: Where is this topic most likely to get stuck?
    10. **Estimated Timeline**: How long to reach a submission-ready result?

    Quality requirements:
    - Every topic must be concrete enough to write a problem statement immediately
    - Do not merely say "study X"; say "prove that X satisfies Z under conditions Y"
    - Do not recommend low-novelty topics such as "apply method A to domain B"
    - Prefer complete structures such as "upper bound + lower bound + small experiment" or "main theorem + corollary + counterexample"
```

If the `mcp__codex__codex-reply` call fails, fall back to a new `mcp__codex__codex` call (or the local agent if Codex is unavailable). Include the direction context in the prompt.

### Step 2.2: Cross-Direction Novelty Quick-Check

For each generated topic across all directions, run a quick novelty check:

1. WebSearch for the topic title or close paraphrase on arXiv
2. WebSearch for the core mechanism + problem combination
3. Assign status: `LIKELY NOVEL` / `NEEDS DEEPER CHECK` / `ALREADY DONE`
4. Eliminate `ALREADY DONE` topics

### Step 2.3: Cross-Direction Ranking

Pool all surviving topics from all directions. Score each on 5 dimensions (1-10):

| Dimension | Description |
|-----------|-------------|
| **Constraint Fit** | How well does this topic match ALL user constraints? |
| **Theory Density** | How many theorems/proofs can this topic support? |
| **Closure Speed** | How quickly can this produce a complete, submittable paper? |
| **Novelty Signal** | Based on the quick-check, how novel does this appear? |
| **Venue Fit** | How well does this match the target venue's taste? |

**Topic Score** = average of 5 dimensions.

Keep the top topics (up to 2x TOP_IDEAS, so default 4) for crystallization.

---

## Phase 3: Idea Crystallization

**Goal**: For each top topic, produce a fully crystallized idea card — detailed enough to directly feed into `/idea-pipeline` or even to start writing a paper.

### Step 3.1: Deep Crystallization via External LLM

For EACH top topic, call the external LLM:

```
mcp__codex__codex-reply:
  threadId: [threadId from Phase 1]
  config: {"model_reasoning_effort": "xhigh"}
  prompt: |
    Refine the following research topic into a complete idea card.

    Topic: [TOPIC TITLE]
    Core problem: [CORE PROBLEM from Phase 2]

    Provide:

    ## 1. Formal Problem Definition
    Define the problem setup mathematically, including:
    - Input/output spaces
    - Assumptions
    - Target quantity (what to optimize or bound)

    ## 2. Main Theorem Roadmap
    List the anticipated theorem chain:
    - Main Theorem: Formal statement of the core result
    - 1-2 Corollaries: Direct consequences of the main theorem
    - Lower Bound / Impossibility: Establish the sharpness of the main theorem
    - Estimated proof difficulty for each theorem (easy/moderate/hard)

    ## 3. Mathematical Toolkit
    Which mathematical tools are needed? Separate "must know" from "helpful to know".

    ## 4. Minimum Viable Experiments
    - Experiment 1: [description] — What does it validate?
    - Experiment 2: [description] — What does it validate?
    - Experiment 3: [description] — What does it validate?
    - Technology stack: What software/libraries are required?
    - Estimated CPU time: How many hours in total?

    ## 5. Paper Skeleton
    - Section 1 (Introduction): What story does it tell?
    - Section 2 (Problem Setup): Formal definitions
    - Section 3 (Main Results): Main theorem + corollaries
    - Section 4 (Lower Bounds / Impossibility): Tightness discussion
    - Section 5 (Experiments): Validate trends predicted by the theorems
    - Section 6 (Discussion): Limitations + extensions

    ## 6. Risk Register
    - Technical risk: Where might proofs fail? What is the fallback?
    - Novelty risk: Who might scoop this result? How can it be differentiated?
    - Reviewer risk: What objections are most likely? How can they be anticipated?

    ## 7. Execution Roadmap
    Give a week-by-week plan targeting a submission-ready draft within [ESTIMATED TIMELINE].

    ## 8. Required Reading
    List 5-8 essential papers in reading order, with one sentence explaining why each matters.
```

### Step 3.2: Crystallization Validation

For each crystallized idea, the local agent independently validates:

1. **Consistency check**: Does the main theorem shape actually follow from the problem definition?
2. **Scope check**: Is this too big for one paper? If yes, suggest a smaller first version.
3. **Risk reality check**: Are the risk assessments realistic? Add any missed risks.
4. **Constraint re-check**: Does this still satisfy ALL original user constraints?

Flag any issues and annotate the idea card.

---

## Phase 4: Pipeline Prompt Generation

**Goal**: For each crystallized idea, generate a ready-to-use `/idea-pipeline` prompt that constrains the pipeline to work on this specific idea.

### Step 4.1: Generate Focused Pipeline Prompts

For each top idea (TOP_IDEAS, default 2), construct a pipeline prompt following this template:

```
/idea-pipeline "Research topic: [IDEA TITLE].
The goal is not to explore unrelated directions, but to run a full novelty gate, generate same-topic variants, screen them across multiple dimensions, and refine this candidate research direction.

Phase 1 / survey focus:
[SPECIFIC SURVEY INSTRUCTIONS — what to search for, what NOT to repeat, what gaps to map]

Phase 2 / gen focus:
Do not branch into unrelated directions. Generate several submission-ready versions of the same candidate topic, prioritizing the following approaches:
[LIST 4-6 VARIANT AXES derived from the crystallized idea]
Requirements: [STYLE CONSTRAINTS from user, e.g., theory-oriented, extremely lightweight experiments]

Phase 3 / screen focus:
Compare each version on:
[LIST SPECIFIC SCREENING CRITERIA derived from the idea's risk profile]

Phase 4 / refine focus:
Refine only the best 1-2 versions into submission-ready paper skeletons, specifying problem formalization, main theorem roadmap, minimal experiment, novelty risk, and fallback plan.

Overall requirements: [AGGREGATE CONSTRAINTS]" -- venue: [VENUE]
```

### Step 4.2: Generate jobs.sh Entry (Optional)

If the user's project has a `jobs.sh` batch runner, also generate the TASKS entry format:

```
TASKS=(
  '[PIPELINE PROMPT TEXT] ||| [VENUE] ||| [SHORT_NAME]'
)
```

---

## Output

Create the `outputs/` directory if it does not exist:
```bash
mkdir -p outputs
```

### `outputs/FILTER_REPORT.md`

Full report of the filtering process.

```markdown
# Idea Filter Report

**Constraints**: [user's original constraints]
**Venue**: [target venue]
**Date**: [YYYY-MM-DD]
**Directions explored**: N
**Topics generated**: M
**Ideas crystallized**: K

---

## User Constraints Summary

| Constraint | Value |
|-----------|-------|
| Resource | [e.g., CPU-only, no GPU] |
| Style | [e.g., theory-heavy, formula-dense] |
| Timeline | [e.g., < 3 months] |
| Venue | [target venue] |
| Other | [any additional constraints] |

---

## Phase 1: Direction Discovery

### Explored Directions (ranked by fitness)

#### Direction 1: [Name] — Fitness: X/10 ✅ SURVIVED
[Why it fits, activity confirmation, key papers]

#### Direction 2: [Name] — Fitness: X/10 ✅ SURVIVED
[Why it fits, activity confirmation, key papers]

#### Direction 3: [Name] — Fitness: X/10 ✅ SURVIVED
[Why it fits, activity confirmation, key papers]

#### Direction 4: [Name] — Fitness: X/10 ❌ ELIMINATED
[Why eliminated]

#### Direction 5: [Name] — Fitness: X/10 ❌ ELIMINATED
[Why eliminated]

---

## Phase 2: Topic Generation & Cross-Ranking

### All Generated Topics

| Rank | Direction | Topic | Constraint Fit | Theory Density | Closure Speed | Novelty | Venue Fit | Score | Status |
|------|-----------|-------|---------------|---------------|---------------|---------|-----------|-------|--------|
| 1 | ... | ... | 9 | 9 | 8 | 8 | 9 | 8.6 | ✅ CRYSTALLIZE |
| 2 | ... | ... | 8 | 8 | 9 | 7 | 8 | 8.0 | ✅ CRYSTALLIZE |
| ... | | | | | | | | | |

---

## Phase 3: Crystallized Ideas

### Idea 1: [Title]

#### Formal Problem Definition
[formal problem setup]

#### Main Theorem Roadmap
- **Main Theorem**: [statement]
- **Corollary 1**: [statement]
- **Lower Bound**: [statement]

#### Mathematical Toolkit
**Must know**: [list]
**Helpful to know**: [list]

#### Minimum Viable Experiments
1. [Experiment 1]
2. [Experiment 2]
3. [Experiment 3]
- Technology stack: [tools]
- CPU time: [estimate]

#### Paper Skeleton
[section outline]

#### Risk Register
- Technical risk: [description + fallback]
- Novelty risk: [description + mitigation]
- Reviewer risk: [description + prevention]

#### Execution Roadmap
[week-by-week plan]

#### Required Reading
1. [Paper 1] — [why read]
2. [Paper 2] — [why read]
...

---

### Idea 2: [Title]
[same structure]

---

## Phase 4: Pipeline-Ready Prompts

### Prompt for Idea 1

```
/idea-pipeline "[FULL PROMPT]" -- venue: [VENUE]
```

### Prompt for Idea 2

```
/idea-pipeline "[FULL PROMPT]" -- venue: [VENUE]
```

### jobs.sh Entry (if applicable)

```bash
TASKS=(
  '[PROMPT 1] ||| [VENUE] ||| [SHORT_NAME_1]'
  '[PROMPT 2] ||| [VENUE] ||| [SHORT_NAME_2]'
)
```

---

## Recommendation

**First choice**: [Idea title] — [1-2 sentences why this is #1]
**Backup**: [Idea title] — [1-2 sentences why this is backup]

### For the Fastest Results
[Which idea to pick and why]

### To Target the Strongest Venue
[Which idea to pick and why]
```

### `outputs/FILTER_IDEAS.json`

Machine-readable output for downstream consumption:

```json
{
  "constraints": { ... },
  "venue": "NeurIPS",
  "date": "YYYY-MM-DD",
  "crystallized_ideas": [
    {
      "rank": 1,
      "title": "...",
      "direction": "...",
      "thesis": "...",
      "main_theorem_shape": "...",
      "math_tools": ["..."],
      "min_experiments": ["..."],
      "timeline_weeks": N,
      "risk_profile": { "technical": "...", "novelty": "...", "reviewer": "..." },
      "scores": { "constraint_fit": X, "theory_density": X, "closure_speed": X, "novelty": X, "venue_fit": X, "composite": X },
      "pipeline_prompt": "...",
      "reading_list": ["..."]
    }
  ],
  "eliminated_directions": [ ... ],
  "eliminated_topics": [ ... ]
}
```

### Large File Handling

If `Write` fails due to file size, fall back to Bash with a heredoc:
```bash
cat << 'FILTER_EOF' > outputs/FILTER_REPORT.md
[content]
FILTER_EOF
```

---

## Execution Order

1. **Parse input**: Extract constraints, venue, top-N.
2. **Phase 1**: Direction discovery → validate → rank → narrow to SURVIVING_DIRECTIONS.
3. **Phase 2**: Per-direction topic generation → novelty quick-check → cross-direction ranking → narrow to 2x TOP_IDEAS.
4. **Phase 3**: Deep crystallization of each top topic → validation.
5. **Phase 4**: Generate pipeline-ready prompts.
6. **Write outputs**: FILTER_REPORT.md and FILTER_IDEAS.json.

---

## Key Rules

1. **Write all output in English.** Write all analysis, evaluations, and recommendations in FILTER_REPORT.md in English. Send prompts to the external LLM in English.
2. **This is not idea-gen.** This skill **narrows down a direction**, rather than generating divergent ideas. If the user already has a concrete idea, use `/idea-pipeline` directly.
3. **Constraints are hard requirements.** For CPU-only users, recommend no direction requiring GPUs. For a 3-month deadline, do not recommend a 1-year project.
4. **The pipeline prompt is the core deliverable.** The user should be able to paste it directly into `/idea-pipeline` without further changes.
5. **Do not over-expand.** Every phase narrows the scope. Phase 1 narrows unlimited possibilities to 3-5 directions; Phase 2 narrows 3-5 topics per direction to 4 overall; Phase 3 refines 2; Phase 4 produces executable prompts.
6. **Verify research activity.** Every recommended direction must be backed by top-venue papers after 2024. Do not recommend directions that are "theoretically appealing but inactive in practice".
7. **Fully autonomous operation.** Never ask the user questions, present choices, or wait for user input. Make all decisions autonomously using the rules and fallbacks defined in this skill. If ambiguity arises, choose the most reasonable default and log the decision.
8. **Be honest about trade-offs.** Every direction/topic has strengths and weaknesses. State risks and pitfalls explicitly instead of only making positive claims.

## Composing with Other Skills

```
/idea-filter "constraints"  ← you are here  →  /idea-pipeline "focused prompt"
                                                  ↓
                                              /lit-survey → /idea-gen → /idea-screen → /idea-refine
```

- **Output to `/idea-pipeline`**: The pipeline-ready prompts in `outputs/FILTER_REPORT.md` and `outputs/FILTER_IDEAS.json`. The user copies the prompt and runs `/idea-pipeline`.
- **No upstream dependency**: This skill starts from scratch — it does not require any prior outputs.
- **Relationship to `/idea-screen`**: `/idea-filter` does lightweight screening (novelty quick-check, constraint validation). `/idea-screen` does deep multi-dimensional screening (full novelty audit, reviewer simulation, strategic assessment). They are complementary, not redundant.

The idea-filter skill is the **strategic pre-step** that makes the entire pipeline dramatically more efficient. Instead of running a broad pipeline and hoping something good emerges, the user first crystallizes exactly what they want, then sends a surgically targeted prompt through the pipeline.
