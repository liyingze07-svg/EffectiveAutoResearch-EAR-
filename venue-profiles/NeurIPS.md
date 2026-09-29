# Venue Profile: NeurIPS

## Venue Metadata
- name: NeurIPS
- full_name: Conference on Neural Information Processing Systems
- type: ML
- acceptance_rate: ~25%
- verdict_options: Strong Reject, Reject, Weak Reject, Weak Accept, Accept, Strong Accept
- allows_revision: false

## Calibration Tiers

Dynamic attitude calibration — 根据 idea 的实际质量动态调整审稿态度。NeurIPS 比 ICML 更宽容地接纳跨学科工作、创造性的新方向、以及有社会影响力的贡献。校准时应当反映这种开放性，同时不降低核心质量标准。

### Tier 1: 顶级工作 (High-Quality / Oral or Spotlight Potential)

- characteristics: 提出了改变游戏规则的新范式或新视角；在理论和实验上都有突出表现；解决了长期存在的核心挑战（如 generalization、causality、scalable inference）；具有广泛的跨领域影响力（一篇论文同时启发了 CV、NLP、RL 的后续工作）；或者通过大规模实证研究揭示了重要的经验性发现。NeurIPS 还特别青睐那些打开全新研究方向的"种子论文"——即使当前实验规模有限，但 idea 的影响力巨大。
- attitude: **"严格的肯定"（Rigorous Endorsement）。** 承认其开创性，但审视其 generality——这个方法是否过于依赖特定假设？在更广泛的条件下是否仍然成立？Broader Impact 声明是否诚实地讨论了潜在风险？
- verdict_range: Accept / Strong Accept

### Tier 2: 中上等工作 (Solid but Incremental)

- characteristics: 方法有一定新意但属于对现有工作的自然延伸；实验结果 positive 但缺乏 surprising 的发现；理论贡献正确但不深刻；或者是一个好的工程贡献但缺乏 conceptual insight。在 NeurIPS，这个 tier 还包括那些"方向有趣但执行不够到位"的论文——NeurIPS 比 ICML 更愿意给这类工作机会，前提是 idea 本身够有趣。
- attitude: **"好奇的审视"（Curious Scrutiny）。** 比 ICML 的 Tier 2 态度稍微温和——NeurIPS 审稿人会认真考虑"这个 idea 是否打开了有趣的方向"，即使当前的执行不完美。但仍然要逼问：这个贡献是否足够 significant？是否只是已知方法在新数据上的重复？
- verdict_range: Weak Accept / Weak Reject

### Tier 3: 平庸/瑕疵工作 (Flawed / Trivial)

- characteristics: 没有清晰的核心贡献；方法是已知技术的简单组合且缺乏新 insight；实验设计有明显缺陷（不公平的比较、数据泄露、缺乏消融实验）；声称的理论结论与实验证据不匹配；或者 Broader Impact 声明完全缺失或敷衍。
- attitude: **"严格的底线审查"（Strict Threshold Review）。** 直接指出核心问题所在。NeurIPS 虽然开放，但对质量底线同样严格——开放性不等于来者不拒。
- verdict_range: Reject / Strong Reject

## Reviewer Profiles

### Reviewer 1: The Empiricist (关注大规模实验与可复现性)

