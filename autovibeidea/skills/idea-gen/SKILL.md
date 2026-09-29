---
name: idea-gen
description: Generate and rank research ideas given a broad direction. Brainstorms 8-12 ideas via external LLM, filters by feasibility, novelty, impact, and a 4-dimension researcher-fit framework. Use when user says "找idea", "brainstorm ideas", "generate research ideas", "想点子", "what can we work on", or wants to explore a research area for publishable directions.
argument-hint: [research-direction]
allowed-tools: Bash(*), Read, Write, Grep, Glob, WebSearch, WebFetch, Agent, mcp__codex__codex, mcp__codex__codex-reply
---

# Research Idea Generator

Generate publishable research ideas for: $ARGUMENTS

## Overview

Given a broad research direction from the user, systematically generate, validate, and rank concrete research ideas. This skill uses an external LLM for divergent brainstorming, then applies multiple filtering layers — feasibility, novelty quick-check, impact estimation, and a 4-dimension researcher-fit evaluation framework — to distill 8-12 raw ideas down to 4-6 high-quality, actionable research directions.

This skill is designed to compose with the `/lit-survey` skill (run first for best results) and feeds into `/idea-screen` and `/idea-refine` downstream.

## Constants

- **REVIEWER_MODEL = `gpt-5.4`** — 用于头脑风暴与评审的外部模型。（**模型可用性依赖账号**：用 ChatGPT 账号登录的 codex 只能用账号自带模型，指定不支持的模型会被 400 拒绝。走 `--codex-cli` 时**不要传 `--model`**，让 codex 用默认模型；走 `--gpt-only` 时该模型必须对你的 OpenAI API key 可用。）
- **MIN_IDEAS = 8** — Minimum number of ideas to generate in the brainstorming phase.
- **MAX_IDEAS = 12** — Maximum number of ideas to generate in the brainstorming phase.
- **FILTER_THRESHOLD = 12** — Minimum composite score (out of 20) on the Researcher-Fit Filter for an idea to survive.
- **SURVIVING_TARGET = 4-6** — Target number of ideas that survive all filtering stages.

> **外部模型路径（三选一，按环境变量 `CODEX_MODE` 路由）**
> - 未设置 → 优先 `mcp__codex__codex` / `mcp__codex__codex-reply`。**注意 codex CLI ≥0.158.0 已移除 `mcp-server` 子命令**，新版环境下这两个工具必然不可用，直接走下面两条之一，不要视为故障。
> - `CODEX_MODE=codex-cli` → `bash tools/codex_call.sh --thread <thread文件> --output <输出文件> --phase <阶段> --model REVIEWER_MODEL --config '{"model_reasoning_effort":"xhigh"}' --prompt "..."`。新建线程时 thread 文件为空即可，脚本会把 thread_id 写回该文件；后续同线程调用传同一个文件即自动 `resume`。**无需 API key**。
> - `CODEX_MODE=gpt-api` → `bash tools/gpt_call.sh`（同样的参数形态，需 `OPENAI_API_KEY`）。
>
> 三条路径都不可用时，才降级为 Claude 自评，并在节点上置 `scores.degraded=true`。

## Workflow

### Phase 1: Landscape Verification (~2 min — NOT a full literature search)

The purpose of this phase is to establish enough context for high-quality idea generation. It is NOT a replacement for `/lit-survey`.

1. **Check for existing landscape artifacts**:
   - Read `outputs/LANDSCAPE.json` if it exists
   - Read `outputs/LANDSCAPE.md` if it exists
   - These files are produced by the `/lit-survey` skill

2. **If landscape files exist**:
   - Verify the research direction in the landscape matches the user's current direction (fuzzy match is acceptable — e.g., "efficient transformers" matches "transformer efficiency")
   - Extract the **Gap Identification Matrix** or equivalent gap listing from the landscape
   - Extract the **key papers** list (titles + one-line summaries)
   - Extract any **open problems** or **future work** themes
   - Store these as `landscape_summary`, `identified_gaps`, and `key_papers` for use in Phase 2

