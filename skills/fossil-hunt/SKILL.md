---
name: fossil-hunt
description: Systematically find high-value "fossil components" in a research domain — long-standing, consensus-layer building blocks that have never been fundamentally questioned but carry hidden improvement potential. Produces a ranked target list with improvement hypotheses for use as input to /idea-gen. Use when user says "where should I look", "find fossil components", "找化石组件", "找盲点", "which components to target", or wants a strategic map before brainstorming ideas.
argument-hint: [research-domain]
allowed-tools: Bash(*), Read, Write, Grep, Glob, WebSearch, WebFetch, Agent, mcp__codex__codex, mcp__codex__codex-reply
---

# Fossil Hunt

在以下研究领域中系统性寻找"化石组件"：$ARGUMENTS

## 核心方法论

"化石组件"是指那些被广泛使用多年、社区默认为最优解、但实际上从未被根本性质疑过的基础模块。它们之所以是高价值靶子，是因为存在**认知套利空间**：社区共识认为它们已经最优，但现实中环境（规模、硬件、算法生态）已经发生了数量级的变化，而组件本身从未被重新审视。

发现路径是从**症状**出发，而非从**组件列表**出发。

---

## Constants

- **REVIEWER_MODEL = `gpt-5.4`** — 用于外部评审的模型。（**模型可用性依赖账号**：用 ChatGPT 账号登录的 codex 只能用账号自带模型，指定不支持的模型会被 400 拒绝。走 `--codex-cli` 时**不要传 `--model`**，让 codex 用默认模型；走 `--gpt-only` 时该模型必须对你的 OpenAI API key 可用。）
- **MIN_TARGETS = 3** — 最终输出的最少靶子数
- **MAX_TARGETS = 8** — 最终输出的最多靶子数
- **CONFIDENCE_THRESHOLD = 2** — 一个靶子至少需要被几条信号线交叉确认才能进入最终列表

---

## Workflow

### Phase 1: Domain Mapping — 竞争层 vs 共识层

**目标**：在指定的研究领域中，区分哪些方向是大家在卷的（竞争层），哪些是大家默认不动的（共识层）。共识层才是化石组件的藏身之处。

1. 用 2-3 次 WebSearch 建立该领域的基本认知：
   - `"[domain] survey 2024 2025 open problems future work"`
   - `"[domain] state-of-the-art benchmark 2025 2026"`
   - `"[domain] architecture components modules standard"`

2. 从搜索结果中识别：
   - **竞争层**：大量论文在卷的方向（e.g., scaling, RLHF, MoE routing, architecture search）
   - **共识层**：被当作胶水代码/标配的模块（e.g., normalization, activation, positional encoding, residual connections, loss function, tokenization, embedding lookup）
   - **计算图中的"关节" vs "肌肉"**：
     - 肌肉 = 承担主要计算的模块（大家盯得很紧）
     - 关节 = 模块之间的连接与转换（被当作不重要的胶水）

3. 输出一个分类表（用于 Phase 2 的搜索聚焦）：
   ```
   竞争层（不搜）: [list]
   共识层候选（重点搜）: [list]
   关节位置（优先级高）: [list]
   ```

**快速判断标准**：如果你跟同行说"我在研究 X 的替代方案"，对方的反应是"为什么要动这个？"——那 X 大概率就在共识层。

---

### Phase 2: 三路信号收集

沿三条独立路线并行收集信号，每条路线都可以产出候选靶子。三条路线互相交叉验证，被多条路线指向的候选靶子置信度更高。

#### 路线 A：症状聚类法（从补丁堆积反推根因组件）

**原理**：当一个组件周围堆满了 workaround，说明问题出在组件本身。补丁越多，底层组件的设计债越重。

执行：
1. 用 2-3 次 WebSearch 搜索该领域的 training tricks、hacks、workaround：
   - `"[domain] training tricks hacks instability workaround 2024 2025"`
   - `"[domain] loss spike gradient explosion clipping warmup 2024 2025"`
   - `"[domain] training recipe stabilization tips 2024 2025"`

2. 对收集到的 tricks 进行聚类，每个 trick 都追问：**这个补丁在修复什么根因？**
   - 例：`gradient clipping` + `learning rate warmup` + `Pre-Norm vs Post-Norm 之争` → 共同根因：残差连接导致的隐状态幅值不稳定

3. 每个根因对应一个候选靶子，标注为 `Signal-A`

#### 路线 B：强原语逆向扫描法（跨维度迁移盲区）

**原理**：一个在某个维度上被验证有效的强原语，往往还没有被系统性地应用到其他维度。Kimi 的核心洞察就是把 attention（在序列维度有效）扫描到了深度维度。

