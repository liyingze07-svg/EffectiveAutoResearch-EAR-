---
name: idea-screen
description: "Multi-dimensional screening of research ideas: novelty check + venue reviewer simulation + strategic fit assessment. Use when user says \"screen ideas\", \"evaluate ideas\", \"review ideas\", \"novelty check\", \"check prior work\", \"filter ideas\", or wants to rank and filter research ideas before committing to execution."
argument-hint: "[ideas-file-or-description] [-- venue: ICML|VLDB|NeurIPS|all]"
allowed-tools: Bash(*), Read, Write, Grep, Glob, WebSearch, WebFetch, Agent, mcp__codex__codex, mcp__codex__codex-reply
---

# Idea Screen — Multi-Dimensional Research Idea Screening

Screen and rank research ideas: **$ARGUMENTS**

## Constants

- **REVIEWER_MODEL** = `gpt-5.4` — External review model. (**Model availability depends on your account**: Codex signed in with a ChatGPT account can use only models available to that account; unsupported models return a 400 error. With `--codex-cli`, **do not pass `--model`**; let Codex use its default model. With `--gpt-only`, the model must be available to your OpenAI API key.)
- **DEFAULT_VENUE** = `ICML` — Default target venue when none is specified.
- **COMPOSITE_WEIGHTS** = `{novelty: 0.25, venue: 0.35, strategic: 0.20, feasibility: 0.20}` — Weights for the composite score. Overridable via `-- weights:`.
- **PROCEED_THRESHOLD** = `7.0` — Composite score at or above this triggers a PROCEED recommendation.
- **CAUTION_THRESHOLD** = `5.0` — Composite score between this and PROCEED_THRESHOLD triggers PROCEED WITH CAUTION. Below this triggers ABANDON.

> **External model routes (choose one, routed by `CODEX_MODE`)**
> - Unset → prefer `mcp__codex__codex` / `mcp__codex__codex-reply`. **Note: Codex CLI ≥0.158.0 removed the `mcp-server` subcommand**. In newer environments these two tools are unavailable; use one of the routes below instead of treating this as an error.
> - `CODEX_MODE=codex-cli` → `bash tools/codex_call.sh --thread <thread-file> --output <output-file> --phase <phase> --model REVIEWER_MODEL --config '{"model_reasoning_effort":"xhigh"}' --prompt "..."`. For a new thread, leave the thread file empty; the script writes the thread_id into it. Pass the same file on later calls to automatically `resume` that thread. **No API key required**.
> - `CODEX_MODE=gpt-api` → `bash tools/gpt_call.sh` (same argument format; requires `OPENAI_API_KEY`).
>
> Only when all three routes are unavailable, fall back to local-agent self-evaluation and set `scores.degraded=true` on the node.

## Overview

This skill combines three evaluation modules to screen research ideas before the researcher commits time and resources to execution. Each idea passes through all three modules, producing a composite score and a ranked recommendation.

- **Module A: Novelty Assessment** — Adapted from the ARIS `novelty-check` skill. Systematically verifies whether each idea's core claims are genuinely novel against recent literature.
- **Module B: Venue Reviewer Simulation** — Adapted from the ICML/VLDB multi-reviewer prompt system. Simulates a real review committee (3 reviewers + meta-review) evaluating the idea as if it were a submission to the target venue.
- **Module C: Strategic Fit Assessment** — Checks whether a precise research claim can be evaluated with accessible evidence, an achievable budget and the user's stated constraints.

The final output is a ranked list of ideas with per-idea breakdowns, composite scores, and actionable recommendations.

## Input

1. **`$ARGUMENTS`** — Either:
   - Direct idea descriptions (one or more ideas inline), or
   - A file reference (e.g., `outputs/IDEAS_FILTERED.md` from `/idea-gen`)
2. **`-- venue:` directive** — Target venue for Module B. Valid values: `ICML`, `VLDB`, `NeurIPS`, `all`. Default: `ICML`.
3. **`-- weights:` directive** — Override composite weights (e.g., `-- weights: novelty=0.3, venue=0.3, strategic=0.2, feasibility=0.2`).
4. **`outputs/LANDSCAPE.json`** — If available from a prior `/lit-survey` run, read it for novelty cross-referencing. If not found, skip silently.