3. **If landscape files do NOT exist** (fallback — abbreviated inline survey):
   - Print a notice: "No landscape files found. Running abbreviated inline survey. For better results, run `/lit-survey [direction]` first."
   - Run 3-5 quick WebSearch queries:
     - `"[direction] survey" site:arxiv.org`
     - `"[direction] benchmark" NeurIPS OR ICML OR ICLR 2024 2025`
     - `"[direction] limitations" OR "future work"`
     - `"[direction]" state-of-the-art`
     - One more query based on a specific sub-aspect of the direction
   - For the top 5-8 results, use WebFetch to read abstracts/introductions
   - Build a **mini landscape map**:
     - Group findings into 2-4 sub-themes
     - List 5-10 key papers (title, year, one-sentence summary)
     - Identify 3-5 gaps or open questions
   - Store as `landscape_summary`, `identified_gaps`, and `key_papers`

4. **Direction specificity check**:
   - **Auto-narrowing for broad directions**: If the user's direction is very broad (e.g., just "NLP" or "computer vision"), do NOT stop to ask. Instead:
     1. Identify the top 3 most promising sub-directions based on the landscape
     2. Generate ideas for each sub-direction (3-4 ideas each)
     3. Merge all ideas into a single pool and apply normal filtering
     4. Log in `outputs/PIPELINE_LOG.md`: "⚠️ Direction was broad, auto-narrowed to: [sub1], [sub2], [sub3]"
   - A good direction is 1-2 sentences specifying the problem, domain, and constraint — e.g., "factorized gap in discrete diffusion LMs" or "sample efficiency of offline RL with image observations"
   - If the direction is broad, auto-narrowing handles it autonomously; the pipeline never stops to ask

### Phase 2: Idea Generation via External LLM (Two-Stage)

This is the creative core of the skill, restructured into two sequential steps: first a **critical analysis** of the landscape, then **critique-anchored idea generation**. This two-stage approach forces ideas to originate from genuine intellectual attacks on the existing literature, rather than extrapolating linearly from it.

#### Phase 2a: Landscape Critique (Critical Thinking)

Open a new Codex thread via `mcp__codex__codex`. This call performs systematic critique — NOT idea generation. Save the `threadId` for Phase 2b.

**Call `mcp__codex__codex`** with:

- **model**: REVIEWER_MODEL (i.e., `gpt-5.4`)
- **config**: `{"model_reasoning_effort": "xhigh"}`
- **prompt**: Construct the following, filling in bracketed sections with data from Phase 1:

```
You are a rigorous ML research critic. Your task is NOT to suggest ideas yet.
Your sole task is to identify the structural weaknesses in the current research
landscape — the kinds of problems that a follow-up paper could exploit.

Research direction: [user's direction from $ARGUMENTS]

Current landscape (from systematic survey):
[paste landscape_summary — either from LANDSCAPE.md or the mini-survey]

Identified gaps (preliminary):
[paste identified_gaps — either the Gap Identification Matrix or the mini-survey gaps]

High-entropy regions (contested claims under comparable conditions):
[paste the 高熵区域 section from outputs/ENTROPY_MAP.json, if it exists — each entry with
its score, stance distribution, and papers. Omit this block entirely if the file does not exist.
NEVER paste claims flagged as 伪冲突嫌疑 (high entropy, low comparability): their disagreement
is likely caused by differing datasets/scales/metrics rather than a genuine field-level conflict.]

Failure modes shared across papers:
[paste failure_modes entries with n_papers >= 2 from outputs/ENTROPY_MAP.json, if it exists.
These are conditions under which multiple methods degrade but nobody has explained why.]

Systematically critique this landscape across FOUR dimensions:

1. **Unverified Assumptions**: What claims does the field accept as true but has never
   directly tested? For each entry: (a) state the assumption, (b) cite which papers
   rely on it, (c) explain why directly testing or refuting it would be publishable.

2. **Incorrectly Generalized Methods**: What methods were proven valid in one specific
   setting (data regime, scale, modality, task type) but are routinely applied to
   other settings where the theoretical justification does not hold? For each entry:
   (a) state the method and its original scope, (b) describe the over-generalization,
   (c) explain what a properly scoped or corrected version would require.

3. **Experimental Design Flaws**: What common experimental protocols in this area have
   fundamental design flaws that could invalidate published conclusions? For each entry:
   (a) describe the flaw precisely, (b) explain what results it may have distorted,
   (c) suggest a corrected experimental design that would re-open the question.

4. **Cross-Domain Misfits**: What problems, methods, datasets, or evaluation metrics
   have been imported from other ML sub-fields (or other sciences) into this area
   WITHOUT verifying that the domain assumptions transfer? For each entry: (a) identify
   the source domain and the target domain, (b) describe the assumption mismatch,
   (c) explain what a correct cross-domain adaptation would require.

Output a numbered "Critique Manifest" covering all four dimensions. Each entry must have:
- [CRITIQUE-ID]: e.g., CRITIQUE-01, CRITIQUE-02, ...
- [Category]: Unverified Assumption / Incorrect Generalization / Experimental Flaw / Cross-Domain Misfit
- [Description]: precise description of the problem (2-4 sentences)
- [Affected Papers/Claims]: which published claims are implicated
- [Why Exploitable]: why addressing this would produce a publishable contribution
```

**After Phase 2a**:
- Save the full response as `outputs/CRITICAL_ANALYSIS.md`. Create `outputs/` if it does not exist.
- Parse the response into a numbered list of critique entries: CRITIQUE-01, CRITIQUE-02, etc.
- **Save the `threadId`** — it will be reused in Phase 2b.

**Phase 2a Codex MCP failure handling**: If `mcp__codex__codex` call fails:
1. Claude performs the landscape critique directly using the same four-dimension prompt structure
2. Write the critique output to `outputs/CRITICAL_ANALYSIS.md` anyway
3. Log: "⚠️ Codex MCP unavailable. Phase 2a (landscape critique) performed by Claude."
4. Since there is no threadId, Phase 2b also becomes a direct Claude call (no thread context). Log this.
5. Continue — do NOT stop or ask the user.

> **GPT-only mode**: If `CODEX_MODE=gpt-api` is set in the environment, substitute
> `mcp__codex__codex` with:
> `bash tools/gpt_call.sh --model REVIEWER_MODEL --config '{"model_reasoning_effort":"xhigh"}' --prompt "..." --output /tmp/phase2a_resp.txt`
> The thread file path is printed to stderr; save it for Phase 2b.

---

#### Phase 2b: Critique-Anchored Idea Generation

Continue the Phase 2a thread via `mcp__codex__codex-reply`. Each idea must be anchored to a specific critique from Phase 2a.

**Call `mcp__codex__codex-reply`** with:

- **threadId**: [saved from Phase 2a]
- **model**: REVIEWER_MODEL (i.e., `gpt-5.4`)
- **config**: `{"model_reasoning_effort": "xhigh"}`
- **prompt**: Construct the following, passing in the Critique Manifest from Phase 2a:

```
Now generate 8-12 concrete research ideas based on the Critique Manifest above.

CRITICAL RULE: Each idea MUST be explicitly anchored to one or more entries from the
Critique Manifest. An idea that does not address any critique is NOT acceptable.
The critique is the intellectual justification for why the idea is worth pursuing.

For each idea, provide:

1. **Title**: A concise, descriptive title (as it would appear on a paper)
2. **Anchored Critique**: Which CRITIQUE-ID(s) does this address? One sentence explaining
   the logical connection between the critique and the proposed investigation.
3. **One-sentence thesis**: The core claim, stated as "We show that X by Y"
4. **Problem it solves**: Which specific gap/critique from the landscape does this address?
5. **Core mechanism**: The key technical insight (not just "apply X to Y")
6. **Why it is non-obvious**: What would a skeptic's first objection be, and why is it wrong?
7. **Theorem/Conjecture Scaffold**: State the core mathematical claim the paper would prove
   or empirically demonstrate, even if informal and incomplete.
   - For method papers: draft the key loss function or optimization objective (use ??? for unknown terms)
   - For theory papers: state the conjecture (e.g., "Conjecture: generalization error ≤ O(d log n / n)")
   - For empirical papers: state the empirical hypothesis as a falsifiable claim
   - Write "N/A" ONLY for purely engineering contributions with no theoretical component
8. **Expected contribution type**: empirical finding / new method / theoretical result / diagnostic / new formulation
9. **Risk level**: LOW / MEDIUM / HIGH (with 1-sentence justification)
10. **Estimated effort**: person-weeks to a publishable result
11. **Closest existing work**: The single most similar paper and the precise delta

Quality criteria (same as before):
- REJECT "apply X to Y" unless the application reveals a genuinely surprising mechanism
- REJECT ideas where the outcome does not matter (if +3% or -3%, who cares?)
- PREFER ideas where a NEGATIVE result is equally publishable
- PREFER ideas that challenge an assumption the field takes for granted
- PREFER ideas with a clear "skeleton experiment" that takes < 1 week
- Each idea must be differentiated from the landscape papers above

Diversity requirements:
- At least 2 ideas should be HIGH risk / high reward
- At least 2 ideas should be LOW risk / solid contribution
- The rest MEDIUM
- At least 50% of ideas must each address a DIFFERENT critique
  (no single critique should account for more than 3 ideas)
```

**After Phase 2b**:
- Parse the response to extract individual ideas into a structured list
- Verify that at least MIN_IDEAS (8) ideas were generated; if fewer, call `mcp__codex__codex-reply` on the same thread asking for additional ideas anchored to under-represented critiques
- Verify that no more than MAX_IDEAS (12) ideas are kept; if more were generated, keep all but note the count
- **The `threadId` from Phase 2a/2b** is the canonical thread for this run — save it for downstream use
- Assign each idea an identifier: `IDEA-01`, `IDEA-02`, etc.

**After assigning identifiers — write the node file**:

```bash
python3 tools/idea_nodes.py init
```

为每个 idea 写一个节点到 `outputs/IDEA_NODES.jsonl`（schema 见 `docs/IDEA_NODE_SCHEMA.md`）：

- `generator.operator`: 锚定批判的用 `critique_anchored`；由高熵区域派生的用 `entropy_region`；由失效模式派生的用 `failure_mode`
- `generator.anchor`: 对应的 `CRITIQUE-ID` / `C<k>` / 失效条件键。**不允许为空**
- `hypothesis.falsifier`: 什么结果会否证这个 idea。写不出来的，说明该 idea 的假设不可否证——退回 Phase 2b 重写
- `closest_work`: `ref` 与 `delta` 必须成对出现

```bash
python3 tools/idea_nodes.py validate      # 必须通过才能进入 Phase 3
```

**去重（在过滤之前）**：

```bash
python3 tools/dedup_ideas.py pairs --top 5
```

该工具只做**廉价的词法/概念重叠标记**，词法重叠与机制重复两个方向都可能不一致。逐对裁定：如果两个 idea 是同一机制的不同表述，执行

```bash
python3 tools/dedup_ideas.py mark IDEA-0X IDEA-0Y --reason "裁定理由"
```

被标记方进入 `status=pruned` / `prune.mask=duplicate`，**不删除**——剪枝记录本身是产物。若裁定为不同机制，不做任何操作，并在 `outputs/PIPELINE_LOG.md` 记一行"已复核 X 组候选重复对，判定为不同机制"。