执行：
1. 识别该领域中已被验证的**强原语**（已经成熟、overhead 可控）：
   - 常见强原语：attention、gating（门控）、routing（MoE路由）、normalization flow、sparse selection、learned interpolation

2. 对每个强原语，列举它目前被应用的维度：
   ```
   原语: Attention
   已应用维度: 序列(token之间) ✓
   未应用维度: 深度(层之间)? 特征/通道之间? 注意力头之间? 词表维度?
   ```

3. 每个"?"处都是一个候选靶子，标注为 `Signal-B`

   额外搜索确认这些"?"是否真的未被探索：
   - `"[primitive] across [dimension] transformer 2024 2025 depth-wise channel-wise"`

#### 路线 C：Ablation 挖矿法（意外敏感性信号）

**原理**：顶会论文的 ablation study 是社区对共识层的"无意探测"。当作者发现去掉某个"标准"组件效果出乎意料地差（隐藏瓶颈）或意料之外地好（可替换），这就是直接信号。

执行：
1. 用 2-3 次搜索寻找包含 ablation 意外发现的论文：
   - `"[domain] ablation study surprising sensitivity normalization activation 2024 2025"`
   - `"[domain] ablation removing [component] unexpected significant impact 2024 2025"`
   - `"[domain] component analysis removing layernorm softmax residual 2024 2025"`

2. 对每个"意外"发现分类：
   - **意外地重要**（移除后性能大幅下降）→ 这个组件是瓶颈，改进它可能有大收益
   - **意外地不重要**（移除后性能几乎不变）→ 这个组件可能是历史遗留，可以被更好的东西替换

3. 每个意外发现对应一个候选靶子，标注为 `Signal-C`

---

### Phase 3: 候选靶子验证

对每个候选靶子（来自路线 A/B/C）进行三项验证，判断是否是真正值得投入的高价值靶子。

#### 3a. 尺度失配验证

**核心问题**：这个问题是否随模型/数据规模增大而加剧？

- 搜索该组件在大模型 vs 小模型中的表现差异
- 如果问题会随规模自动放大 → 高价值（行业趋势会自动暴露问题）
- 如果问题在小规模就存在且规模无关 → 中等价值
- 如果问题只在小规模出现、大模型已经不是问题 → 低价值，排除

#### 3b. 跨领域类比验证

**核心问题**：在其他领域（信号处理、控制论、神经科学、运筹学），这个"固定"操作是否已经有成熟的"自适应"版本？

- 在 ML 中某个组件的"固定"版本，在其他领域往往已经有"自适应"方案
- 如果跨领域有成熟解 → 说明改进方向是有理论支撑的，可行性高
- 如果跨领域也没有好的解 → 说明这可能是一个更基础的困难问题

搜索示例：`"adaptive [component-concept] control theory signal processing 2020 2021 2022"`

#### 3c. 时机成熟度验证

**核心问题**：痛点是否足够尖锐？修复工具是否已经成熟？

两个条件同时满足才算时机成熟：
1. **痛点已足够尖锐**：社区已经广泛感知到这个问题，但还没有正确归因（正在归因 = 竞争激烈，归因完成但没解决 = 好时机）
2. **修复原语已经成熟**：用来替换旧组件的新原语（如 attention、gating）已经在其他地方被验证可用，overhead 可控

最好的时机是：**痛点正在被广泛感知但尚未被正确归因**。

---

### Phase 4: 外部 LLM 交叉审查

用外部 LLM 对候选靶子列表进行独立评审，验证是否遗漏了重要候选靶子，并对每个靶子的改进假设进行质量评估。

**调用 `mcp__codex__codex`**，参数：

- **model**: REVIEWER_MODEL (i.e., `gpt-5.4`)
- **config**: `{"model_reasoning_effort": "xhigh"}`
- **prompt**:

```
You are a senior ML researcher with deep expertise in [domain from $ARGUMENTS].

I have identified the following "fossil component" candidates — long-standing, consensus-layer building blocks that may have hidden improvement potential due to environmental drift (scale changes, new hardware, new algorithmic primitives becoming available):

[paste the candidate list from Phases 2-3, with their signal sources and validation results]

Research domain: [domain]

Your tasks:
1. **Coverage check**: Are there high-value fossil components I missed? List up to 3 additional candidates with the signal that makes you think they're worth targeting. Be specific: cite the concrete symptom, scale failure mode, or cross-domain analogue.

2. **Quality review** of each candidate I found: For each candidate, provide:
   - Confidence (HIGH / MEDIUM / LOW) that this is a genuinely underexplored target
   - The single strongest argument FOR pursuing this
   - The single strongest argument AGAINST (most common failure mode or reason it may have already been tried)
   - Whether the "improvement hypothesis" is mechanistically sound

3. **Ranking**: Rank all candidates (including any you added) by expected impact × feasibility. Justify the top 3 placements briefly.

Evaluation criteria:
- HIGH value: Scale-sensitive problem + cross-domain analogue exists + timing is right + social consensus treats it as "solved"
- LOW value: Already crowded space / requires compute we can't access / improvement requires something that doesn't exist yet

Be critical. Many "fossil" hunts fail because the component WAS updated (just not widely cited) or because the update IS hard for a fundamental reason.
```

