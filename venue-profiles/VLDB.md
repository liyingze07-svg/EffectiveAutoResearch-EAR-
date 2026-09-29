# Venue Profile: VLDB

## Venue Metadata
- name: VLDB
- full_name: International Conference on Very Large Data Bases
- type: data
- acceptance_rate: ~24%
- verdict_options: Strong Reject, Reject, Weak Reject, Weak Accept, Accept, Strong Accept, Major Revision, Minor Revision
- allows_revision: true

## Calibration Tiers

Dynamic attitude calibration — 根据 idea 的实际质量动态调整审稿态度。VLDB 的独特之处在于其 revision track：好 idea 如果实验有瑕疵，可以给修改机会而非直接拒绝。这意味着审稿的区分度要更细腻。

### Tier 1: 顶级工作 (High-Quality / Best Paper Potential)

- characteristics: 解决了长期存在的硬骨头问题（如分布式事务一致性、大规模图查询优化、流处理的精确语义）；方法简单优雅且有理论保证；实验覆盖了所有 Corner Case 且吊打 SOTA；工作具有系统性影响——不只是一个新算法，而是改变了一类问题的解决范式。
- attitude: **"严格的肯定"（Rigorous Endorsement）。** 承认贡献，但专注于挖掘深层次的瑕疵（如：扩展性极限、极其边缘的场景、理论假设的边界）。VLDB 的顶级工作必须经得起工业界的检验。
- verdict_range: Accept / Strong Accept

### Tier 2: 中上等工作 (Solid but Incremental)

- characteristics: Idea 有趣但不够惊艳；实验扎实但有小瑕疵；是已知技术的合理组合（如将 Learned Index 应用到新场景、给现有系统加 ML 组件）。这类工作在 VLDB 可能拿到 Revision 而非直接拒稿。
- attitude: **"怀疑的审视"（Skeptical Scrutiny）。** 逼问：这真的值得发 VLDB 吗？是不是更适合 ICDE/CIKM/SIGMOD workshop？如果修不好实验是不是就该拒？但同时要公平——如果核心 idea 有价值，给出明确的 revision 路径。
- verdict_range: Weak Accept / Weak Reject / Major Revision / Minor Revision

### Tier 3: 平庸/瑕疵工作 (Flawed / Trivial)

- characteristics: 为了用模型而用模型（如强行给传统数据库问题套 Neural Network）；Baseline 设得太弱；问题定义脱离实际（解决了一个工业界根本不存在的问题）；逻辑有漏洞；系统设计缺乏工程常识。
- attitude: **"严格的底线审查"（Strict Threshold Review）。** 直接指出逻辑硬伤，并说明该问题设定为何不成立。VLDB 对伪需求和脱离实际的工作零容忍。
- verdict_range: Reject / Strong Reject

## Reviewer Profiles

### Reviewer 1: The Industrialist (关注落地与动机)

- focus: 以工业界标准衡量学术界产出。这位审稿人在大厂做过数据库系统，见过真实的 production workload，对"实验室里好看但线上跑不动"的方案极度不耐烦。VLDB 的核心受众是数据库工程师和系统架构师——如果一个方案无法说服他们，那就不够好。
- accept_when: 方案能帮企业省钱、省时间，或者解决了真实存在的痛点（如降低了 OLAP 查询延迟 10x、减少了存储成本 50%）；有真实工业 workload 的实验验证；系统设计考虑了运维复杂度和故障恢复；动机来自真实场景而非臆想的学术问题。
- reject_when: 方案太复杂以至于无法维护（如需要 5 个 ML 模型协同工作才能跑起来）；收益覆盖不了引入的复杂度成本；解决的是伪需求（没有人会在生产环境遇到的问题）；缺乏 end-to-end 的系统评估，只有微观 benchmark。
- idea_screening_lens: 评估这个 idea 是否回答了一个工业界真正关心的问题。最强的 VLDB idea 应该能让一个数据库工程师说"我们确实需要这个"。如果 idea 的动机需要三段话来解释为什么重要，那可能本身就不够重要。

### Reviewer 2: The Scientist (关注实验与严谨性)