### Parsing Logic

1. If `$ARGUMENTS` points to a file path, read and parse that file. Extract each idea as a separate entity (look for headings, numbered lists, or `### Idea N:` patterns).
2. If `$ARGUMENTS` is inline text, treat each paragraph or clearly delimited section as a separate idea.
3. Parse `-- venue:` from the arguments. If absent, set `TARGET_VENUE = DEFAULT_VENUE`.
4. Parse `-- weights:` from the arguments. If absent, use `COMPOSITE_WEIGHTS`.
5. Try to read `outputs/LANDSCAPE.json`. If found, load the paper list for cross-referencing in Module A.

---

## Module A: Novelty Assessment

Adapted from the ARIS `novelty-check` skill. For EACH idea, execute Phases A through D.

### Phase A: Extract Key Claims

1. Read the idea description carefully.
2. Identify 3-5 core technical claims that would need to be novel:
   - What is the **method**?
   - What **problem** does it solve?
   - What is the **mechanism** (the key technical insight)?
   - What makes it **different from obvious baselines**?
3. Write each claim as a single declarative sentence.

### Phase B: Multi-Source Literature Search

For EACH core claim, search using ALL available sources:

1. **Web Search** (via `WebSearch`):
   - Search arXiv, Google Scholar, Semantic Scholar
   - Use specific technical terms from the claim
   - Try at least 3 different query formulations per claim (e.g., synonyms, broader/narrower terms, different orderings)
   - Include year filters for 2024-2026
   - Specifically check: ICLR 2025/2026, NeurIPS 2025, ICML 2025/2026
2. **Cross-reference against `LANDSCAPE.json`**: If `outputs/LANDSCAPE.json` was loaded, check whether any papers already found in Stage 1 (lit-survey) overlap with the current claim. Skip re-fetching those — use the cached metadata. Flag any overlapping papers for detailed comparison.
3. **Read abstracts**: For each potentially overlapping paper found in steps 1-2, use `WebFetch` to retrieve the abstract and (where possible) the related work or introduction section. This is critical for determining whether the overlap is superficial or fundamental.

**Search failure handling**:
- If a WebSearch query fails: retry once with a reformulated query
- If retry also fails: skip that claim's web-based verification
- If ALL web searches fail: assess novelty based solely on the external LLM's knowledge (Phase C) and the existing LANDSCAPE.json data
- Log any failures: "⚠️ Web search unavailable for claim [X]. Novelty assessment based on LLM knowledge only."

### Phase C: Cross-Model Verification

Call REVIEWER_MODEL via Codex MCP (`mcp__codex__codex`) with xhigh reasoning effort:

```
mcp__codex__codex:
  config: {"model_reasoning_effort": "xhigh"}
  prompt: |
    I need to verify the novelty of a research idea.

    Proposed idea: [IDEA DESCRIPTION]

    Papers found that may overlap:
    [LIST EACH PAPER: title, authors, year, venue, abstract summary]

    Core claims to verify:
    [LIST EACH CLAIM]

    For each core claim, answer THREE questions:
    1. Has this EXACT mechanism been published? (cite specific paper + section if yes)
    2. Has a CLOSELY RELATED mechanism been published that achieves the same goal through a different path? (cite + explain degree of overlap)
    3. Would a reviewer at [TARGET_VENUE] consider this sufficiently novel? (yes/no + reasoning)

    Overall novelty assessment:
    - Score: 0-10 (where 10 = completely unprecedented, 0 = already published verbatim)
    - Recommendation: PROCEED / PROCEED WITH CAUTION / ABANDON
    - Key differentiator (what, if anything, makes this unique)
    - Suggested positioning to maximize novelty perception at the target venue
```

> **GPT-only mode**: If `CODEX_MODE=gpt-api` is set in the environment, substitute the `mcp__codex__codex` call above with:
> `bash tools/gpt_call.sh --model REVIEWER_MODEL --config '{"model_reasoning_effort":"xhigh"}' --prompt "[prompt text]" --output /tmp/screen_novelty_resp.txt`
> For follow-up calls, add `--thread /tmp/screen_thread.id` to continue the conversation.

