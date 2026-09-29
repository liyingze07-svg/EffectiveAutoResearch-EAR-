---
name: idea-filter
description: "Pre-filter and crystallize research directions before running the full idea-pipeline. Narrows broad interests into 1-3 concrete, well-scoped ideas through constraint-driven exploration, direction deep-dive, and idea crystallization. Use when user says \"filter ideas\", \"narrow directions\", \"选方向\", \"筛方向\", \"锁题\", \"帮我定个方向\", \"what should I work on\", or wants to go from vague research interests to a focused, pipeline-ready idea."
argument-hint: "[constraints-and-interests] [-- venue: ICML|NeurIPS|ICLR|AISTATS|all] [-- top: N]"
allowed-tools: Bash(*), Read, Write, Grep, Glob, WebSearch, WebFetch, Agent, mcp__codex__codex, mcp__codex__codex-reply
---

# Idea Filter — Constraint-Driven Direction Discovery & Crystallization

Pre-filter research directions for: **$ARGUMENTS**

## Constants

- **REVIEWER_MODEL** = `gpt-5.4` — 外部模型，用于方向探索与 idea 收敛。（**模型可用性依赖账号**：用 ChatGPT 账号登录的 codex 只能用账号自带模型，指定不支持的模型会被 400 拒绝。走 `--codex-cli` 时**不要传 `--model`**，让 codex 用默认模型；走 `--gpt-only` 时该模型必须对你的 OpenAI API key 可用。）
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
- Use `/idea-filter` when you have **constraints and interests** but no concrete idea yet (e.g., "低资源、偏理论、CPU 友好")
- Use `/idea-pipeline` directly when you already have a **specific research topic** (e.g., "ICL 泛化界 under prompt shift")

## Input

1. **`$ARGUMENTS`** — The user's constraints, interests, and preferences. Examples:
   - "纯 AI 方向，理论公式多，CPU 友好，能冲顶会"
   - "low-resource theory work on Transformer mechanisms, no GPU needed"
   - "我想做 conformal prediction 相关的，要稳、快、容易闭环"
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
    你是一位资深 ML 研究顾问。用户有以下研究约束和偏好：

    === 用户约束 ===
    [INJECT PARSED CONSTRAINTS FROM $ARGUMENTS]
    === END ===

    目标会议: [VENUE]

    请推荐 [MAX_DIRECTIONS] 个最适合用户的研究方向。每个方向必须满足用户的所有约束。

    对于每个方向，请提供：
    1. **方向名称**: 简洁的中英文名称
    2. **为什么适合用户**: 逐条对照用户约束解释为什么这个方向符合
    3. **当前活跃度**: 近 1-2 年（2024-2026）是否有顶会论文在推进？列出 2-3 篇代表性工作
    4. **创新空间**: 这个方向还有哪些未解决的理论/方法问题？
    5. **公式/理论密度**: 这个方向的典型论文有多少定理/证明？(低/中/高)
    6. **最小资源需求**: 做出可投稿成果需要什么最低配置？
    7. **典型论文结构**: 一篇该方向的强论文长什么样？(e.g., "主定理 + 下界 + toy 实验")
    8. **风险点**: 这个方向最容易踩的坑是什么？
    9. **适合度评分**: 1-10，综合所有约束后的推荐度

    请按适合度从高到低排列。

    重要：
    - 不要推荐需要大规模 GPU 训练的方向（如果用户标明低资源）
    - 不要推荐已经过于拥挤的方向（除非用户有明确的差异化优势）
    - 每个方向必须有近 2 年的活跃论文支撑，不要推荐冷门死方向
    - 优先推荐那些"小模型、合成数据、纯理论也能做出成果"的方向
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
    请深入分析方向「[DIRECTION NAME]」，生成 3-5 个可直接开题的具体论文题目。

    对于每个题目，请提供：
    1. **论文标题**: 一个像样的英文标题（像真的论文标题一样）
    2. **一句话描述**: 这篇论文要证明/发现/解决什么
    3. **核心问题**: 用 1-2 段话把研究问题讲清楚
    4. **主定理/主结果长什么样**: 给出定理 statement 的大致形式（可以用伪公式）
    5. **你能堆的公式/数学工具**: 列出需要的数学工具箱
    6. **CPU 可做法**: 实验怎么做才能 CPU 友好
    7. **为什么有顶会潜力**: 为什么审稿人会觉得这个题有价值
    8. **最近相关工作**: 2-3 篇最直接相关的论文
    9. **风险与难点**: 这个题最可能卡在哪里
    10. **预估周期**: 做出可投稿成果需要多久

    质量要求：
    - 每个题目必须足够具体，能直接写 problem statement
    - 不要只说"研究 X"，要说"证明 X 在 Y 条件下满足 Z"
    - 不要推荐"把 A 方法应用到 B 领域"这种低创新度的题
    - 优先推荐能做出"上界 + 下界 + 小实验"或"主定理 + 推论 + 反例"这种完整结构的题
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
    请帮我把以下研究题目精炼成一个完整的 idea 卡片。

    题目: [TOPIC TITLE]
    核心问题: [CORE PROBLEM from Phase 2]

    请输出：

    ## 1. 正式问题定义
    用数学语言写出问题 setup。包括：
    - 输入/输出空间
    - 假设条件
    - 目标量（要优化/界定的东西）

    ## 2. 主定理路线图
    列出你预期的定理链：
    - 主定理 (Main Theorem): 核心结果的 formal statement
    - 推论 1-2 个 (Corollary): 主定理的直接推论
    - 下界/不可能性结果 (Lower Bound / Impossibility): 说明主定理的 sharpness
    - 每个定理的证明难度估计 (容易/中等/困难)

    ## 3. 数学工具箱
    做这个题需要哪些数学工具？按"必须掌握"和"最好会"分类。

    ## 4. 最小可行实验
    - 实验 1: [描述] — 验证什么？
    - 实验 2: [描述] — 验证什么？
    - 实验 3: [描述] — 验证什么？
    - 技术栈: 需要什么软件/库？
    - 预计 CPU 时间: 总共多少小时？

    ## 5. 论文骨架
    - Section 1 (Introduction): 讲什么故事？
    - Section 2 (Problem Setup): 正式定义
    - Section 3 (Main Results): 主定理 + 推论
    - Section 4 (Lower Bounds / Impossibility): 紧性讨论
    - Section 5 (Experiments): 验证定理趋势
    - Section 6 (Discussion): 局限性 + 扩展方向

    ## 6. 风险清单
    - 技术风险: 证明可能卡在哪里？fallback 是什么？
    - 新颖性风险: 最可能被谁 scoop？如何差异化？
    - 审稿人风险: 审稿人最可能的 objection 是什么？如何预防？

    ## 7. 执行路线图
    给出按周的推进计划，目标是在 [ESTIMATED TIMELINE] 内出可投稿初稿。

    ## 8. 必读论文
    列出 5-8 篇必读论文，按阅读顺序排列。每篇写一句话说明为什么要读。
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
/idea-pipeline "研究主题：[IDEA TITLE]。
这次任务的目标不是发散找新方向，而是对这条候选主线做完整的 novelty gate、同题变体生成、多维筛选与最终精炼。

