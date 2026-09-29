# Venue Profile: SIGMOD

## Venue Metadata
- name: SIGMOD
- full_name: ACM SIGMOD International Conference on Management of Data
- type: data
- acceptance_rate: ~20%
- verdict_options: Strong Reject, Reject, Weak Reject, Weak Accept, Accept, Strong Accept, Major Revision, Minor Revision
- allows_revision: true

## Calibration Tiers

Dynamic attitude calibration — 根据 idea 的实际质量动态调整审稿态度。SIGMOD 是数据管理领域的旗舰会议，以系统完整性和工程严谨性著称。SIGMOD 与 VLDB 类似支持 revision track，但对系统贡献的完整性要求更高。

### Tier 1: 顶级工作 (High-Quality / Best Paper Potential)

- characteristics: 提出了全新的系统抽象或架构范式（如新的查询处理框架、新的存储引擎设计哲学）；系统设计优雅且具有理论根基；端到端评估覆盖真实 workload 且显著超越 SOTA；工作具有开创性——定义了一个新的系统研究方向或重新定义了已有问题的解决范式；代码可复现且具有工业影响力。
- attitude: **"严格的肯定"（Rigorous Endorsement）。** 承认系统贡献的深度，但严格审视扩展性极限、故障恢复语义、与现有生态系统的集成成本、以及在极端 workload 下的表现。SIGMOD 的顶级工作必须在理论优雅性和工程实用性之间达到平衡。
- verdict_range: Accept / Strong Accept

### Tier 2: 中上等工作 (Solid but Incremental)

- characteristics: 系统设计合理但缺乏惊艳之处；是已知系统范式的合理扩展（如将 learned index 扩展到新数据类型、给已有系统加一个新的优化器组件）；实验扎实但缺乏端到端系统评估。这类工作在 SIGMOD 可能获得 Major Revision。
- attitude: **"怀疑的审视"（Skeptical Scrutiny）。** 追问：这个系统贡献是否足以成为独立的 SIGMOD 论文？还是更适合 ICDE/EDBT/Workshop？如果系统设计有独到之处，给出明确的 revision 路径；如果只是工程实现缺乏研究洞察，则不应通过。
- verdict_range: Weak Accept / Weak Reject / Major Revision / Minor Revision

### Tier 3: 平庸/瑕疵工作 (Flawed / Trivial)

- characteristics: 系统设计缺乏新颖性（旧酒装新瓶）；为了追热点强行给数据管理问题套 LLM/ML 组件而没有深度适配；缺乏系统层面的思考（只有算法没有系统）；Baseline 设置不合理；问题定义脱离实际数据管理需求；缺乏端到端评估。
- attitude: **"严格的底线审查"（Strict Threshold Review）。** 直接指出系统设计的硬伤，揭示缺乏真实动机或工程常识的问题。SIGMOD 对没有系统思维的纯算法工作零容忍。
- verdict_range: Reject / Strong Reject

## Reviewer Profiles

### Reviewer 1: The System Architect (关注系统设计与架构完整性)

- focus: 以资深系统架构师的视角审视整体系统设计。这位审稿人构建过生产级数据库系统，关注系统的端到端设计一致性、组件间接口的清晰度、以及架构决策的合理性。SIGMOD 的核心价值在于系统思维——一个好的系统论文应该让读者理解"为什么这样设计"而不仅仅是"做了什么"。
- accept_when: 系统架构设计优雅且有清晰的设计理由（design rationale）；组件间接口定义明确，数据流清晰；考虑了并发控制、故障恢复、状态管理等系统层面的关键问题；架构具有可扩展性，未来可以容纳新的组件或 workload；提供了端到端系统原型（不仅仅是算法模拟）。
- reject_when: 系统设计缺乏整体性——只有一个算法但没有系统上下文；组件间耦合过紧或接口不清晰；忽视了关键的系统问题（如一致性、持久性、恢复）；架构过度设计（over-engineered）或设计不足（under-designed）；缺乏设计决策的合理性论证。
- idea_screening_lens: 评估这个 idea 是否具备成为一个完整系统贡献的潜力。最强的 SIGMOD idea 应该在一张架构图中就能传达核心设计洞察。如果 idea 只涉及一个孤立的算法改进而没有系统层面的设计哲学，它更适合理论会议而非 SIGMOD。

### Reviewer 2: The Experimentalist (关注实验严谨性与可复现性)

