# CRAFT.md — rebuttal 共享大脑（每个策略、每次写作必读)

> 这是"rebuttal 写得好不好"的核心。3 个 MoE 姿态(s1/s2/s3)都**建立在本文件之上**;姿态只决定差异化的取舍,底层手艺一律照这里。蒸馏自 paper-rebuttal skill 的 `strategy_playbook.md` + `stance_playbook.md`(更全的案例见 skill `examples/case_library.md`)。

## 0. 五条总则(适用所有 concern)
1. **答心结,不答字面(Jiu-Jitsu)**:化解的是 r2 诊断出的 `real_concern`,不是 reviewer 那句原话。字面对了、心结没碰,不动分。
2. **Clarify + Justify 混用**:别整篇认错(显得贡献站不住),也别整篇辩护(显得听不进)。每条回应"认合理部分 + 正面给证据"搭配。
3. **给台阶**:reviewer 改分有心理成本。措辞让他能自然说"the authors clarified my concern",把误解框架化为"我们没写清楚",哪怕是他没细读。
4. **先答后证**:第一句就是答案 → 证据(节/表/数字)→ 影响 → 怎么改。
5. **data beats arguments**:能用数字解决别用形容词。没数字 → `[TBD]` + action,绝不编。

## 1. 立场三分流(先判,再落笔)
| 情形 | 立场 | 纪律 |
|---|---|---|
| **① 事实错误**(reviewer 说了论文没有/相反的) | 坚定纠正:"We respectfully clarify/note that ..." + 页码级证据 | 别怕冲突就把"他错了"说成"我们没写清楚"(除非确实是) |
| **② 合理批评**(真问题) | 体面承认:只认到那一点 + 附具体修复,把"承认"转成"已解决" | 认 clarity ≠ 认 soundness 崩;认一个局限 ≠ 认贡献不成立 |
| **③ 灰色地带**(设计选择/scope/偏好) | 辩护优先:有证据就辩,辩护是学术常态 | respectfully disagree 合法;别一 pushback 就退,真说服不了再退到"文中注明这不是唯一选择" |

## 2. 🔴 不滑跪不自爆(= 诚实在实质不在表演;写作硬纪律)
- ✗ **不回应 reviewer 没提的弱点**——rebuttal 是答辩不是忏悔。
- ✗ **不把小问题升级**——clarity 别写成 soundness,typo 别上升到方法缺陷。
- ✗ **不用自我定罪词**——`major weakness / fundamental limitation / our method fails`(真硬伤该在门口就 BLOCK,不写进 rebuttal)。
- ✗ **不表演诚实**——`we honestly concede / will not manufacture / we did not spin it / (conceded) 标签 / 反复 fair criticism`。诚实是不谎报事实,不是把"我很诚实"写出来(显心虚、递软肋)。
- ✓ **承认必同句兜底**:"we acknowledge X, **however** [证据表明影响有限/已缓解/属未来工作]",绝不留光秃秃的"我们承认 X"。
- ✓ **一次 acknowledge 就够**,别每段道歉。

## 3. 14 种 concern type → canonical 打法(默认值;实际以 r2 心结为准)
| concern | 心结 | 打法骨架 |
|---|---|---|
| Novelty/贡献 | Novelty/Substance | 先认最近邻 X 相关 → 列 **3 点本质区别**(task/assumption/evaluation,各带位置)。忌"X irrelevant"/"we are first" |
| Related Work 缺 | Novelty/Evidence | 真漏→大方补 + 当场给区别;没漏→指位置。引用必先核实,绝不编 |
| Motivation/意义 | Substance/Scope | 用**具体场景/数字**重建动机,忌一堆形容词 |
| Soundness/正确性(常 P0) | Soundness | **正面刚不许绕**:推导铺开 + worked example + 引理/文献。含糊=默认他对 |
| Method Clarity | 表面 Clarity 常掩 Soundness | 认表达 + **当场给 revised snippet**;背后是 soundness 就追加正面论证 |
| Experiment/评测 | Evidence(常是某组件没被证明) | 诊断他真要什么(常是关键消融非更多数据)→ 补真数字或解释设计理由 |
| Missing Baseline | Evidence/Novelty | 能跑就跑 apples-to-apples 进正文;赢→主文,不赢→转 robustness/efficiency;跑不完 `[TBD]`;不可比→给理由但先认相关 |
| Ablation/分析 | Evidence/Substance | 给**组件级**证据(去掉该组件指标变化);已有的精确指位并复述数字 |
| Reproducibility | Reproducibility | 指细节确切位置(超参表/伪码/代码链);只承诺能兑现的 |
| Limitation/Scope | Scope | 诚实认 + "影响有限"证据 + 扩展=future work。认边界≠认核心失败;claim 过宽当场收缩 |
| Writing/排版 | Clarity | 谦虚 + 具体修改清单。**P2,一小段带过**,别占主文火力 |
| Ethics/合规 | 流程 | 严肃对待,指 checklist 位置,缺了当场补声明文本 + 具体依据 |
| Reviewer 误读 | 任意 | 礼貌但坚定 + 给台阶:set stage → 指位置 → 框架化为表达问题。证据硬(页码级)语气软。忌"clearly stated"(打脸) |
| Review 本身有问题 | — | 公开只做克制澄清,绝不指责;太模糊→请具体化;满足触发才走 AC 保密评论。不同意/要实验/嫌 novelty 弱都**不**构成 |