- focus: 大规模实证验证和可复现性。NeurIPS 社区非常重视实验的 scale 和 reproducibility——这位审稿人代表了这种文化。他/她期望看到在真实规模的 benchmark 上、多次运行、带 error bar 的严谨实验。NeurIPS 近年来推动了 reproducibility checklist，这位审稿人是最认真执行的那一个。
- accept_when: 实验覆盖了多种 scale 和场景（从合成数据到真实大规模数据集）；提供了完整的 reproducibility 信息（代码、超参数、计算资源、随机种子）；Ablation study 完备，清晰展示了每个组件的边际贡献；和 SOTA 的比较公平、全面、且使用了最新的 baseline；大规模实验揭示了有趣的 scaling behavior。
- reject_when: 实验只在小规模或过时的数据集上进行（如只用 CIFAR-10 声称解决了 vision 的问题）；缺乏 reproducibility 信息——没有代码承诺、没有超参数细节；Error bar 缺失或可疑地小；Baseline 选择过时或调参不公平；声称的性能提升在统计上不显著。
- idea_screening_lens: 评估这个 idea 是否能通过严格的大规模实验验证。好的 NeurIPS idea 应该有清晰的 experimental story：它在什么 scale 上应该 work？随着数据/模型/计算量增加，效果如何变化？是否存在自然的 ablation 维度？如果一个 idea 只能在 toy setting 下验证，在 NeurIPS 会面临困难。

### Reviewer 2: The Innovator (关注范式转移与创造性)

- focus: 范式转移和创造性的新 framing。这是 NeurIPS 区别于其他 ML 会议的核心——NeurIPS 的最佳论文往往不是"在现有方向上做得最好"，而是"开辟了全新的方向"。这位审稿人寻找的是那些让人重新思考问题本身的工作。NeurIPS 的跨学科传统（神经科学、认知科学、统计物理等与 ML 的交叉）也在这位审稿人的评估范围内。
- accept_when: 提出了看待老问题的全新视角（如重新 formulate 一个 optimization 问题为一个 game theory 问题，带来了新 insight）；方法背后的 intuition 清晰、深刻、且有启发性；打开了一个全新的研究方向，即使当前的实验不完美；从其他领域（神经科学、物理、经济学等）引入了有价值的概念并成功迁移到 ML；Broader Impact 考虑周全，展现了对 ML 社会影响的深刻理解。
- reject_when: 只是现有方法的 trivial extension（如给 Loss 加一项、换一种 Normalization）；声称 novelty 但实际上已被之前的工作覆盖（缺乏 thorough literature review）；创新点只在工程实现层面而非概念层面；跨学科的 framing 只是表面功夫，删掉后论文完全不受影响。
- idea_screening_lens: 评估这个 idea 的 novelty ceiling。问自己：这个 idea 最好的版本——如果执行完美——会让 NeurIPS 社区兴奋吗？会被引用 100 次以上吗？NeurIPS 接受"high risk, high reward"的 idea——如果一个 idea 可能失败但如果成功会非常有影响力，应该比一个必然成功但影响力有限的 idea 得到更高评价。

### Reviewer 3: The Rigorist (关注理论深度与形式化分析)

- focus: 理论深度和数学严谨性。NeurIPS 有着强大的理论社区（learning theory、optimization theory、information theory），这位审稿人代表了这个传统。他/她不需要每篇论文都有定理，但期望每篇论文都有 rigorous thinking——无论是形式化的理论还是 principled 的方法论。
- accept_when: 提供了方法有效性的理论保证（收敛性、泛化界、sample complexity）；理论假设合理且明确讨论了适用范围；理论结果和实验结果之间有清晰的对应关系（理论预测的现象在实验中被验证）；即使没有定理，方法的设计也有清晰的原理性解释（principled derivation）而非 ad-hoc 的 trick 组合。**公式密度（严谨的非正式性）**：接受明确猜想 + 对应实证验证的组合——例如"我们猜想 generalization error ≤ O(1/√n)（类比 PAC-Bayes），并在 Section 4 实证验证"——这比纯自然语言声明更有说服力，即使定理尚未正式证明。
- reject_when: "Mathiness"——堆砌无关公式来制造深度的假象（如果删掉数学部分论文完全不受影响，那这些数学就是装饰品）；理论假设过于强以至于脱离实际（如假设凸优化来分析 deep learning）；证明有错误或逻辑跳跃；理论和实验完全脱节——理论分析的是简化模型，实验跑的是完全不同的方法。**Principled-free derivation**：方法决策只靠"试了 X 有效"解释，声称有理论贡献但零数学符号——在 NeurIPS 理论社区审稿人看来，这是方法设计缺乏严肃思考的标志。
- idea_screening_lens: 评估这个 idea 是否有 principled foundation。好的 NeurIPS idea 不一定需要有完整的理论，但应该有一个"为什么这个方法应该 work"的清晰论证——可以是直觉性的，但必须能经受住逻辑推敲。如果一个 idea 的核心论证是"我试了一下，发现 work"，在 NeurIPS 会面临质疑。**Theorem Scaffold 评估**：在 idea 阶段检查是否包含核心数学 claim 的草稿（即使非正式）。"我们猜想本方法的样本复杂度为 O(d/ε²)，基于与 ridge regression 的类比" 远优于 "我们的方法具有良好的理论性质"。NeurIPS Rigorist 对有猜想+实证支撑的 idea 评分明显高于只有叙述性描述的 idea。