**失败处理**：如果 Codex MCP 不可用，跳过此阶段，在输出中标注 "⚠️ Phase 4 skipped: Codex MCP unavailable. External cross-check not performed."，继续后续流程。

---

### Phase 5: 改进算子映射

对每个通过验证的靶子，系统性地套用改进算子，生成具体的改进假设。改进算子是历史成功工作中反复出现的模式：

| 算子 | 含义 | 适用信号 |
|------|------|---------|
| **Static → Adaptive** | 固定操作变为输入相关的（最常见的模式，Kimi 的 AttnRes 就是这个） | 操作与输入内容无关 |
| **Global → Local** | 全局操作变为局部/稀疏的 | 全局操作在长序列/大规模下开销太高 |
| **Local → Global** | 局部操作引入全局信息 | 局部操作无法捕获长程依赖 |
| **Independent → Coupled** | 原本独立的单元引入交互 | 多个独立单元处理的信息有相关性 |
| **Single-scale → Multi-scale** | 单一粒度变为多粒度操作 | 现象在不同尺度上有不同特性 |
| **Uniform → Selective** | 均匀处理变为选择性处理 | 不同位置/特征重要性差异很大 |

对每个靶子，选出最有理论依据的 1-2 个算子，生成具体的改进假设句（格式："将 [组件] 中的 [固定操作] 替换为 [自适应机制]，使其从 [静态特性] 变为 [动态特性]"）。

---

### Phase 6: 验证指标设计

对每个最终靶子，明确**正确的验证指标**。

历史经验表明：Kimi 的核心论证不是"我在某个 benchmark 上高了几个点"，而是"同样的 loss 我少用 20% 算力"——这是一个 **scaling 论证**。在小规模实验中应关注：

- **Loss-vs-compute 曲线的斜率变化**（核心指标）
- 而非绝对 benchmark 分数（容易被各种因素稀释）

对每个靶子指定：
- 最小可行实验设计（skeleton experiment，< 1 周可完成）
- 用什么指标验证（优先 scaling exponent，而非 top-1 accuracy）
- 应该在什么规模上验证（足够小以快速迭代，足够大以见到规模效应）

---

### Phase 7: 输出

确保 `outputs/` 目录存在，写入以下文件。

#### File 1: `outputs/FOSSIL_TARGETS.md`