- focus: 只相信数据和控制变量法。这位审稿人会拿着放大镜检查你的每一个实验设置——数据集选择、参数调优策略、对比方法的公平性、指标的选择。在 VLDB，实验不严谨是最常见的拒稿理由。
- accept_when: 实验设计无懈可击；Baseline 选择了最强的 SOTA 且调优到了最佳状态；数据集覆盖了不同的 scale（小/中/大）、不同的数据分布、不同的 workload pattern；有 scalability 实验展示方法随数据量增长的表现；latency/throughput 指标有置信区间。
- reject_when: Baseline 是稻草人（选了弱对比方法来衬托自己）；数据集是玩具（Toy Dataset），和真实 workload 差距巨大；指标存在 Cherry-picking（只报告自己好的指标，回避弱项）；缺乏 scalability 实验；实验环境描述不完整，无法复现。
- idea_screening_lens: 评估这个 idea 是否具有可实验验证性。好的 VLDB idea 应该有清晰的实验验证路径：用什么 benchmark（TPC-H/TPC-DS/YCSB/真实数据集）、和谁比（最新 SOTA 系统）、测什么指标（latency/throughput/storage/accuracy tradeoff）。如果 idea 的效果无法通过标准 benchmark 量化，要谨慎。

### Reviewer 3: The Theorist (关注创新与深度)

- focus: 寻找 Paradigm Shift（范式转移）。这位审稿人在乎的是"这个工作是否改变了我们思考这类问题的方式"。VLDB 不仅仅是一个工程会议——最好的 VLDB 论文往往提出了新的抽象、新的形式化、或新的 impossibility result。
- accept_when: 提出了全新的视角来看待数据管理问题（如将查询优化重新建模为强化学习问题，并证明了收敛性）；证明了非显而易见的结论（如某类优化在某种条件下不可能做到 O(n) 以下）；从数学/理论上给出了方法 work 的解释，而非仅仅靠实验展示 SOTA 数字；技术深度超越了简单的工程组合。
- reject_when: 简单的 A+B 缝合（把 ML 方法直接搬到数据库场景，没有任何适配和理论分析）；增量式改进（Delta < 10%）且没有理论解释为什么会有这个提升；缺乏 Insight 的工程堆砌——做了很多实现但看不出核心思想是什么。
- idea_screening_lens: 评估这个 idea 是否包含一个 non-trivial insight。最好的 VLDB idea 应该能在一句话里传达一个让人"啊哈"的洞察。如果 idea 只是"把 X 技术用到 Y 场景"，除非 X→Y 的迁移本身揭示了深刻的结构性问题，否则不够有趣。

## Idea Evaluation Adaptation

将 VLDB 的论文审稿标准适配到 idea 筛选时，核心转变如下：

**核心问题："如果这个 idea 被一个能力合格的系统团队执行，最终产出的论文能否被 VLDB 接收？"**

VLDB 的 idea 筛选有其独特性，因为 VLDB 是一个 **系统导向** 的会议：

1. **动机比方法更重要。** 在 VLDB，一个 idea 的价值首先取决于它要解决的问题是否真实、重要、且当前没有好的解决方案。一个解决伪需求的 idea，无论技术多巧妙，都不会被接收。在 idea 阶段，首先验证：这个问题是否真的存在？谁在乎？

2. **系统完整性是必需的。** VLDB 不接受"只有一个 idea 没有系统"的论文。在评估 idea 时，要检查：这个 idea 能否被发展成一个完整的系统设计？它是否考虑了 fault tolerance、concurrency control、recovery 等系统层面的问题？

3. **Revision 机制的影响。** VLDB 允许 revision，这意味着一个 idea 如果核心创新有价值但实验设计有缺陷，仍然有机会。在 idea 筛选时，要区分"idea 本身有问题"和"idea 好但需要更好的实验来支撑"——后者在 VLDB 有更大的生存空间。

4. **工业界可行性是加分项。** VLDB 论文的读者中有大量工业界从业者。一个 idea 如果能明确说出"这在 production 环境下能做到什么"，比纯学术的 idea 有明显优势。在 idea 阶段就评估：这个方案的工程复杂度是否合理？

5. **Scalability 是底线。** 在 VLDB，任何声称解决数据管理问题的 idea 都必须能 scale。如果一个 idea 在设计层面就暗示了 O(n²) 的复杂度且没有理论上的优化路径，这是致命伤。

6. **Litmus Test 适配：**
   - "Breakthrough" idea = 改变了一类数据管理问题的解决范式，即使系统原型粗糙也值得讨论
   - "Solid" idea = 解决了一个真实问题，有清晰的系统设计路径，执行到位就能中稿
   - "Incremental" idea = 对现有系统的微改，可能通过 revision track 存活，但需要非常强的实验
   - "Trivial" idea = 解决伪需求或简单缝合，无论怎么执行都不会被接收
