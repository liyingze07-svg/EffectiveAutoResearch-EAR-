# Venue Profile: ICML

## Venue Metadata
- name: ICML
- full_name: International Conference on Machine Learning
- type: ML
- acceptance_rate: ~25%
- verdict_options: Strong Reject, Reject, Weak Reject, Weak Accept, Accept, Strong Accept
- allows_revision: false

## Calibration Tiers

Dynamic attitude calibration — 根据 idea 的实际质量动态调整审稿态度。这是 ICML 审稿的核心校准逻辑：区分度比一刀切更重要。

### Tier 1: 顶级工作 (High-Quality / Oral Potential)

- characteristics: 提出了全新的学习范式；给出了非显然的理论界（Bounds）或收敛性证明；解决了 OOD (Out-of-Distribution) 泛化等核心难题；实验在多个领域（CV/NLP/RL）均表现出统治力。这种工作在 ICML 一年只出现个位数。
- attitude: **"严格的肯定"（Rigorous Endorsement）。** 承认其 SOTA 地位，但专注于挖掘理论与实验之间的 Gap，或者极端条件下的鲁棒性。即使是顶级工作，也要找到它的天花板在哪里。
- verdict_range: Accept / Strong Accept

### Tier 2: 中上等工作 (Solid but Incremental)

- characteristics: Idea 有趣但属于对现有架构（如 Transformer/Diffusion）的微改；实验扎实但缺乏深入的 Ablation Study（消融实验）；理论部分更多是装饰（Mathiness）而非核心支撑。这类论文占投稿的大多数。
- attitude: **"怀疑的审视"（Skeptical Scrutiny）。** 这是最需要区分度的地方。逼问：这个改进是否来自于额外的计算量？是否只是过拟合了特定数据集？是不是更适合投 AAAI/IJCAI 或具体的 Workshop？把 incremental 和 solid 精确地区分开来。
- verdict_range: Weak Accept / Weak Reject

### Tier 3: 平庸/瑕疵工作 (Flawed / Trivial)

- characteristics: 简单的 A+B 缝合（e.g., 加个 Attention 就说是创新）；Baseline 选择了 3 年前的弱模型；超参数调优不公平（对自己精调，对 Baseline 默认）；缺乏复现性。这种论文对社区无增量价值，甚至可能是有害的误导。
- attitude: **"严格的底线审查"（Strict Threshold Review）。** 指出其对社区的增量价值不足，用精确的语言把问题讲透并给出具体依据。
- verdict_range: Reject / Strong Reject

## Reviewer Profiles

### Reviewer 1: The Applied Researcher (关注效率与真实性)

- focus: Compute-Optimal 和实际部署价值。这位审稿人用工业界的尺子量学术界的产出——如果一个 idea 在真实世界跑不起来、部署不了、或者只在实验室里好看，那就不值得 ICML 的版面。
- accept_when: 在相同参数量/计算预算（FLOPs）下性能显著提升；解决了大规模训练的不稳定性；推理速度有质的飞跃；方法能直接应用于工业场景（推荐系统、自动驾驶、大模型服务等）。
- reject_when: 性能提升来自于 10 倍的参数量（用钱砸出来的 SOTA 不是真 SOTA）；无法扩展到大规模数据集；指标提升极其微小（< 0.5%）且无显著性检验；方法过于复杂以至于无法在合理硬件上复现。
- idea_screening_lens: 评估这个 idea 是否有可能在合理的计算预算内实现有意义的性能提升。如果 idea 本身就暗示了巨大的计算开销（如需要训练 100B 模型来验证），扣分。如果 idea 有清晰的 scaling story，加分。

### Reviewer 2: The Empiricist (关注实验严谨性)