Phase 1 / survey 的重点：
[SPECIFIC SURVEY INSTRUCTIONS — what to search for, what NOT to repeat, what gaps to map]

Phase 2 / gen 的重点：
不要发散到其他方向，只围绕同一候选题生成若干个可投稿版本。优先覆盖以下主线：
[LIST 4-6 VARIANT AXES derived from the crystallized idea]
要求：[STYLE CONSTRAINTS from user, e.g., 偏理论、实验极轻量]

Phase 3 / screen 的重点：
重点比较每个版本的：
[LIST SPECIFIC SCREENING CRITERIA derived from the idea's risk profile]

Phase 4 / refine 的重点：
只精炼最优的 1-2 个版本，形成可投稿的论文骨架，明确 problem formalization、main theorem roadmap、minimal experiment、novelty risk 与 fallback plan。

总体要求：[AGGREGATE CONSTRAINTS]" -- venue: [VENUE]
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

#### 正式问题定义
[formal problem setup]

#### 主定理路线图
- **Main Theorem**: [statement]
- **Corollary 1**: [statement]
- **Lower Bound**: [statement]

#### 数学工具箱
**必须掌握**: [list]
**最好会**: [list]

#### 最小可行实验
1. [Experiment 1]
2. [Experiment 2]
3. [Experiment 3]
- 技术栈: [tools]
- CPU 时间: [estimate]

#### 论文骨架
[section outline]

#### 风险清单
- 技术风险: [description + fallback]
- 新颖性风险: [description + mitigation]
- 审稿人风险: [description + prevention]

#### 执行路线图
[week-by-week plan]

#### 必读论文
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

**首选**: [Idea title] — [1-2 sentences why this is #1]
**备选**: [Idea title] — [1-2 sentences why this is backup]

### 如果你想最快出成果
[Which idea to pick and why]

### 如果你想冲最强会议
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

1. **所有输出使用中文。** FILTER_REPORT.md 中的分析、评估、建议均使用中文撰写。论文标题、技术术语、数学公式可保留英文。发给外部 LLM 的 prompt 使用中文。
2. **这不是 idea-gen。** 这个 skill 的目的是**锁定方向**，不是发散找 idea。如果用户已经有了具体的 idea，应该直接用 `/idea-pipeline`。
3. **约束是硬约束。** 如果用户说 CPU-only，就不要推荐任何需要 GPU 的方向。如果用户说 3 个月，就不要推荐需要 1 年的题目。
4. **Pipeline prompt 是核心产出。** 用户拿到这个 prompt 应该可以直接粘贴到 `/idea-pipeline` 里运行，不需要额外修改。
5. **不要过度发散。** 每个阶段都在收窄，不在扩张。Phase 1 从无限可能收到 3-5 个方向，Phase 2 从每方向 3-5 题收到总共 4 个，Phase 3 精炼到 2 个，Phase 4 生成可执行的 prompt。
6. **活跃度必须验证。** 任何推荐的方向都必须有 2024 年以后的顶会论文支撑。不要推荐"理论上很好但实际上没人做"的方向。
7. **Fully autonomous operation.** Never ask the user questions, present choices, or wait for user input. Make all decisions autonomously using the rules and fallbacks defined in this skill. If ambiguity arises, choose the most reasonable default and log the decision.
8. **Be honest about trade-offs.** 每个方向/题目都有优缺点。不要只说好话，也要明确说明风险和坑。

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
