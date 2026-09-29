# strategies.md — r6 的 3 个融合并行策略（MoE 池）

r6 并行跑这 **3 个策略**(不是 7 个——eval 教训:复杂≠更好,多智能体/逐点式实测垫底)。每个都走论证编译器;三者**互相拉开、覆盖风险谱**,好让 MoE 选择真正探索不同区域。verify 选最高分 → 过门 → 不过 carry-forward 再 roll( / moe_loop.py)。

融合自 `LZQ/.../agent_rebuttal_eval` 的 7 专家(取其强、去其弱)。

---

## ① 证据锁定·结构化（低风险锚）
融合:EvidenceLocked_CriticRevise + 论证编译 + 证据先行。

- **事实安全优先**:绝不声称未做的实验;缺结果一律 `[TBD]` + action item;无 raw 支撑的数字不写。
- **论证编译**:每个 concern 建 DAG,每句 = 一个 warrant 绑真实证据的 claim 节点。
- **证据先行**:每段开头甩最强证据夺回框架,不先复述 reviewer 的攻击。
- **定位**:我们门下 EvidenceLocked 已排第 1(唯一清 bar)。弹药自控最好,是保底锚。

## ② 审稿人说服·讨论预判（高 raise 潜力）
融合:RebuttalAgent_TSR + AgentReview_AuthorReviewerAC。

- **先内部推断**(隐藏分析,不写进正文):这个 reviewer 到底要什么?哪些是**根本**顾虑、哪些是**可解决**的?什么能真正说服 TA?
- **模拟讨论**:预判 reviewer-author-AC 在讨论阶段会怎么走,针对"会改变 TA 意见的那一点"发力。
- **最敢答**(eval 里 raise 率最高),但风险也最高 → **靠弹药门 grep==0 硬约束**,别为了敢答递弹药。

## ③ 补证据规划·多阶段（弱稿翻盘）
融合:Paper2Rebuttal_MultiStage + 让步。

- **多阶段**:先归纳 concern → **列出"需要补什么实验/证据"** → 交实验执行模块(见 shared-assets/experiment-ladder.md)跑出真实结果 → 再写针对性回复。
- **对接实验模块**:这条策略天然是 r4a 实验分支的消费者——弱稿唯一能翻盘的路(纯写作过不了门,得补真证据)。
- **优雅让步**:补不了的真实弱点,认 + 划 scope,不空承诺("we will" 是弹药)。

---

## 三条共用铁律
1. 都走论证编译,每句可追溯 warrant。
2. 终稿弹药 grep==0(strategy② 尤其要盯,它最敢答)。
3. 只写真跑出来的实验结果(strategy③ 尤其),`[TBD]` 而非空承诺。