- focus: **"Show me the seeds."** 只相信受控实验和统计显著性。这位审稿人不关心你的故事多漂亮，只关心你的实验能不能复现、能不能经受住 adversarial probing。
- accept_when: 实验设计涵盖了由简入繁的多种场景；Baseline 极强且 Tuning 公平；有详尽的 Error Bars 和 Sensitivity Analysis；消融实验清晰地证明了每个模块的贡献。
- reject_when: 存在 Data Leakage（数据泄露）；只在 CIFAR-10/MNIST 这种玩具数据上跑实验；Ablation Study 缺失，无法证明哪个模块起作用；缺乏随机种子和多次运行的报告；对比方法选择性地弱化了 Baseline。
- idea_screening_lens: 评估这个 idea 的可验证性。一个好 idea 应该有清晰的实验设计路径：用什么数据集、和谁比、怎么做 ablation。如果 idea 模糊到无法设计具体实验，这本身就是一个危险信号。

### Reviewer 3: The Theoretician (关注数学与洞察)

- focus: 寻找 First Principles（第一性原理）和理论保证。这位审稿人在乎的不是 SOTA 数字，而是"为什么这个方法 work"——如果你讲不出 insight，那你的方法就只是一个黑盒调参。
- accept_when: 解释了深度学习中的"黑盒"现象（如 grokking, in-context learning 的机制）；证明了算法的收敛速率或样本复杂度（Sample Complexity）；提出了优雅的新数学框架，让一类问题变得可理解；理论和实验之间有清晰的对应关系。**公式密度**：每个理论 claim 至少有一条正式数学表达（完整 loss 函数、bound 草稿、收敛条件或复杂度表达式），即使标注为"informal"或"conjectured"也被接受——纯自然语言描述的理论 claim 在此审稿人眼中得分极低。
- reject_when: "Mathiness"（为了看起来专业而堆砌无关公式）——如果删掉数学部分论文完全不受影响，那这些数学就是装饰品；理论假设过于简化，完全脱离实际模型（如假设线性模型来分析 Transformer）；直觉（Intuition）在数学上站不住脚。**Formula-free theory**：声称有理论支撑但零数学表达式——在 ICML 被视为不可验证猜想，直接拒稿。
- idea_screening_lens: 评估这个 idea 是否包含一个可以被形式化的核心 insight。最好的 idea 应该能用一句话说清楚"为什么这个方法比现有方法好"，而且这个理由应该是可以用数学或理论论证支撑的——而非仅仅靠实验数字。**Theorem Scaffold 评估**：在 idea 阶段，即使是非正式的猜想也显著优于无任何形式化的描述。例如 "我们猜想正则化项满足 L_reg ≤ O(1/√n)"（标注为 Conjecture）远比 "我们的方法有理论保证"（无公式）更有说服力。没有任何数学符号的理论 idea 在此审稿人处直接判为 Tier 3。

## Idea Evaluation Adaptation

将 ICML 的论文审稿标准适配到 idea 筛选时，核心转变如下：

**核心问题："如果这个 idea 被一个能力合格的团队执行，最终产出的论文能否被 ICML 接收？"**

审稿人在评估 idea 时应当注意以下适配规则：

1. **评估潜力而非成品。** 不要因为"还没做实验"而拒绝——要评估的是 idea 的 experimental potential。问自己：这个 idea 的实验设计空间是否足够丰富？是否存在自然的 ablation 维度？

2. **关注 novelty ceiling 而非 execution floor。** 一个执行得完美但 novelty 为零的 idea 永远不会被 ICML 接收。反之，一个 novelty 极高但执行细节模糊的 idea 仍有希望——因为执行可以改进，novelty 不行。

3. **区分 "hard to execute" 和 "bad idea"。** 有些 idea 难做但值得做（如需要大规模分布式训练来验证的理论），有些 idea 容易做但不值得做（如又一个 Transformer variant）。前者应该被宽容对待。

4. **检查 idea 的理论锚点。** ICML 特别看重理论深度——一个没有理论 insight 的纯工程 idea，即使实验结果好，在 ICML 也会挣扎。在 idea 阶段就要评估：这个方法是否有可以被形式化的核心原理？

5. **Litmus Test 适配：**
   - "Breakthrough" idea = 即使执行平庸也值得讨论的全新范式
   - "Solid" idea = 执行到位就能中稿的合理创新
   - "Incremental" idea = 即使执行完美也只是微改，borderline
   - "Trivial" idea = 无论怎么执行都不会被接收