### Phase D: Novelty Report (per idea)

Produce the following structured report for each idea:

```markdown
### Novelty: [Idea Title]
- **Score**: X/10
- **Recommendation**: PROCEED / PROCEED WITH CAUTION / ABANDON
- **Core Claims**:
  1. [Claim 1] — Novelty: HIGH/MEDIUM/LOW — Closest: [paper title, year]
  2. [Claim 2] — Novelty: HIGH/MEDIUM/LOW — Closest: [paper title, year]
  3. [Claim 3] — Novelty: HIGH/MEDIUM/LOW — Closest: [paper title, year]
- **Closest Prior Work**:

| Paper | Year | Venue | Overlap | Key Difference |
|-------|------|-------|---------|----------------|
| ...   | ...  | ...   | ...     | ...            |

- **Key differentiator**: [what makes this unique, if anything]
- **Suggested positioning**: [how to frame the contribution to maximize novelty perception]
```

### Important Rules for Module A

- Be **BRUTALLY honest** — false novelty claims waste months of research time.
- "Applying X to Y" is **NOT novel** unless the application reveals surprising insights or requires non-trivial adaptation.
- Check both the **method** AND the **experimental setting** for novelty.
- If the method is not novel but the **finding** would be novel, say so explicitly.
- Always check the most recent **6 months** of arXiv — the field moves fast.
- If a paper is found that is nearly identical, do not soften the blow. State it plainly: "This has been done."

---

## Module B: Venue Reviewer Simulation

This is the key innovation of the screening skill. It adapts the ICML/VLDB multi-reviewer prompt system to evaluate **ideas** (not finished papers), answering the core question: "If this idea is executed correctly, would the resulting paper be accepted at the target venue?"

### How It Works

1. Read the venue profile from `venue-profiles/{VENUE}.md` (e.g., `venue-profiles/ICML.md`). If the file does not exist, fall back to the generic profile below.
2. Extract from the profile: calibration tiers (what constitutes top/solid/weak work), reviewer profiles (personas, accept/reject criteria), and verdict options.
3. Inject these into a single external LLM prompt that simulates 3 reviewers and a meta-reviewer.

### Venue Selection Logic

- User specifies `-- venue: ICML` → use ICML profile.
- User specifies `-- venue: VLDB` → use VLDB profile.
- User specifies `-- venue: NeurIPS` → use NeurIPS profile.
- User specifies `-- venue: all` → run against ALL available venue profiles, produce comparative results.
- Not specified → default to `DEFAULT_VENUE` (ICML).

### Fallback Generic Profile

If no venue profile file is found, use this generic "top ML venue" profile:

**Calibration Tiers:**
- **Tier 1 (Top work)**: New paradigm, non-trivial theoretical guarantees, dominant experimental results across domains. Attitude: "strict admiration" — acknowledge strength but probe for deep flaws.
- **Tier 2 (Solid but incremental)**: Interesting idea, reasonable execution, but incremental advance over existing work. Attitude: "skeptical scrutiny" — challenge whether this is truly venue-worthy.
- **Tier 3 (Flawed/trivial)**: Simple combination of existing techniques, weak baselines, no real insight. Attitude: "unsparing critique" — identify why this adds no value.

**Reviewer Profiles:**
- Reviewer 1: The Applied Researcher (efficiency, scalability, real-world impact)
- Reviewer 2: The Empiricist (experimental rigor, baselines, reproducibility)
- Reviewer 3: The Theoretician (novelty, mathematical depth, insight)

**Verdict Options:** Strong Reject, Reject, Weak Reject, Weak Accept, Accept, Strong Accept

### The Screening Prompt

For EACH idea, call the external LLM:

```
mcp__codex__codex:
  model: REVIEWER_MODEL
  config: {"model_reasoning_effort": "xhigh"}
  prompt: |
    You will simulate the review committee of [VENUE_NAME] ([VENUE_FULL_NAME]).

    You are reviewing a **research idea** (not a completed paper). The key question is:
    "If this idea is executed correctly, could the resulting paper be accepted at [VENUE_NAME]?"

    ## Review Calibration Criteria
    [INJECT CALIBRATION TIERS FROM VENUE PROFILE]

    ## Reviewer Profiles
    [INJECT REVIEWER PROFILES FROM VENUE PROFILE]

    === IDEA ===
    Title: [title]
    Thesis: [one-sentence thesis]
    Problem: [gap addressed]
    Core Mechanism: [key technical insight]
    Contribution Type: [empirical/method/theory/diagnostic]
    Closest Work: [paper + delta, from Module A]
    Novelty Score: [X/10, from Module A]
    === END IDEA ===

    For each reviewer, provide:
    1. **Calibration Tier**: Tier 1/2/3, with justification
    2. **Strengths**: At least 2 specific strengths from that reviewer's perspective
    3. **Critical Weaknesses**: 2-3 specific, actionable weaknesses (not generic remarks)
    4. **Verdict**: [Choose from verdict_options: Strong Reject / Reject / Weak Reject / Weak Accept / Accept / Strong Accept]
    5. **"What would make me accept"**: 1-2 sentences telling the authors exactly what is needed

    Then write a **Meta Review**:
    - Main disagreements among reviewers (if any); reviewers should disagree, not give three identical opinions
    - Final verdict: [Choose from verdict_options]
    - If rejected: What venue tier would suit this idea? (e.g., "Suitable for AAAI/IJCAI" or "Consider a workshop")
    - If accepted: What would make it a Best Paper contender?
    - Top 3 execution risks (technical, experimental, positioning)
```

> **GPT-only mode**: If `CODEX_MODE=gpt-api` is set in the environment, substitute the `mcp__codex__codex` call above with:
> `bash tools/gpt_call.sh --model REVIEWER_MODEL --config '{"model_reasoning_effort":"xhigh"}' --prompt "[prompt text]" --output /tmp/screen_venue_resp.txt`

**Codex MCP failure handling**: If `mcp__codex__codex` is unavailable:
1. Fall back to the local agent performing the venue reviewer simulation directly
2. Use the exact same prompt (venue profile injection, 3 reviewers + meta review)
3. Log: "⚠️ Codex MCP unavailable. Venue simulation performed by the local agent (self-review mode — reduced independence)."
4. Apply a 0.8x penalty to the venue score to account for reduced objectivity
5. Continue pipeline — do NOT stop or ask the user.

### Score Mapping (Verdicts to Numeric)

Convert each reviewer's verdict to a numeric score:

| Verdict | Score |
|---------|-------|
| Strong Reject | 1 |
| Reject | 3 |
| Weak Reject | 4 |
| Weak Accept | 6 |
| Accept | 8 |
| Strong Accept | 10 |

**Venue Score** = average of 3 reviewer verdict scores (rounded to 1 decimal place).

---

## Module C: Strategic Fit Assessment

The local agent checks the research plan directly; no external LLM call is needed.
Start with the claim, the available inputs, an estimate of the minimum convincing
study or proof, and the user's explicit requirements. Do not require an industry
application, a multi-paper roadmap or exclusive team resources. A pure-theory
proposal can qualify through precise proof obligations and accessible mathematical
inputs.

For each idea, score four checks from 1 to 10:

| Check | 1-3: unresolved blocker | 4-6: plausible but incomplete | 7-10: supported execution plan |
|-------|------------------------|------------------------------|--------------------------------|
| **Falsifiability** | No precise claim or identifiable failure condition | Claim is stated; decisive test or proof obligation needs sharpening | Explicit assumptions and a diagnostic, counterexample search or proof obligation can distinguish success from failure |
| **Evidence access** | Essential data, baselines, sources or mathematical inputs cannot be obtained | Named inputs exist but access/preparation is still uncertain | Required inputs are accessible, and collection or verification can be reproduced |
| **Budget completion** | Minimum convincing result exceeds the user's stated resources | A smaller study or proof milestone seems achievable; iteration costs are uncertain | Time/compute/funding estimates, a first decisive check and a stopping condition fit the stated budget |
| **User constraint fit** | Conflicts with a stated capability, interest or scope requirement | Compatible with known constraints, or user preferences/capabilities are unspecified | Explicit user interests and capabilities match the task; required learning and tooling have been included |