## Broader Impact Consideration

NeurIPS 要求所有论文包含 Broader Impact 声明。在 idea 筛选阶段，这意味着：

- **加分项：** idea 明确考虑了潜在的社会影响（正面和负面）；方法设计中内置了 fairness/privacy/robustness 考量；应用场景有明确的社会价值。
- **扣分项：** idea 有明显的 dual-use 风险但未讨论；方法可能放大现有偏见但未提及；声称的应用场景过于理想化，忽略了现实中的伦理约束。
- **中性：** 纯理论工作的 Broader Impact 可以简短，但不应缺失。

## Idea Evaluation Adaptation

将 NeurIPS 的论文审稿标准适配到 idea 筛选时，核心转变如下：

**核心问题："如果这个 idea 被一个能力合格的团队执行，最终产出的论文能否被 NeurIPS 接收？"**

NeurIPS 的 idea 筛选有其独特性——它是 ML 领域最广泛的顶会：

1. **比 ICML 更宽容的范围。** NeurIPS 接受纯理论、纯实验、方法论、应用、benchmark/dataset 贡献、甚至 position paper（以 workshop 形式）。在评估 idea 时，不要仅因为它不是典型的"提出新方法+实验验证"范式就拒绝——NeurIPS 欢迎多样性。

2. **"High risk, high reward" 原则。** NeurIPS 社区对创造性和大胆的 idea 更加包容。一个可能失败但如果成功会极其有影响力的 idea，应该得到比 ICML 更高的评分。在 idea 筛选时，明确区分"risky but exciting"和"flawed and uninteresting"。

3. **跨学科加分。** NeurIPS 的名字中有"Neural"和"Information Processing"——它的传统根植于神经科学、认知科学、统计物理与计算机科学的交叉。一个从非 ML 领域引入新视角的 idea，在 NeurIPS 比在 ICML 有更好的机会。

4. **Broader Impact 不是装饰。** NeurIPS 社区认真对待 AI 的社会影响。一个在 idea 阶段就考虑了 fairness、privacy、environmental cost 的工作，会比完全忽略这些维度的工作有优势。

5. **Empirical 贡献也有价值。** 不同于 ICML 对理论的偏好，NeurIPS 接受纯 empirical 的贡献——前提是实验规模够大、发现够 surprising、且对社区有参考价值（如 scaling laws 论文、large-scale benchmark 论文）。在 idea 筛选时，不要因为 idea 缺乏理论组件就自动降分。

6. **Litmus Test 适配：**
   - "Breakthrough" idea = 打开全新方向、或对已知现象给出全新解释的 idea，即使执行有限也值得发表
   - "Solid" idea = 在一个明确的方向上有清晰贡献的 idea，执行到位即可中稿
   - "Incremental" idea = 自然延伸但缺乏 surprise 的 idea，需要非常强的实验才能过线
   - "Trivial" idea = 无论执行如何都不会被 NeurIPS 社区认为有价值的 idea
