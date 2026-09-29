---
name: exp-design
description: 实验设计 Skill。从第一性原理出发设计论文实验：以审稿人为目标受众，围绕"方法有效"和"方法有用"两大支柱组织实验，同时严格控制成本。在规划新实验或审视现有实验时加载此 skill。

---

# 实验设计 Skill (Experiment Design from First Principles)

> 每个实验存在的理由是让审稿人相信一个具体的 claim。没有 claim 支撑的实验是浪费资源。

---

## 核心原则：审稿人买不买账？

实验不是为了"做了"，是为了**说服**。在设计任何实验之前，先回答：

1. **我要审稿人相信什么？**（具体的 claim，一句话）
2. **他现在为什么不信？**（他的 prior belief / 疑虑）
3. **什么实验结果能让他从不信变成信？**（预期的数据 pattern）

如果答不上来，这个实验不该做。

---

## 两大支柱

所有实验围绕两个目标组织，不要超出这两个范围：

### 支柱 A：方法有效（"你的理论预测准吗？"）

审稿人的疑虑：你的理论基于简化假设（完美 oracle、固定 bandwidth），真实世界不是这样的。

**回应策略**：展示理论预测和实验测量高度吻合。

典型实验：

- 测某个可预测的量（如 per-gate accuracy、round ratio）
- 和理论预测值直接对比
- 画 "theory vs experiment" 的图，两条线越近越好

### 支柱 B：方法有用（"你的理论能指导什么？"）

审稿人的疑虑：就算理论在玩具问题上成立，和真实任务有什么关系？

**回应策略**：展示多个下游任务 / 真实场景中，理论预测和实际表现一致。

典型实验：

- 找多个不同结构的任务（覆盖理论的不同 regime）
- 在每个任务上验证理论预测
- 至少一个 real-world case study（不能全是人造的）

---

## 实验设计流程

### Step 1: 列出论文的所有 claims

从 abstract 和 introduction 出发，逐条列出论文声称的东西。每个 claim 标记：

- 是否需要实验支撑（理论 claim 不需要，建模假设和实用性 claim 需要）
- 支撑该 claim 的最小实验是什么

### Step 2: 检查已有数据

**不要重跑已有的好数据。** 审稿人不会因为数据太好而怀疑。对每个 claim：

- 已有数据能支撑吗？→ 直接复用
- 数据有问题（模型不对、规模不够）？→ 重跑
- 没有数据？→ 设计新实验

**复用原则**：已有数据只需要**重新解读**（relabel/reframe），不需要重新采集。例如 AND/OR 树实验数据可以直接 relabel 为 "treewidth=1 的 CSP 实验"。

### Step 3: 设计新实验（最小化原则）

对每个需要新数据的 claim：

1. **找最简单的实验设计**能验证这个 claim
2. **估算成本**（prompts 数、推理时间、是否需要新的 prompt 设计）
3. **确认 per-step accuracy**：先跑 pilot（100 条 prompts），确认 LLM 能做好单步评估。如果单步都做不好，换任务，不要硬跑
4. **确认区分度**：实验结果能区分"理论对"和"理论错"吗？如果两种情况下结果一样，这个实验白做

### Step 4: 排优先级

| 优先级          | 标准                              |
| --------------- | --------------------------------- |
| **P0 必做**     | 没有这个实验，核心 claim 无法支撑 |
| **P1 强烈建议** | 加强说服力，堵住审稿人可能的质疑  |
| **P2 锦上添花** | 有最好，没有不影响 accept         |

**只做 P0 和 P1。** P2 只在 P0/P1 全做完且还有资源时才考虑。

---

## 成本管控

### 硬约束

| 约束                      | 上限     | 理由                         |
| ------------------------- | -------- | ---------------------------- |
| 单次 batch 总 prompts     | ≤ 100K   | GPU 服务器共享，单次不占太久 |
| 单次推理时间              | ≤ 1 小时 | 同上                         |
| 每条 prompt 的 max_tokens | ≤ 16     | 实验输出通常 1-2 tokens      |
| 模型选择                  | 最小够用 | 9B 够就不上 27B              |
| 总实验轮次                | ≤ 3 轮   | 包括 pilot + 正式 + 补充     |

### 成本估算模板

在提交任何实验之前，先算：

```
实验名: B3 Treewidth 预测
Prompts 数: 4 (tw) × 3 (sizes) × 50 (inputs) × ~100 (gates/input) = ~60,000
推理时间估算: 60K prompts × ~60 tokens/prompt ÷ 3800 tokens/sec ≈ 16 分钟
是否在预算内: ✅ < 100K prompts, < 1 小时
```