**Phase 2b Codex MCP failure handling**: If the reply call fails (or no threadId available from Phase 2a fallback):
1. Claude brainstorms directly using the Phase 2b prompt structure and the critique manifest from `outputs/CRITICAL_ANALYSIS.md`
2. Log: "⚠️ Codex MCP unavailable. Phase 2b (idea generation) performed by Claude using critique manifest."
3. Continue — do NOT stop or ask the user.

> **GPT-only mode**: Use `bash tools/gpt_call.sh --thread THREAD_FILE --model REVIEWER_MODEL --prompt "..."` where THREAD_FILE is the path saved from Phase 2a.

### Phase 3: First-Pass Filtering

For each generated idea, perform three quick evaluations. The goal is to eliminate clearly non-viable ideas before investing time in deeper scoring.

#### 3a. Feasibility Check

For each idea, evaluate:

- **Compute requirements**: Estimate GPU-hours needed for the minimum viable experiment. Skip ideas requiring > 1 month of GPU time.
- **Data availability**: Is the required data publicly available or obtainable? Skip ideas requiring proprietary or non-existent datasets.
- **Implementation complexity**: Can this be implemented in a reasonable timeframe by a small team (1-3 researchers)?
- **Dependency risk**: Does this require access to specific models, APIs, or infrastructure that may not be available?

Mark each idea as: `FEASIBLE`, `FEASIBLE WITH CAVEATS`, or `INFEASIBLE`.
Eliminate `INFEASIBLE` ideas. Note the reason for elimination.

#### 3b. Novelty Quick-Check

For each remaining idea, run 2-3 targeted WebSearch queries to check if it has already been done:

- Search for the idea's title or close paraphrase
- Search for the core mechanism + domain combination
- Search for the closest existing work mentioned in the idea + the proposed delta

For each idea, assign a novelty status:
- `LIKELY NOVEL` — No close matches found
- `NEEDS DEEPER CHECK` — Tangentially related work exists, but the exact angle appears unexplored
- `ALREADY DONE` — A paper doing essentially the same thing was found

Eliminate `ALREADY DONE` ideas. Note the paper that already covers it.

#### 3c. Impact Estimation ("So What?" Test)

For each remaining idea, evaluate:

- If the experiment succeeds with a positive result, does it change how people think or work?
- If the experiment produces a negative result, is that equally informative and publishable?
- Is the finding actionable (leads to better methods, new understanding) or just academically interesting?
- Would a reviewer at a top venue find the contribution significant?

Mark each idea as: `HIGH IMPACT`, `MEDIUM IMPACT`, or `LOW IMPACT`.
Eliminate `LOW IMPACT` ideas where neither a positive nor negative result would be interesting.

**After Phase 3**: Typically 8-12 ideas reduce to 5-8 survivors. Record all eliminated ideas and their elimination reasons.

### Phase 4: Researcher-Fit Filter (4-Dimension)

Apply the 4-dimension researcher-fit evaluation framework. This is a structured scoring system that captures dimensions often missed by pure novelty/feasibility analysis.

> Framework provenance: this four-dimension rubric is adapted from a publicly published research-topic-selection methodology. See the acknowledgements section in `README.md`.

For each surviving idea from Phase 3, score on four dimensions (1-5 scale each):

| Dimension | Score (1-5) | Scoring Criteria |
|-----------|-------------|------------------|
| **Longevity** | | Will this topic still be relevant in 3-5 years? Score 5 if it addresses a fundamental question. Score 1 if it rides a transient trend that may be obsolete in 1-2 years. |
| **Passion alignment** | | Does this align with the researcher's stated interests, skills, and existing expertise? If the user has not stated preferences, default to score 3. If they have (e.g., "I work on systems" or "I'm interested in theory"), score accordingly. |
| **Application potential** | | Can this strengthen a paper's motivation with real-world impact? Score 5 if it directly improves a deployed system or addresses a practitioner pain point. Score 1 if it is purely theoretical with no foreseeable application. |
| **Uniqueness** | | Can the researcher make a unique contribution here that others cannot easily replicate? Score 5 if the idea leverages a unique dataset, insight, or methodological strength. Score 1 if any well-funded lab could do this faster. |

