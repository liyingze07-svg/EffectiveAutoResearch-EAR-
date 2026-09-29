# EAR v2 — 设计决策说明

本文记录 v2 改造的原始疑惑、诊断过程和重构思路，作为未来迭代的参考基线。

---

## 疑惑一：idea-gen 生成质量不够"有攻击性"

### 原始现象
v1 的 idea-gen 直接把 landscape 和 gaps 喂给 GPT，让它生成 8-12 个 idea。生成的 idea 确实覆盖了 gap，但普遍偏"顺势延伸"——沿着已有工作的脉络往前走一步，缺乏真正质疑领域假设的那种想法。

### 诊断
问题的根源在于**生成的起点是 gap，而不是质疑**。Gap 是"这里还没做"，但研究者更值钱的洞见是"这里的已有做法根本是错的"。前者生成的是填补工作，后者生成的是挑战性工作。

LLM 的行为模式决定了它不会主动去质疑给它的上下文——它倾向于顺势补全。要让它产出真正的批判性洞见，必须**显式要求它先扮演批评者**，再扮演建议者。

### 重构方案：两段式生成（Phase 2a → 2b）

```
Phase 2a（新）: 批判者视角
  GPT 被要求不生成任何 idea，只做一件事：
  系统性批判当前 landscape 的四类结构性弱点：
    ① 哪些假设从未被直接检验（Unverified Assumptions）
    ② 哪些方法被错误泛化到不适用的场景（Incorrect Generalization）
    ③ 哪些实验设计存在根本性缺陷（Experimental Design Flaws）
    ④ 哪些跨领域迁移没有检验假设是否成立（Cross-Domain Misfits）
  输出: CRITICAL_ANALYSIS.md，编号 CRITIQUE-01...N

Phase 2b（新）: 建议者视角（基于批判）
  GPT 在同一 thread 内继续，但现在的起点是"批判清单"而非"gap 矩阵"
  每个 idea 必须声明它在攻击哪个 CRITIQUE-ID
  约束: ≥50% idea 各自锚定不同批判（防止所有 idea 都扑向同一个问题）
```

**效果**：idea 从"填补空白"变成"质疑前提"。在内部测试案例中，排名第一的 idea 其核心洞见直接来自一条 "experimental design flaw" 类批判（该领域通行的二值化打分机制会系统性奖励冒进行为），而不是来自 gap 矩阵里的任何一条 gap。

---

## 疑惑二：idea-refine 出来的还是太 general

### 原始现象
v1 的 idea-refine 跑 3 轮 GPT review-revise，达到 9/10 分后输出 FINAL_PROPOSAL.md。但用户拿到这份文件后发现方法部分仍然停留在"系统描述"层面，比如"我们设计了一个 loss function"，却没有写出 loss 的数学形式。这样的提案很难直接指导实验。

### 诊断
v1 的评分维度 `Method Specificity`（占权重 25%）虽然是最重要的维度，但其评分标准是"能否让工程师开始实现"——这个门槛大约在 7-8 分，GPT 达到这个分数之后就不会再继续追问具体公式了。换言之，**评分机制本身没有逼迫方法细节的完整写出**。

根本问题：review 循环的目标是"评价方向是否正确"，而不是"填充实现细节"。这是两件事，不该用同一个循环做。

### 重构方案：Deep Expansion Pass（Phase 5.5）

在 review 循环结束、Final Report 写入之前，插入一个专门的"展开"步骤：

```
Phase 5.5: Deep Expansion Pass（非评审，只填充）
  Step 1: 扫描当前最优提案，找出所有"手波"章节：
    - 方法组件只有散文，无公式或伪代码 → [EXPAND]
    - Loss 只提名字未展开 → [EXPAND]
    - 模块无输入/输出维度 → [EXPAND]
    - 训练 recipe 只写"standard"无具体超参 → [EXPAND]

  Step 2: 调用 mcp__codex__codex-reply（同线程），
    任务只做一件事：对每个 [EXPAND] 节，分别提供：
      ① 完整 loss 公式（所有项定义）
      ② 5-15 行伪代码
      ③ 模块接口（输入维度→输出维度）
      ④ 超参范围 + 选取依据

  输出: round-N-expanded.md → FINAL_PROPOSAL.md 的基础
```

**设计原则**：Expansion Pass 被严格约束为"只填细节，不改方向"。它不是第四轮 review，不能推翻已经确定的方法选择，只能把已选择的方法写清楚。

---

## 疑惑三：直接生成理论内容，容易出现"理论 OK 但实验不能验证"

### 原始现象
在公式推导的诉求下，如果只是简单地让 LLM"写一个定理"，它很容易生成一个表述正确但实验上无法验证的 claim——比如"证明了样本复杂度为 O(n/ε²)"，但如果你的实验只能跑 100 个样本，根本看不到 O(n) 这个量级的规律。

这是**理论-实验脱节**的问题，它不仅是写作风格问题，更是一个 paper 从 idea 阶段就会埋下的结构性缺陷。

### 诊断
核心问题在于：不同类型的理论 claim 对应不同的实验验证协议，但 LLM 在生成理论时并不会自动对照"这个 claim 我能不能验证"。需要一个显式的映射机制，把 claim 类型和实验设计连接起来。