## 4. Response action 措辞骨架(证据槽位必来自 evidence_map,不能编)
Clarify: "We respectfully clarify that ... (Sec X)" · Correct: "We respectfully note [fact] + 页码证据" · Concede&Fix: "We agree this deserves improvement; we have revised ... to '...'" · Provide Existing: "This is in Table 3, where ... shows ..."(必须说在哪+说明什么) · Add Experiment: "We have run ...: [table]. This shows ..."(没跑用 `[TBD]`) · Compare: "We agree X is related. We differ in (1)..(2)..(3).." · Narrow Claim: "We have revised the claim to '...'" · Reframe Scope: "A full treatment of X warrants a separate study; our scope is ..., because ..." · Defend: "We chose ... because ...; empirically Table Y shows ..."(忌无出处 "standard practice") · Acknowledge Limitation: "We acknowledge ...; results suggest impact is limited (证据); future work: ..." · **Defer to Revision: 能现在做的别用这条**。

## 5. 心结 → pattern 速查
Substance→展示已有分量证据(规模/深度/消融)+ 必要时补一个最有说服力的关键实验。Soundness→正面论证铺开,绝不绕。Novelty→task/assumption/evaluation 三维区分,先认相关。Evidence→直接给数据。Clarity→认表达 + revised snippet + set stage。Scope→认大方向重要 + 论证本文 scope 合理 + 扩展=future。Reproducibility→精确指细节位置。

## 6. 对外呈现 = 应答编译(主方法:`strategies/write-direct-rebuttals.md`)
> §0–5 是**内部 logic**(想清楚该答什么心结、用什么证据、什么立场)。**最终 reviewer-facing 稿按 `write-direct-rebuttals.md` 的应答编译范式产出**:rebuttal = 对每个 reviewer slot 的**最小、字面、诚实直接应答**的编译,**directness 压倒一切修辞**。核心对外原则(细节读方法文件):
- **不写致谢/复述好评段**,直接进 W1;给台阶靠答案内部的**正向框架化**("we did not state this upfront; in the camera-ready we will state it"),不靠开场恭维。
- **W 标号 verbatim 引用 reviewer 原句**(不概括);每条**第一句字面槽位直答**、mirror 主谓宾(`What is X?`→`X is…`),机制/证据留后。
- **多部分问题的每个 clause 必答**;礼貌语不当独立问题。
- **时态三分**:理论现在时 / 完成实验完成时 / **手稿编辑将来时 "In the camera-ready we will…"**;⚠️**不许假装已改**("is now stated" / "the revised X reads")。编辑类 `we will` 合法,禁的只是"用承诺搪塞 reviewer 要的实质/实验工作"。
- **边界写成正向技术条件**,不写 apology/limitation;不 volunteer 未问弱点,不把实质反对说成"only a clarity issue"。
- **deletion test**:每句必须承担 answer-slot / 定义 / 连接 / 证据 / camera-ready-edit 之一,否则删。表格仅**多列对比**用,数字能内联就内联,不追求字数。
- (原"谦卑/给台阶"精神保留在 §0.3、§1,但**由答案内部的正向框架化实现,不由开场恭维**;§2 不滑跪不自爆 = ammunition test。)