**Composite score** = Longevity + Passion + Application + Uniqueness (out of 20).

**Elimination rule**: Ideas scoring below FILTER_THRESHOLD (12/20) are eliminated. Record the scores and the reason (which dimension(s) dragged the score down).

**Dynamic threshold adjustment**: If ALL ideas score below FILTER_THRESHOLD (12/20):
1. Lower the threshold to 10/20
2. Keep the top 3 ideas regardless of score
3. Log: "⚠️ All ideas below threshold 12/20. Lowered to 10/20, keeping top 3."
4. If still no ideas survive at 10/20, keep the single highest-scoring idea and log: "⚠️ Emergency: keeping highest-scoring idea (score: X/20) despite low score"

**After Phase 4**: Target SURVIVING_TARGET (4-6) ideas. If more than 6 survive, keep all but note that the top 6 by composite score are recommended. If fewer than 4 survive, revisit eliminated ideas from Phase 3 that scored `MEDIUM IMPACT` or `FEASIBLE WITH CAVEATS` and re-evaluate with the He framework — some may pass on a second look.

### Phase 5: Anti-Pattern Check

Before finalizing the output, check each surviving idea against four common anti-patterns. This is a quality gate to catch ideas that look good on paper but have structural problems.

For each surviving idea, check:

1. **"Overly trendy"** — If 5+ papers in the landscape already address this exact angle, flag it. The space is crowded and differentiation will be hard.

2. **"Overly niche"** — If 0 papers in the landscape are even tangentially related, flag it. The idea may be too far from the current discourse to get reviewer buy-in, or it may indicate an underdeveloped landscape search.

3. **"A+B stitching"** — If the idea is essentially "combine method A and method B" without a clear new mechanism or insight that explains why the combination is non-trivially better, flag it. This is the most common anti-pattern in mediocre research.

4. **"Scale-dependent"** — If the expected result only holds at a computational scale the researcher cannot reproduce (e.g., "this works at 100B parameters but we can only test at 1B"), flag it. The contribution becomes unverifiable.

**Flagging rules**:
- Flagged ideas get a warning label and a one-sentence explanation
- Flagged ideas are NOT automatically eliminated — the user may disagree with the flag or have additional context
- If an idea has 2+ flags, add a strong caution note
- Display flags prominently in the output

### Phase 5.9: 同步过滤结果到节点文件

每个在 Phase 3-5 被淘汰的 idea，都要更新其节点，使剪枝原因可统计：

```bash
python3 tools/idea_nodes.py update IDEA-0X --set prune.pruned=true \
    --set prune.mask=<mask> --set 'prune.reason=<一句话>'
```

`mask` 取值与淘汰阶段的对应关系：

| 淘汰原因 | mask |
|---|---|
| 查新发现撞车 | `collision` |
| Researcher-Fit < 12/20 | `fit_below_threshold` |
| 可行性不足 / 理论 claim 验不起 | `not_feasible` |
| 与其他 idea 机制重复 | `duplicate` |
| 同一批判下 idea 过多（>3） | `critique_saturated` |

存活 idea 写入 `scores.researcher_fit`，并**必须**同时写 `scores.source`（哪个模型给的分）与 `scores.degraded`（外部模型是否降级为自评）。最后：

```bash
python3 tools/idea_nodes.py validate && python3 tools/idea_nodes.py stats
```

`stats` 若提示"单个证据锚定超过 3 个 idea"，说明多样性约束已被突破，在 `PIPELINE_LOG.md` 中记录。

### Phase 6: Output

Write two output files. Ensure the `outputs/` directory exists before writing (create it if needed).

#### File 1: `outputs/IDEAS_RAW.md`

This file contains ALL generated ideas before any filtering, serving as a complete record.

