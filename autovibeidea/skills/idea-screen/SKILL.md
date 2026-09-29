---
name: idea-screen
description: "Multi-dimensional screening of research ideas: novelty check + venue reviewer simulation + strategic fit assessment. Use when user says \"screen ideas\", \"evaluate ideas\", \"review ideas\", \"novelty check\", \"查新\", \"筛选idea\", or wants to rank and filter research ideas before committing to execution."
argument-hint: "[ideas-file-or-description] [-- venue: ICML|VLDB|NeurIPS|all]"
allowed-tools: Bash(*), Read, Write, Grep, Glob, WebSearch, WebFetch, Agent, mcp__codex__codex, mcp__codex__codex-reply
---

# Idea Screen — Multi-Dimensional Research Idea Screening

Screen and rank research ideas: **$ARGUMENTS**

## Constants

- **REVIEWER_MODEL** = `gpt-5.4` — 外部评审模型。（**模型可用性依赖账号**：用 ChatGPT 账号登录的 codex 只能用账号自带模型，指定不支持的模型会被 400 拒绝。走 `--codex-cli` 时**不要传 `--model`**，让 codex 用默认模型；走 `--gpt-only` 时该模型必须对你的 OpenAI API key 可用。）
- **DEFAULT_VENUE** = `ICML` — Default target venue when none is specified.
- **COMPOSITE_WEIGHTS** = `{novelty: 0.25, venue: 0.35, strategic: 0.20, feasibility: 0.20}` — Weights for the composite score. Overridable via `-- weights:`.
- **PROCEED_THRESHOLD** = `7.0` — Composite score at or above this triggers a PROCEED recommendation.
- **CAUTION_THRESHOLD** = `5.0` — Composite score between this and PROCEED_THRESHOLD triggers PROCEED WITH CAUTION. Below this triggers ABANDON.

> **外部模型路径（三选一，按环境变量 `CODEX_MODE` 路由）**
> - 未设置 → 优先 `mcp__codex__codex` / `mcp__codex__codex-reply`。**注意 codex CLI ≥0.158.0 已移除 `mcp-server` 子命令**，新版环境下这两个工具必然不可用，直接走下面两条之一，不要视为故障。
> - `CODEX_MODE=codex-cli` → `bash tools/codex_call.sh --thread <thread文件> --output <输出文件> --phase <阶段> --model REVIEWER_MODEL --config '{"model_reasoning_effort":"xhigh"}' --prompt "..."`。新建线程时 thread 文件为空即可，脚本会把 thread_id 写回该文件；后续同线程调用传同一个文件即自动 `resume`。**无需 API key**。
> - `CODEX_MODE=gpt-api` → `bash tools/gpt_call.sh`（同样的参数形态，需 `OPENAI_API_KEY`）。
>
> 三条路径都不可用时，才降级为本地 agent 自评，并在节点上置 `scores.degraded=true`。

## Overview

This skill combines three evaluation modules to screen research ideas before the researcher commits time and resources to execution. Each idea passes through all three modules, producing a composite score and a ranked recommendation.

- **Module A: Novelty Assessment** — Adapted from the ARIS `novelty-check` skill. Systematically verifies whether each idea's core claims are genuinely novel against recent literature.
- **Module B: Venue Reviewer Simulation** — Adapted from the ICML/VLDB multi-reviewer prompt system. Simulates a real review committee (3 reviewers + meta-review) evaluating the idea as if it were a submission to the target venue.
- **Module C: Strategic Fit Assessment** — Deepened from the 4-dimension researcher-fit framework. Evaluates whether the idea is strategically sound for the researcher's long-term trajectory.

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
    你将模拟 [VENUE_NAME] ([VENUE_FULL_NAME]) 的审稿委员会。

    你评审的是一个**研究 Idea**（不是完成的论文）。核心问题是：
    "如果这个 idea 被正确执行，产出的论文能发 [VENUE_NAME] 吗？"

    ## 评审校准标准
    [INJECT CALIBRATION TIERS FROM VENUE PROFILE]

    ## 审稿人画像
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

    请为每位审稿人输出：
    1. **校准层级**: Tier 1/2/3，附理由
    2. **Strengths**: 从该审稿人视角出发的优点（至少 2 个具体点）
    3. **Critical Weaknesses**: 2-3 个具体、可操作的弱点（不要泛泛而谈）
    4. **Verdict**: [从 verdict_options 中选择: Strong Reject / Reject / Weak Reject / Weak Accept / Accept / Strong Accept]
    5. **"怎样才能让我给 Accept"**: 1-2 句话，告诉作者具体需要什么

    然后写 **Meta Review**:
    - 审稿人之间的核心争议（如果有）—— 审稿人之间应该有分歧，不要三人一致
    - 最终裁决: [从 verdict_options 选择]
    - 如果拒稿: 这个 idea 适合什么级别的会议？（e.g., "适合 AAAI/IJCAI" 或 "建议转投 Workshop"）
    - 如果接收: 怎样才能冲击 Best Paper?
    - 执行中的 Top 3 风险（技术风险、实验风险、定位风险）
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

This module deepens the 4-dimension researcher-fit framework (provenance in `README.md`) into a quantified 5-dimension evaluation. The local agent performs this assessment directly — no external LLM call needed.