For each score, cite the plan detail or user statement that supports it. If an
input is unknown, assign a provisional 5 and identify what must be established
before execution; do not infer a personal preference, expertise or permission.
Known inaccessible evidence or a violated user constraint remains a blocker even
if the weighted composite is high. Recommend resolving it or reducing scope before
execution.

### Strategic Score Calculation

**Strategic Score** = average of the four check scores (rounded to 1 decimal place).
The `strategic` field and 0-10 scale remain unchanged for downstream compatibility.

### Strategic Report (per idea)

```markdown
### Strategic Fit: [Idea Title]
- **Strategic Score**: X.X/10
- **Dimensions**:
  | Dimension | Score | Justification |
  |-----------|-------|---------------|
  | Falsifiability | X/10 | [claim and decisive test/proof obligation] |
  | Evidence access | X/10 | [accessible inputs and unresolved access needs] |
  | Budget completion | X/10 | [minimum result, resource estimate and stopping condition] |
  | User constraint fit | X/10 | [explicitly stated constraints; unknowns remain provisional] |
- **Strategic recommendation**: [execute, resolve a named blocker, or reduce scope; explain why]
```

---

## Composite Scoring

After all 3 modules complete for each idea, compute the composite score:

```
COMPOSITE = (
    COMPOSITE_WEIGHTS.novelty    * Novelty_Score    +   # 0-10 from Module A
    COMPOSITE_WEIGHTS.venue      * Venue_Score      +   # 0-10 from Module B
    COMPOSITE_WEIGHTS.strategic  * Strategic_Score   +   # 0-10 from Module C
    COMPOSITE_WEIGHTS.feasibility * Feasibility_Score    # 0-10 carried from idea-gen
)
```

Where:
- **Novelty_Score** = Module A score (0-10)
- **Venue_Score** = Module B score (average of 3 reviewer verdicts, mapped to numeric, 0-10)
- **Strategic_Score** = Module C score (average of four research-plan checks, 0-10)
- **Feasibility_Score** = Carried from the `/idea-gen` output. If not available (e.g., ideas were provided directly), the local agent estimates feasibility on a 0-10 scale based on: computational requirements, data availability, timeline, and implementation complexity.

Default weights: `novelty=0.25, venue=0.35, strategic=0.20, feasibility=0.20`

Override with: `-- weights: novelty=0.3, venue=0.3, strategic=0.2, feasibility=0.2`

### Recommendation Thresholds

| Composite Score | Recommendation | Action |
|-----------------|----------------|--------|
| >= 7.0 (PROCEED_THRESHOLD) | **PROCEED** | Move to `/idea-refine` for detailed development |
| 5.0 - 6.9 (CAUTION to PROCEED range) | **PROCEED WITH CAUTION** | Address specific weaknesses first; consider `/lit-survey` on flagged sub-topics |
| < 5.0 (below CAUTION_THRESHOLD) | **ABANDON** | Document for future reference; do not invest further effort |

**All-ABANDON fallback**: If ALL ideas score below CAUTION_THRESHOLD (5.0):
1. Do NOT terminate the pipeline
2. Select the top 2 ideas by composite score, regardless of absolute score
3. Override their recommendation to "PROCEED WITH CAUTION"
4. Log: "⚠️ No ideas scored above 5.0. Keeping top 2 (scores: X.X, X.X) as best available options."
5. Continue to idea-refine — the refinement process may improve these ideas.

---

## Execution Order

1. **Parse input**: Extract all ideas, venue, weights.
2. **Load context**: Read `outputs/LANDSCAPE.json` if available.
3. **For each idea**:
   a. **Module A** (Novelty Assessment) — must complete first, as Module B needs the novelty score and closest prior work.
   b. **Module B** (Venue Reviewer Simulation) — runs after Module A completes for this idea. Uses novelty score and closest work as input.
   c. **Module C** (Strategic Fit Assessment) — can run concurrently with Module B (no dependency on Module B output).
4. **Compute composite scores** for all ideas.
5. **Rank ideas** by composite score (descending).
6. **Write outputs**.

