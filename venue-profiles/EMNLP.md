# Venue Profile: EMNLP

## Venue Metadata
- name: EMNLP
- full_name: Conference on Empirical Methods in Natural Language Processing (2026)
- type: NLP
- acceptance_rate: ~22-25% (main conference); Findings ~15% additional
- verdict_options: [Strong Reject, Reject, Weak Reject, Weak Accept, Accept, Strong Accept]
- allows_revision: false (single review cycle, ARR-style rebuttal)

## EMNLP 2026 Theme Context

EMNLP 2026 主题强调以下评审导向（影响 reviewer 期望）：

1. **Rethinking progress in NLP**：仅靠 leaderboard 上 1-2 分提升已不被视为足够 contribution；reviewer 倾向问"这真的是进步吗？"
2. **Real-world impact, trustworthiness, robustness**：toy benchmark 上的改进若不能映射到部署场景，会被打折
3. **Longitudinal behavior**：模型行为随训练 / 数据 / 时间漂移的研究受重视
4. **Humans vs models generalization**：把人类与模型的泛化模式做对照分析的工作处于 hot zone
5. **Multilinguality, fairness, value pluralism**：跨语言、跨群体的不均衡是 senior reviewer 常用的 reject lever
6. **CoT faithfulness, agent collaboration, evaluation methodology**：EMNLP 2025 outstanding/best paper 中占比上升

## Calibration Tiers

### Tier 1: Top Work
- characteristics:
  - 提出对 NLP 评估范式的**结构性重构**（不只是新 benchmark），并通过实验**推翻**至少一个被广泛接受的隐含假设
  - Empirical 工作必须包含**人类 baseline 或人类对照**，并展示 model-human gap 的 pattern 而非单一数字
  - 跨多个模型族（闭源 + 开源 + 不同规模）展示一致或反直觉的现象
  - 提供**可证伪的 falsifiable claim**（"X 能力在条件 C 下系统性失败"，而非"X 提升了 Y%"）
  - 理论与实验有干净映射（每条 claim 都对应一个具体可复现实验）
- attitude: "严格的肯定（rigorous endorsement）"——承认贡献，但会苛求是否真的"重构理解"，而不是"再加一个维度"

### Tier 2: Solid-Incremental
- characteristics:
  - 提出新的 perturbation set / probe / metric，但是核心论点是"我们发现 LLM 在 X 上不 robust"——这在 EMNLP 已是大量 prior work 的 message
  - 仅在 1-2 个 task family 上展示，缺乏跨任务通用性证据
  - 没有人类对照或人类对照只是简单 accuracy 数字
  - taxonomy / framework paper，但 taxonomy 本身没有产生 testable predictions
- attitude: "怀疑的细查（skeptical scrutiny）"——逐条问"这一点和 prior work [X] 区别在哪？"

### Tier 3: Flawed/Trivial
- characteristics:
  - "Apply X to Y" 类工作（比如把已有 perturbation 套到新 task）
  - 单纯报告"某模型在某 setting 下表现差"，但没有 mechanism explanation
  - 用 closed-source API 跑全部实验、不可复现
  - 把 robustness 等同于 perturbation accuracy，未触及 invariance 的语义层面
- attitude: "严格的底线审查（strict threshold review）"——给出 Reject 并列明 5 处主要缺陷

## Reviewer Profiles

### Reviewer 1: The Methodologist (评估方法论审稿人)
- focus: 评估协议本身是否站得住——metric 定义、人类 baseline、统计显著性、confound control
- accept_when:
  - 有 explicit human baseline 与 calibrated comparison
  - Metric 是 well-defined 的（有 mathematical 或 operational definition，不是"我们觉得好的就叫 generalization"）
  - 至少 3 seeds + 显著性检验 + ablation 区分 confound（model size vs training data vs decoding）
  - 评估方法本身被 release 为可复用工具
- reject_when:
  - 对"什么算 generalize"只给定性描述
  - 全部用 closed-source API，他人无法复现
  - 用一个 test set accuracy 数字代替整个 generalization 概念
  - 把 prompt 变化导致的 variance 当 noise 而不是 signal