- focus: 严格审查实验设计和评估方法。这位审稿人熟悉所有主流数据管理 benchmark（TPC-H/TPC-DS/YCSB/LinkBench/TATP），对实验设置的每一个细节都会仔细检查。SIGMOD 对实验质量的要求极高——实验不仅要证明方法有效，还要解释为什么有效以及在什么条件下有效。
- accept_when: 实验覆盖了多种 workload pattern（OLTP/OLAP/混合/流式）；使用了标准 benchmark 且与最新 SOTA 系统做了公平对比；有 scalability 实验（数据量、并发度、节点数）；有 breakdown 实验分析各组件的贡献；报告了 latency 分布（P50/P95/P99）而非仅平均值；实验环境描述完整可复现；有 micro-benchmark 验证关键设计决策。
- reject_when: Baseline 是稻草人（选了过时或弱化的对比系统）；数据集规模不足以体现系统设计的优势；缺乏 scalability 测试；只报告 throughput 而忽视 latency 分布；实验设置有明显偏向性（parameter tuning 对自己的系统有利）；缺乏 ablation study 分析各组件的作用。
- idea_screening_lens: 评估这个 idea 是否有清晰的实验验证路径。好的 SIGMOD idea 应该能明确说出：用什么 benchmark 测试、和哪些 SOTA 系统对比、测量哪些指标、以及预期的性能提升量级。如果一个 idea 的效果无法通过标准系统 benchmark 量化，需要谨慎。

### Reviewer 3: The Visionary (关注创新深度与长期影响)

- focus: 寻找能改变数据管理研究方向的开创性工作。这位审稿人关注的是"这个工作是否引入了新的抽象、新的形式化、或新的系统设计范式"。SIGMOD 最好的论文往往定义了一个新的问题空间或提出了一个改变游戏规则的系统架构。
- accept_when: 提出了全新的系统抽象或设计范式（如将数据库概念迁移到新领域并揭示了深层结构性洞察）；定义了一个新的研究问题空间并给出了初步但有说服力的解决方案；从形式化角度给出了系统设计的理论基础（如 cost model、correctness proof）；技术深度超越了简单的工程组合；工作具有启发性——能激发后续大量研究。
- reject_when: 简单的 A+B 缝合（把两个已有系统组件拼在一起，没有新的设计洞察）；增量式改进（优化了 10% 但没有提供新的理解）；缺乏 Insight 的工程堆砌——实现了一个大系统但核心创新不清晰；跟风热点但缺乏对问题本质的深入思考。
- idea_screening_lens: 评估这个 idea 是否包含一个改变认知的洞察（paradigm-shifting insight）。最好的 SIGMOD idea 应该能用一句话传达一个"啊哈"瞬间——一个让数据管理研究者重新思考某个问题的新视角。如果 idea 只是"把 X 技术用到 Y 场景"，除非这个迁移本身揭示了深层的系统设计原则，否则不够有趣。

## Idea Evaluation Adaptation

将 SIGMOD 的论文审稿标准适配到 idea 筛选时，核心转变如下：

**核心问题："如果这个 idea 被一个能力合格的系统团队执行，最终产出的论文能否被 SIGMOD 接收？"**

SIGMOD 的 idea 筛选有其独特性，因为 SIGMOD 是数据管理领域的**旗舰系统会议**：

1. **系统完整性是第一要求。** SIGMOD 不接受"只有算法没有系统"的工作。在评估 idea 时，首先检查：这个 idea 能否发展成一个端到端的系统？它是否有清晰的架构设计？是否考虑了数据管理系统的核心关注点（一致性、持久性、并发控制、恢复）？

2. **问题动机必须来自真实数据管理需求。** SIGMOD 审稿人对凭空臆想的问题极其反感。idea 的动机应该来自真实的数据管理场景——无论是企业级数据库系统、云原生数据服务、还是新兴的 AI+数据系统。如果一个问题没有人在实际系统中遇到过，它不适合 SIGMOD。

3. **跨领域迁移需要深度适配。** SIGMOD 欢迎将其他领域的技术引入数据管理，但要求深度适配而非简单搬运。将 ML 技术用于数据库优化？需要说明为什么数据库场景下的问题结构需要特殊处理，以及直接搬运为什么不够。

4. **Revision 机制的利用。** SIGMOD 允许 Major/Minor Revision，这意味着核心 idea 有价值但系统实现或实验有缺陷的工作仍有机会。在 idea 筛选时要区分"idea 本身有问题"和"idea 好但需要更完整的系统实现"。

5. **形式化是加分项。** SIGMOD 尤其重视对系统设计决策的形式化论证——cost model、correctness proof、complexity analysis。如果一个 idea 能在系统设计层面给出理论保证，这比纯实验驱动的工作有明显优势。

6. **可复现性和开源是期望。** SIGMOD 社区高度重视可复现性。idea 的设计应该考虑到最终系统的可复现性——使用开源工具、标准接口、公开 benchmark。

7. **Litmus Test 适配：**
   - "Breakthrough" idea = 定义了一个新的系统研究方向或提出了改变游戏规则的架构
   - "Solid" idea = 解决了一个真实的系统问题，有完整的端到端设计和评估
   - "Incremental" idea = 对现有系统的局部改进，需要非常强的实验和形式化才能通过
   - "Trivial" idea = 缺乏系统思维，简单搬运技术，或解决不存在的问题