When screening multiple ideas, Module A for different ideas can run concurrently. The constraint is: for a single idea, Module A must finish before Module B starts (since Module B's prompt includes the novelty score and closest prior work from Module A).

---

## Output

Create the `outputs/` directory if it does not exist:
```bash
mkdir -p outputs
```


### Synchronize to `outputs/IDEA_NODES.jsonl`

For each screened idea, write dimension scores back to its node (schema: `docs/IDEA_NODE_SCHEMA.md`):

```bash
python3 tools/idea_nodes.py update IDEA-0X \
    --set scores.novelty=8.0 --set scores.venue=6.67 \
    --set scores.strategic=7.6 --set scores.feasibility=7.0 \
    --set scores.composite=7.25 \
    --set 'scores.source=<REVIEWER_MODEL> via <codex-mcp|gpt-api|local-selfreview>' \
    --set scores.degraded=<true|false>
```

**`scores.source` and `scores.degraded` are required**: Self-evaluation when the external model is unavailable (including Module B's 0.8x penalty) is not comparable to normal scoring. Scores without provenance cannot be interpreted.

For ideas judged ABANDON:

```bash
python3 tools/idea_nodes.py update IDEA-0X --set prune.pruned=true \
    --set prune.mask=collision --set 'prune.reason=Module A found that <paper> already uses the same mechanism'
```

Choose `mask` by the dominant reason: prior-work collision → `collision`; feasibility/theory-validation cost → `not_feasible`; otherwise use the enums in `docs/IDEA_NODE_SCHEMA.md`. **Keep pruned nodes in the file.**

### `outputs/SCREENING_REPORT.md`

Full detailed report with per-idea breakdown across all 3 modules.

```markdown
# Screening Report

**Direction**: [research direction]
**Venue**: [target venue]
**Date**: [YYYY-MM-DD]
**Ideas screened**: N
**Composite weights**: novelty=X, venue=X, strategic=X, feasibility=X

## Executive Summary

[2-3 paragraphs summarizing the screening results. How many ideas passed? What are the top recommendations? Any surprises?]

## Per-Idea Reports

### Idea 1: [Title] — [PROCEED/CAUTION/ABANDON]

#### Module A: Novelty Assessment
[Full Phase D novelty report]

#### Module B: Venue Reviewer Simulation ([VENUE])
[Full 3-reviewer + meta-review output]

#### Module C: Strategic Fit Assessment
[Full research-plan fit report, including evidence and unresolved inputs]

#### Composite Score
| Component | Score | Weight | Weighted |
|-----------|-------|--------|----------|
| Novelty | X/10 | 0.25 | X.XX |
| Venue | X/10 | 0.35 | X.XX |
| Strategic | X/10 | 0.20 | X.XX |
| Feasibility | X/10 | 0.20 | X.XX |
| **Composite** | | | **X.XX** |

**Recommendation**: PROCEED / PROCEED WITH CAUTION / ABANDON

---

### Idea 2: [Title] — [PROCEED/CAUTION/ABANDON]
[repeat structure]

---

[repeat for all ideas]
```

### `outputs/SCREENING_RANKED.md`

Concise ranked summary for quick reference and handoff to downstream skills.

```markdown
# Screening Results: Ranked Ideas

**Direction**: [direction]
**Venue**: [venue]
**Date**: [YYYY-MM-DD]
**Ideas screened**: N

## Rankings

| Rank | Idea | Novelty | Venue Score | Strategic | Feasibility | Composite | Recommendation |
|------|------|---------|-------------|-----------|-------------|-----------|----------------|
| 1    | ...  | 8.5     | 7.2         | 8.0       | 7.5         | 7.8       | PROCEED        |
| 2    | ...  | 7.0     | 6.8         | 7.5       | 8.0         | 7.2       | PROCEED        |
| 3    | ...  | 6.0     | 5.5         | 6.0       | 7.0         | 6.0       | CAUTION        |
| 4    | ...  | 4.0     | 3.5         | 5.0       | 6.0         | 4.4       | ABANDON        |

## Detailed Per-Idea Reports

### Rank 1: [Title] — PROCEED

#### Module A: Novelty
- Score: X/10
- Key differentiator: [what makes it unique]
- Closest prior work: [paper, year, delta]

#### Module B: Venue Simulation ([VENUE])
- Reviewer 1 ([persona]): [Verdict] — [1-line summary]
- Reviewer 2 ([persona]): [Verdict] — [1-line summary]
- Reviewer 3 ([persona]): [Verdict] — [1-line summary]
- Meta-review: [Final verdict] — [1-line summary]
- Top risk: [the single biggest execution risk]

#### Module C: Strategic Fit
- Falsifiability: X/10 — [claim and decisive test/proof obligation]
- Evidence access: X/10 — [accessible inputs and unresolved access needs]
- Budget completion: X/10 — [minimum result, estimate and stopping condition]
- User constraint fit: X/10 — [explicit constraints or provisional unknowns]

---

### Rank 2: [Title] — PROCEED
[repeat structure]

---

[repeat for all ideas, in rank order]

## Next Steps

### For PROCEED ideas:
- Run `/idea-refine` to develop detailed research plans, experimental designs, and paper outlines.

### For PROCEED WITH CAUTION ideas:
- Run `/lit-survey` on the specific sub-topics flagged as weak by the reviewers.
- Address the critical weaknesses identified in Module B before proceeding.
- Re-screen after improvements.

### For ABANDON ideas:
- Documented here for future reference.
- May revisit if the landscape changes (new tools, new datasets, paradigm shifts).
- Consider whether a sub-component of the idea could be extracted and developed independently.
```

### Large File Handling

If `Write` fails due to file size, fall back to Bash with a heredoc:
```bash
cat << 'SCREENING_EOF' > outputs/SCREENING_REPORT.md
[content]
SCREENING_EOF
```

---

## Key Rules

1. **Write all output in English.** Write novelty assessments, reviewer comments, strategic analysis, and meta-reviews in SCREENING_REPORT.md and SCREENING_RANKED.md in English. Send reviewer-simulation prompts to the external LLM in English.
2. **Module A must complete before Module B** for each idea — the novelty score and closest prior work are injected into the venue simulation prompt.
2. **Module C has no dependencies** on A or B — it can run concurrently with Module B.
3. **Be BRUTALLY honest in novelty assessment.** False novelty claims waste months. If someone has done this, say so plainly.
4. **The venue simulation should feel like a real review committee.** Reviewers should DISAGREE sometimes. A unanimous verdict (especially unanimous accept) should be rare and reserved for genuinely outstanding ideas.
5. **If no venue profile file is found**, fall back to the generic "top ML venue" profile described above. Never fail because a profile file is missing.
6. **All scores are on a 0-10 scale.** Round composite scores to 1 decimal place.
7. **Feasibility score**: If not available from `/idea-gen` output, estimate it based on: computational requirements, data availability, timeline to first results, and implementation complexity.
8. **Large file handling**: If `Write` fails, use Bash with a heredoc. The screening report can be long for multiple ideas.
9. **Never invent papers.** If the literature search finds nothing overlapping, say so — but also flag that the idea might be in a niche area where absence of results could mean lack of interest rather than novelty.
10. **Check both method AND experimental setting** for novelty. A new method on a standard benchmark is more novel than a standard method on a new benchmark.
11. **Fully autonomous operation.** Never ask the user questions, present choices, or wait for user input. Make all decisions autonomously using the rules and fallbacks defined in this skill. If ambiguity arises, choose the most reasonable default and log the decision.

## Composing with Other Skills

```
/lit-survey → /idea-gen → /idea-screen  ← you are here  → /idea-refine
```

- **Input from `/lit-survey`**: `outputs/LANDSCAPE.json` — paper database for novelty cross-referencing.
- **Input from `/idea-gen`**: `outputs/IDEAS_FILTERED.md` — candidate ideas with feasibility scores.
- **Output to `/idea-refine`**: `outputs/SCREENING_RANKED.md` — ranked ideas with detailed assessments, ready for refinement.

The screening skill is the critical quality gate in the pipeline. Its purpose is to prevent the researcher from investing weeks into an idea that is either not novel, would not survive peer review, or is strategically unsound. Be rigorous. Be honest. Save the researcher's time.