### Reviewer 2: The Theoretical-NLP Reviewer (理论 NLP 审稿人)
- focus: 概念框架的严谨性与对认知科学 / 形式语义学 / linguistics 文献的尊重
- accept_when:
  - taxonomy 或 framework 引用 Hupkes 2020 (compositional generalization), Lake & Baroni, Fodor & Pylyshyn 等经典工作并表明立场
  - 区分 "能力"（competence）vs "表现"（performance）vs "robustness"
  - 对 invariance / equivariance / counterfactual / causal 等概念使用准确，不滥用
  - 提出的概念能产生 non-trivial prediction（即从 framework 推出至少一个非平凡的实验结果）
- reject_when:
  - 把 generalization, robustness, OOD, transfer 当同义词混用
  - 对 "causal" 一词使用 loose（无 do-calculus / counterfactual / intervention 操作化）
  - 忽视心理语言学 / 认知科学 prior work
  - 提出的 "novel framework" 实质是 prior work 的换名

### Reviewer 3: The Empirical-Practitioner Reviewer (产业实践审稿人)
- focus: 这个研究是否对真正使用 LLM 的人有用——是部署 / 安全 / 产品视角
- accept_when:
  - perturbation 类型与真实用户行为有映射（paraphrase 对应自然语言变体，不是合成攻击）
  - 跨语言 / 跨文化 / 跨领域评估包含真实部署场景代表
  - findings 给出 actionable advice（"在 X 情境下应该警惕 Y"）
  - 包含 frontier models（GPT-5/Claude/Gemini 这一代）而不只是 GPT-3.5 / LLaMA-2
- reject_when:
  - 全部在 toy / synthetic 任务上做
  - 只跑 1-2 个开源小模型，未触及当前 frontier
  - 提出的"问题"在生产中已被 RAG / verifier / refusal 解决
  - 没有讨论 cost-aware tradeoff（如果建议每个 query 跑 100x perturbation 验证，谁来出钱）

## Idea Evaluation Adaptation

把 paper-review 标准映射到 idea-review，核心问题：
**"If this idea were executed competently with adequate compute, would EMNLP 2026 accept the resulting paper?"**

### EMNLP-specific 评审重点（idea 阶段必须能回答的问题）：

1. **Framework vs benchmark 之分**：这是 framework paper 还是 benchmark paper？两者都可发 EMNLP，但 framework paper 必须产生 testable prediction，benchmark paper 必须比 prior benchmarks 多揭示一个层次的现象。

2. **Human baseline 计划**：是否计划做人类对照？没有 human baseline 的 generalization 研究在 EMNLP 2026 较难过 Tier 1。

3. **Frontier model coverage**：是否包括 GPT-5 / Claude 4.x / Gemini 2.x 这一代？只用开源小模型的 robustness paper 在 EMNLP 已被多次质疑"是否能外推到 frontier"。

4. **Reproducibility**：closed-source API 的 reliance 程度、prompt sensitivity 控制、decoding 参数透明。

5. **Falsifiability**：核心 claim 是否 falsifiable？"我们提出 X taxonomy" 不是 falsifiable claim；"在条件 C 下，所有当前 LLM 的 X 类泛化都失败"是 falsifiable。

6. **Causal vs correlational**：如果 idea 用 "causal" / "mechanism" 等词，是否有 operational definition（do-intervention on prompt structure / counterfactual data / 等）？

7. **Broader Impact / Ethics**：跨语言 / 跨文化 / 公平性维度有没有被纳入设计而非事后补丁？

### Idea-stage red flags（直接降级）：
- "我们提出新的 generalization taxonomy" 而无 testable consequence
- "我们做更难的 test set" 而无 mechanism analysis
- 把 perturbation accuracy 等同于 generalization
- 不计划任何人类对照
- 仅评估开源 7B 以下模型

### Idea-stage green flags（提升至 Tier 1 候选）：
- 提出一个 specific invariance / equivalence relation，并展示当前 LLM 系统性 violate 它的 mechanism
- 把 model 与人类在同一 paradigm 下做 calibrated 对照，揭示**不同形状**的 failure mode
- 用 longitudinal 或 mechanism 分析揭示"看似 robust 实则记忆"或"看似失败实则 calibration mismatch"
- 提出可被独立团队复现的 evaluation protocol，并 release 工具