```markdown
# Generated Research Ideas (Raw)

**Direction**: [research direction from $ARGUMENTS]
**Date**: [today's date]
**Model**: gpt-5.4
**Landscape source**: [LANDSCAPE.md / abbreviated inline survey]
**Ideas generated**: [N]
**Codex thread ID**: [threadId for follow-up]

---

## IDEA-01: [title]
- **Anchored critique**: [CRITIQUE-XX] — [one-sentence connection between critique and idea]
- **Thesis**: We show that X by Y
- **Gap addressed**: [specific gap from landscape, e.g., "G3: No existing work on Z"]
- **Core mechanism**: [the key technical insight]
- **Non-obvious because**: [skeptic's objection + rebuttal]
- **Contribution type**: [empirical finding / new method / theoretical result / diagnostic / new formulation]
- **Theorem scaffold**: [informal conjecture, loss draft, or falsifiable empirical hypothesis — "N/A" for pure engineering]
- **Risk**: [LOW / MEDIUM / HIGH] — [1-sentence justification]
- **Effort**: [N] person-weeks
- **Closest work**: [paper title + authors/year] — delta: [what is specifically different]

---

## IDEA-02: [title]
[same structure]

---

[repeat for all ideas]
```

#### File 2: `outputs/IDEAS_FILTERED.md`

This file contains the filtered, scored, and ranked ideas — the actionable output.

```markdown
# Filtered Research Ideas

**Direction**: [research direction from $ARGUMENTS]
**Date**: [today's date]
**Pipeline**: Generated [X] ideas -> Feasibility filter -> Novelty quick-check -> Impact filter -> Researcher-Fit Filter -> [Y] surviving
**Landscape source**: [LANDSCAPE.md / abbreviated inline survey]
**Codex thread ID**: [threadId for follow-up]

---

## Surviving Ideas (ranked by researcher-fit composite score, descending)

### Rank 1: [title] (IDEA-XX)
- **Anchored critique**: [CRITIQUE-XX] — [one-sentence connection between critique and idea]
- **Thesis**: We show that X by Y
- **Gap addressed**: [specific gap]
- **Core mechanism**: [technical insight]
- **Non-obvious because**: [skeptic's objection + rebuttal]
- **Contribution type**: [type]
- **Theorem scaffold**: [informal conjecture, loss draft, or falsifiable empirical hypothesis — "N/A" for pure engineering]
- **Risk**: [level] — [justification]
- **Effort**: [N] person-weeks
- **Closest work**: [paper] — delta: [difference]
- **He Score**: Longevity [X] + Passion [X] + Application [X] + Uniqueness [X] = [XX]/20
- **Anti-pattern flags**: [none / list of flags with explanations]
- **Quick novelty**: [LIKELY NOVEL / NEEDS DEEPER CHECK]
- **Why this ranks #1**: [1-2 sentences explaining why this is the top recommendation]

---

### Rank 2: [title] (IDEA-XX)
[same structure]

---

[repeat for all 4-6 surviving ideas]

---

## Eliminated Ideas

| # | Idea | Stage | Reason |
|---|------|-------|--------|
| IDEA-XX | [title] | Feasibility | [e.g., Requires unavailable dataset (ImageNet-22k with annotations)] |
| IDEA-XX | [title] | Novelty | [e.g., Already published: "Paper Title" (Author et al., 2025)] |
| IDEA-XX | [title] | Impact | [e.g., Neither positive nor negative result would change practice] |
| IDEA-XX | [title] | He Filter | [e.g., Score 10/20 — Longevity 2 (trend-dependent), Uniqueness 2 (easily replicated)] |

---

## Risk Distribution of Survivors
| Risk Level | Count | Ideas |
|------------|-------|-------|
| HIGH | [N] | [IDEA-XX, IDEA-XX] |
| MEDIUM | [N] | [IDEA-XX, IDEA-XX] |
| LOW | [N] | [IDEA-XX, IDEA-XX] |

---

## Suggested Next Steps
1. Run `/idea-screen` on the top 2-3 ideas for deep multi-dimensional screening
2. Run `/idea-refine` on the #1 ranked idea to iteratively sharpen it
3. If no landscape was available, run `/lit-survey "[direction]"` and re-run `/idea-gen` for better results

---

## Methodology Notes
- Brainstorming model: gpt-5.4 with xhigh reasoning effort
- Filtering pipeline: Feasibility -> Novelty quick-check -> Impact -> Researcher-Fit Filter (threshold: 12/20) -> Anti-pattern check
- Novelty checks are quick (2-3 searches per idea); run `/idea-screen` for deep novelty verification
- Researcher-Fit scores reflect researcher-agnostic assessment unless user provided preference information
```