```markdown
# Fossil Hunt Report: [domain]

**Date**: [today]
**Domain**: [domain from $ARGUMENTS]
**Signal sources**: Symptom clustering (A) + Primitive scan (B) + Ablation mining (C) + External LLM review (D)
**Candidates identified**: [N total]
**Final targets**: [M after validation]

---

## 方法论简介

本报告基于"化石组件"方法论，专注于找到深度学习领域中长期被默认为最优但从未被根本质疑的基础组件——即认知套利空间最大的地方。

搜索路径：共识层组件 + 关节位置 → 三路信号验证（症状聚类 / 强原语逆向扫描 / Ablation挖矿）→ 尺度失配 × 跨领域类比 × 时机成熟度三重验证 → 改进算子映射

---

## Domain Map: 竞争层 vs 共识层

### 竞争层（大量人在卷，不是我们的目标）
- [list]

### 共识层（被默认为最优，是我们的搜索空间）
- [list]

### 关节位置（计算图中的连接/转换模块，优先级最高）
- [list]

---

## Top [M] Fossil Targets（按综合置信度排序）

---

### Target #1: [组件名]

**信号来源**: [Signal-A/B/C] × [validation results]
**综合置信度**: HIGH / MEDIUM
**外部LLM评分**: HIGH / MEDIUM / LOW

#### 核心问题诊断
- **化石症状**: [具体的补丁堆积 / 尺度失配 / 固定性描述]
- **隐含假设**: [当初设计时的假设是什么？为什么当时合理？]
- **假设何时被打破**: [哪些环境变化使得原假设不再成立]
- **尺度敏感性**: [问题是否随规模加剧？具体证据]
- **跨领域类比**: [其他领域的对应"自适应"方案是什么？]
- **时机判断**: [痛点尖锐度 + 修复工具成熟度]

#### 改进假设
- **算子**: [Static→Adaptive / Global↔Local / ...]
- **改进假设**: 将 [组件] 中的 [固定操作] 替换为 [自适应机制]，使其从 [静态特性] 变为 [动态特性]
- **Drop-in 可行性**: [是否可以直接替换，不改变接口]

#### 最小验证实验
- **Skeleton experiment**: [< 1 周可完成的实验设计]
- **验证指标**: [Loss-vs-compute 曲线斜率 / scaling exponent / ...]
- **推荐验证规模**: [模型大小 × token数]

#### 反方论点
- [为什么这个方向可能不奏效？最强的反驳论点是什么？]

---

### Target #2: [组件名]
[同上结构]

---

[重复至所有 M 个 targets]

---

## Eliminated Candidates

| 候选 | 信号来源 | 排除原因 |
|------|---------|---------|
| [组件] | Signal-A | [e.g., 尺度不敏感：问题在大模型中反而消失] |
| [组件] | Signal-B | [e.g., 已被 2025 年某论文解决，只是没有广泛传播] |

---

## 建议的下一步

1. 用 Top-1 target 作为方向，运行 `/lit-survey "[target] rethinking improvement adaptive 2024 2025"` 做深入文献调研
2. 然后运行 `/idea-gen "[target] — [改进假设]"` 生成具体 idea
3. 如果你想直接从这份报告生成 idea，可以直接运行 `/idea-gen` 并在 direction 中引用本报告的 Top-1 改进假设

---

## 方法论注记

- **为什么从症状出发而不是从组件列表出发**: 暴力枚举组件是低效的，症状是组件有问题的直接证据
- **为什么用 scaling exponent 而非 benchmark 分数**: 绝对分数依赖于太多因素；scaling exponent 的变化才说明基础组件确实被改进了
- **认知套利空间的本质**: 环境变化速度 >> 组件重新评估速度。2015-2017 年的设计选择是在完全不同的硬件和规模约束下做出的。
```

#### Writing procedure:
1. 确保 `outputs/` 目录存在：`mkdir -p outputs/`
2. 用 Write tool 写入 `outputs/FOSSIL_TARGETS.md`
3. 若 Write 失败（文件过大），改用 Bash heredoc 写入，不需要询问用户

---

## Key Rules

1. **所有输出使用中文。** 报告内容使用中文，组件名、技术术语、论文标题保留英文。

2. **从症状出发，不要从组件列表出发。** 不要先列出所有可能的组件然后逐个问"这个能不能改"——那是暴力搜索，不是方法论。

3. **三路信号交叉验证是核心。** 只被一条路线发现的候选靶子置信度低（除非外部 LLM 强烈推荐）。被两条或以上路线独立指向的靶子优先级高。

4. **时机判断是差异化关键。** 一个组件有问题还不够，还需要修复它的工具已经成熟、且目前还没有人正在修复它。发现一个 2025 年刚被人发表的"化石组件"改进是没有意义的。

5. **反方论点必须认真对待。** 每个靶子都必须包含一个最强的反驳论点。只有正向论据的靶子是不完整的。如果反方论点非常强（例如"这个组件在大模型中已经被自动解决了"），就把该靶子排除。

6. **Drop-in 可行性决定影响力。** 改进越接近 drop-in replacement（不改变接口，可以直接替换），实际采用率越高，论文影响力越大。在设计改进假设时优先考虑 drop-in 方案。

7. **验证指标要用 scaling exponent，不要用绝对 benchmark。** 基础组件的改进应该体现在 loss-vs-compute 曲线的斜率上，而不是某个 benchmark 上的点。

8. **不要报告显而易见的东西。** 如果一个"候选靶子"出现在了近期大量论文的标题中（说明它已经是竞争层了），不要把它列为化石组件。

---

## 在 Pipeline 中的位置

```
/fossil-hunt "domain"     <- 你在这里（找到高价值靶子区域）
/lit-survey "target"      -> 针对具体靶子做深入文献调研
/idea-gen "target"        -> 生成具体 idea
/idea-screen              -> 多维筛选
/idea-refine              -> 迭代精炼
/idea-pipeline            -> 一键全流程
```

`/fossil-hunt` 的产出（`FOSSIL_TARGETS.md` 中的改进假设）可以直接作为 `/lit-survey` 和 `/idea-gen` 的输入方向，使这两个技能的搜索更加精准。