### Pilot 原则

**任何新实验都先跑 pilot。** Pilot = 正式实验的 1/10 规模（比如 10 个 inputs instead of 100）。

Pilot 检查：

1. prompt 格式正确，LLM 输出可解析
2. per-step accuracy > 80%（否则换任务或换 prompt）
3. 结果有区分度（不同条件下结果不同）

**只有 pilot 通过才跑正式实验。** 这避免了"花 1 小时跑完发现 prompt 写错了"的浪费。

---

## 实验架构：三阶段分离

所有实验遵循同一架构（已验证为最稳定方案）：

```
Phase 1: 本地生成 (generate_prompts.py)
  - 用 ground truth 值构造所有 prompt
  - 输出: all_prompts.json

Phase 2: GPU 服务器推理 (run_inference.py)
  - 一次加载模型 → batch_chat → 释放
  - 输出: all_results.json

Phase 3: 本地分析 (analyze_results.py)
  - 解析输出 → 计算指标 → 生成图表
```

**不要用 API 服务器逐次调用。** 已验证不稳定（隧道断、超时、模型反复加载）。

### Ground truth 输入的合理性

> "为什么用 ground truth 子节点值而不是 LLM 自己的输出？"

因为我们测的是**每个 oracle call 的可靠性**，不是**端到端协议的准确率**。这正是论文的核心 claim：LLM 作为 oracle 是否可靠。

端到端准确率可以从 per-gate error rate 用公式推导：

- Tree: P_correct ≈ (1-ε)^depth
- Chain: P_correct ≈ (1-ε)^(n-1)

不需要实际跑端到端协议。

---

## 实验结果呈现原则

### 每个实验对应一个清晰的 claim

| 实验 | Claim（一句话）              | 呈现方式                                        |
| ---- | ---------------------------- | ----------------------------------------------- |
| A1   | LLM 是可靠的 oracle          | Table: per-gate accuracy by gate type and depth |
| A2   | Round ratio 匹配理论         | Table + Figure: empirical vs n/log₂n            |
| A3   | Locality 是因果来源          | Table: accuracy vs prompt locality              |
| B1   | 框架泛化                     | Table: accuracy on non-AND/OR tasks             |
| B3   | Separation 随 treewidth 变化 | Figure: separation ratio vs treewidth           |
| B4   | 框架对实际有用               | Case study narrative + data                     |

### 不要呈现没有 claim 支撑的数据

如果一个实验结果不支撑任何 claim（比如 iterated fn 的 5% accuracy），要么：

1. 找到它支撑的 claim（"oracle 假设对算术不成立"→ 框架的 scope limitation）
2. 不放进论文

### 负面结果的处理

负面结果（如"顺序任务上 tree 无优势"）是 **有价值的**，因为它验证了理论的精确性：不是"tree 万能"，而是"tree 的优势取决于任务结构"。

把负面结果放在 Discussion 中，framing 为"理论正确地预测了 tree 没有优势的 regime"。

---

## 避免的坑

### 坑 1：实验规模不对

太小 → 统计意义不够。太大 → 浪费资源。

经验值：

- Per-gate accuracy：每个条件 ≥ 500 次评估（置信区间 ±2%）
- 比较两种条件：每种 ≥ 1000 次评估
- Scaling 实验：至少 3 个规模点（能看出趋势）

### 坑 2：测模型能力而非拓扑差异

如果 LLM 连单步都做不好（如 (3x+7)%256 只有 5%），实验测的是模型能力，不是拓扑差异。

**检查方法**：per-step accuracy > 80% 才有意义。低于 80% 换任务。

### 坑 3：过度实验

做 10 个实验不如做 3 个做透。审稿人看的是实验是否 convincing，不是数量。

每个实验应该占论文 0.5-1 页篇幅。NeurIPS 正文 9 页，实验最多 3-4 页，所以**最多 5-6 个实验**。

### 坑 4：忘记 ablation

每个核心 claim 都需要 ablation：你说 A 导致了 B，那去掉 A 看 B 是否消失。没有 ablation = 没有因果证据，只有相关性。

---

## Checklist

设计完实验后，逐条检查：

- [ ] 每个实验对应一个明确的 claim
- [ ] 已有数据能复用的都复用了
- [ ] 新实验的成本已估算，在预算内
- [ ] 每个新实验有 pilot 计划
- [ ] per-step accuracy 已确认 > 80%
- [ ] 正面结果和负面结果都有（不是"一切都好"）
- [ ] 实验总数 ≤ 6（不是越多越好）
- [ ] 每个 claim 有 ablation 支撑因果性
- [ ] 呈现方式已规划（table / figure / narrative）