#### Writing procedure:

1. Ensure the `outputs/` directory exists: `mkdir -p outputs/`
2. Write `outputs/IDEAS_RAW.md` using the Write tool
3. Write `outputs/IDEAS_FILTERED.md` using the Write tool
4. **Large file fallback**: If the Write tool fails due to file size, immediately retry using Bash:
   ```bash
   cat << 'FILEEOF' > outputs/IDEAS_RAW.md
   [content]
   FILEEOF
   ```
   Do NOT ask the user for permission — just do it silently.

## Key Rules

1. **所有输出使用中文。** IDEAS_RAW.md、IDEAS_FILTERED.md 中的 idea 描述、评估理由、过滤原因均使用中文撰写。Idea title、论文标题、技术术语可保留英文。
2. **The user provides a DIRECTION, not an idea.** Your job is to generate the ideas. Do not ask the user "what idea do you want to explore?" — that is your task.

2. **Quantity first, quality second.** Brainstorm broadly in Phase 2, then filter ruthlessly in Phases 3-5. The external LLM should generate freely without over-constraining.

3. **A good negative result is just as publishable as a positive one.** Prioritize ideas where the answer matters regardless of which way it goes. An idea where only one outcome is interesting is a weaker idea.

4. **Don't fall in love with any idea before validating it.** Be willing to kill ideas that don't pass the filters, even if they sound exciting.

5. **"Apply X to Y" is the lowest form of research idea.** Push for deeper questions: Why does X work? When does X fail? What assumption does X make that is wrong?

6. **Include eliminated ideas in the report.** They save future time by documenting what was considered and why it was rejected. A researcher returning to this direction later will benefit from seeing the dead ends.

7. **If the user's direction is too broad, auto-narrow it.** Do not stop or ask the user to clarify. Instead, identify the top 3 sub-directions from the landscape and generate ideas for each (see Phase 1, step 4). Log the auto-narrowing decision to `outputs/PIPELINE_LOG.md`.

8. **Respect the phase boundaries.** Do not skip phases or combine them. Each phase has a distinct purpose and rushing through produces lower-quality output.

9. **Track provenance.** Every claim about the landscape, every novelty assessment, and every gap reference should be traceable back to a specific search result or landscape file entry.

10. **Be transparent about confidence.** If the landscape data is thin (abbreviated inline survey rather than full `/lit-survey`), say so. If a novelty check is inconclusive, say `NEEDS DEEPER CHECK` rather than guessing.

## Composing with Other Skills

This skill is designed to work as part of a larger research idea pipeline:

```
/lit-survey "direction"    -> landscape (run first for best results)
/idea-gen "direction"      <- you are here
/idea-screen               -> deep multi-dimensional screening of top ideas
/idea-refine               -> iterative refinement of top ideas
/idea-pipeline             -> full automated workflow (runs the above in sequence)
```

**Upstream**: `/lit-survey` produces `outputs/LANDSCAPE.json` and `outputs/LANDSCAPE.md` which this skill consumes. Running `/lit-survey` first significantly improves idea quality because the landscape data is more comprehensive.

**Downstream**: `/idea-screen` takes the surviving ideas from `outputs/IDEAS_FILTERED.md` and performs deep multi-dimensional screening (novelty verification, critical review, competitive analysis). `/idea-refine` then iteratively sharpens the top ideas based on screening feedback.