AI/ML 各子领域对理论-实验对应关系有相当清晰的客观规律：
- Convergence bound → 训练曲线实验（loss vs steps，多 seed）
- Generalization bound → 数据缩放实验（train size vs test error）
- Sample complexity → 标签效率实验（label fraction vs metric）
- Approximation ratio → 合成最优解对比实验
- Computational complexity → wall-clock + FLOP scaling

### 重构方案：三层理论接地（Phase 1.4.T + 1.4.TE）

```
Phase 1.4.T: Theoretical Grounding（在写初始提案时强制执行）
  T1 Formalizability Scan: 逐组件检查"能否关联一个数学对象"
     → 起草公式草稿，未知部分用 ??? 占位
  T2 Assumption Inventory: 列出每条公式的前提假设
     → 分类：STANDARD / RESTRICTIVE / UNVERIFIED

Phase 1.4.TE: Theory-Experiment Alignment Matrix
  对每条理论 claim，查 Claim Type 映射表，填入：
    | Claim | 类型 | 标准验证协议 | 所需规模 | 可行性 |
  可行性 = FEASIBLE / CAVEATS / NOT FEASIBLE（按 Phase 0 资源约束评估）

  对 NOT FEASIBLE 的 claim，强制写出三条出路：
    (a) 弱化 claim 到可验证版本
    (b) 纯理论证明路径（不需要实验）
    (c) 重新设计实验使其可行
```

这个机制的关键不是"禁止理论"，而是**在 idea 阶段就让作者意识到每条理论 claim 的实验代价**。如果验证代价超出资源约束，应该在提案阶段就调整主张，而不是等到实验阶段才发现。

Phase 5.5 之后还会二次检查，防止 GPT 在展开公式时"偷偷引入"新的不可验证 claim。

---

## 疑惑四：单向 review 循环不能真正逼迫方法细节

### 原始现象
v1 的 review 循环是：Claude 写提案 → GPT 给评分和意见 → Claude 修改 → 重复。这个流程里 GPT 是"批评者"，Claude 是"修改者"。GPT 的每次评分都基于它读到的文本，但如果提案写得模糊，GPT 并不会追问——它只会给出"Method Specificity 偏低"的评分，然后 Claude 自行猜测怎么改。

本质上：**单向的评价-修改循环没有逼迫 Claude 解释清楚它实际上是怎么设计的**。Claude 改出来的方案可能看起来更完整，但它是基于 GPT 的批评"表面改好看"，而不是被逼着把真正的设计思路说清楚。

### 重构方案：Socratic 对话模式（-- mode: socratic）

改变交互模型：**GPT 从评价者变成追问者**。

```
Socratic 循环（最多 5 轮）:
  Turn 0: GPT 读提案，提出 3-5 个具体的机制问题
           规则：禁止评分，只能问问题
           好问题: "Step 2 的 loss 是 supervised 还是 self-supervised？"
           坏问题: "方法不够清晰" (太模糊，不允许)

  每轮循环:
    Claude 逐条回答 → 整合进提案 → GPT 继续追问
    直到 GPT 主动写出"我已充分理解这个方法"

  最终评分：只在 GPT 声明完全理解之后进行
```

**设计意图**：如果 GPT 通过追问仍然能理解方法，说明方法描述已经足够清晰。传统 review 循环里，GPT 评分低≠GPT 真的不懂——它可能只是给了一个保守的分数。Socratic 模式让 GPT 的"理解"成为一个可显式触发的状态，而不是通过分数隐式推断。

两种子模式：
- `socratic-auto`：Claude 自动回答 GPT 的问题（全自动，适合 batch）
- `socratic-human`：每轮 PAUSE，等人工输入（适合深度打磨某个关键方法）

---

## 疑惑五：低成本 Codex 交互

### 原始现象
所有 GPT 调用都通过 `mcp__codex__codex` 工具，依赖 Codex MCP Server 本地部署。部分用户没有配置 MCP，fallback 成 Claude 自评（减分），质量下降。

### 重构方案：GPT-only 路径

新增 `tools/gpt_call.sh`，curl 封装 OpenAI API，模拟 `mcp__codex__codex` 的 thread 语义（通过临时 JSON 文件跟踪对话历史）。

```bash
./run.sh --gpt-only "方向" ICML
# 等价于设置 CODEX_MODE=gpt-api
# 所有 mcp__codex__codex 调用 → bash tools/gpt_call.sh
```

不需要 Codex MCP Server，只需要 `OPENAI_API_KEY` 环境变量即可。

---

## 设计原则总结

经过这次重构，v2 的核心设计原则是：

1. **从质疑出发，而非从 gap 出发**  
   批判 landscape 是比填补 gap 更有价值的起点。CRITICAL_ANALYSIS.md 是整个 pipeline 的新起点。

2. **评价和展开是两件不同的事**  
   review 循环负责判断方向对不对，Deep Expansion Pass 负责把方向说清楚。不要用同一个工具做两件事。

3. **理论 claim 在 idea 阶段就要和实验挂钩**  
   用 ML 子领域的客观规律（而不是通用 prompt）来检查每条 claim 的实验可行性。不可行的 claim 不是禁止，而是要求作者提前做出选择。

4. **"理解"应该是可观测的状态，而不是分数的代理**  
   Socratic 模式让 GPT 的理解变成一个明确的触发条件，而不是通过 8.5 分 vs 9 分来猜测。