For EACH idea, evaluate on these 5 dimensions (1-10 each):

### 1. Longevity (1-10)

Is the core problem persistent, or is it a transient fad?

| Score Range | Meaning |
|-------------|---------|
| 1-3 | Likely obsolete within 1 year (e.g., tied to a specific model version or API) |
| 4-6 | Relevant for 2-3 years (e.g., current architectural paradigm) |
| 7-10 | Addresses a fundamental, long-standing problem (e.g., generalization, efficiency, interpretability) |

Ask: "Will researchers still care about this problem in 5 years?"

### 2. Research Roadmap Viability (1-10)

Can this idea grow into a multi-paper research arc?

| Score Range | Meaning |
|-------------|---------|
| 1-3 | One-off finding, no natural follow-up work |
| 4-6 | One clear extension paper possible |
| 7-10 | Opens a new sub-area; 3+ papers are naturally achievable (foundational contribution → extensions → system/application) |

Ask: "After Paper 1, what are Papers 2 and 3?"

### 3. Application Grounding (1-10)

Does the idea connect to real-world needs?

| Score Range | Meaning |
|-------------|---------|
| 1-3 | Pure theoretical curiosity with no foreseeable application |
| 4-6 | Benchmark-only demonstration (e.g., improves CIFAR-10 accuracy) |
| 7-10 | Clear industry or societal application (e.g., healthcare, sustainability, production ML systems) |

Ask: "Who outside academia would care about this result?"

### 4. Execution Uniqueness (1-10)

Does the researcher (or team) have a unique advantage in executing this idea?

| Score Range | Meaning |
|-------------|---------|
| 1-3 | Any competent team could do this equally well; high risk of being scooped |
| 4-6 | Moderate advantage (e.g., some relevant prior work, partial infrastructure) |
| 7-10 | Strong unique position (e.g., proprietary data, unique computational resources, rare domain expertise, established collaboration) |

Ask: "Why should THIS team pursue this, rather than a team at Google/DeepMind/FAIR?"

### 5. Iteration Readiness (1-10)

How fast is the experimental feedback loop?

| Score Range | Meaning |
|-------------|---------|
| 1-3 | Each iteration takes weeks (e.g., large-scale pre-training, human studies) |
| 4-6 | Each iteration takes days (e.g., medium-scale training, moderate compute) |
| 7-10 | Iterations within hours; rapid signal on whether the idea works (e.g., small diagnostic experiments, existing benchmarks, fast prototyping) |

Ask: "How quickly can we know if this idea is working or dead?"

### Strategic Score Calculation

**Strategic Score** = average of all 5 dimension scores (rounded to 1 decimal place).

### Strategic Report (per idea)

```markdown
### Strategic Fit: [Idea Title]
- **Strategic Score**: X.X/10
- **Dimensions**:
  | Dimension | Score | Justification |
  |-----------|-------|---------------|
  | Longevity | X/10 | [1-2 sentences] |
  | Roadmap Viability | X/10 | [1-2 sentences] |
  | Application Grounding | X/10 | [1-2 sentences] |
  | Execution Uniqueness | X/10 | [1-2 sentences] |
  | Iteration Readiness | X/10 | [1-2 sentences] |
- **Strategic recommendation**: [1-2 sentences on whether this is a good bet for the researcher]
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
- **Strategic_Score** = Module C score (average of 5 dimensions, 0-10)
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


### 同步到 `outputs/IDEA_NODES.jsonl`

每个被筛选的 idea，把各维分数写回其节点（schema 见 `docs/IDEA_NODE_SCHEMA.md`）：

```bash
python3 tools/idea_nodes.py update IDEA-0X \
    --set scores.novelty=8.0 --set scores.venue=6.67 \
    --set scores.strategic=7.6 --set scores.feasibility=7.0 \
    --set scores.composite=7.25 \
    --set 'scores.source=<REVIEWER_MODEL> via <codex-mcp|gpt-api|local-selfreview>' \
    --set scores.degraded=<true|false>
```

**`scores.source` 与 `scores.degraded` 是必填项**：外部模型不可用时的自评分（含 Module B 的 0.8x 惩罚）与正常评分不可比，缺少来源标注的分数无法解释。

被判为 ABANDON 的 idea：

```bash
python3 tools/idea_nodes.py update IDEA-0X --set prune.pruned=true \
    --set prune.mask=collision --set 'prune.reason=Module A 发现 <论文> 已做同一机制'
```

`mask` 按主导原因选择：查新撞车 `collision`；可行性/理论验证代价 `not_feasible`；其他沿用 `docs/IDEA_NODE_SCHEMA.md` 的枚举。**被剪节点保留在文件中。**

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
[Full 5-dimension strategic report]

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
- Longevity: X/10 — [1 line]
- Roadmap Viability: X/10 — [1 line]
- Application Grounding: X/10 — [1 line]
- Execution Uniqueness: X/10 — [1 line]
- Iteration Readiness: X/10 — [1 line]

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

1. **所有输出使用中文。** SCREENING_REPORT.md、SCREENING_RANKED.md 中的新颖性评估、审稿人评语、战略分析、Meta Review 均使用中文撰写。论文标题、技术术语可保留英文。审稿人模拟的 prompt 可以用中文发送给外部 LLM。
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
