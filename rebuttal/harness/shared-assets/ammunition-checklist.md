# ammunition-checklist.md — 弹药 grep 清单（终稿必 0 命中）

"弹药"= rebuttal 里**自己递给 reviewer 的攻击面 / 自揭短 / 过度让步框架**句式。给 reviewer 递现成攻击,本身就是失败。任何 Type-B 门(尤其涨分门)调用前,终稿必须过本清单 grep == 0。

> **⚠️ 权威判定 = 语义门 `b3_ammunition_gate.md`(独立判官,非 grep)。** 正则(`coach_loop.AMMO_PATTERNS`)太静态、追不上"sharpen/streamline/tighten…"的无限变体,也分不清"we will revise X"(弹药)和"the revised X reads:'…'"(不是)。所以正则**已降级为 cheap_eval 里的免费排名提示**,不再当放行门;**PASS 前由 B3 语义判官逐句读全文、按句意判 A–E 类弹药**。本清单是 B3 判官的**判据定义**(给它读),不是给 grep 的模式表。

grep 是**信号**不是真理:命中只是排名 hint,真判定在 B3。宁可改写句式,也别把自我攻击留给 reviewer。

## A. 自揭短 / 泄底（禁止进正文）
- 未测 / 尚未验证 / 还没来得及 / due to time / we did not test
- 留作后续 / future work will / 我们计划 / we plan to（除非是真诚 action item 且不是核心 claim）
- 我们不声称 / we do not claim / 不保证 / no guarantee that
- 诚实地说 / to be honest / 坦白 / admittedly（把让步做成示弱）
- 可能存在问题 / might be flawed / 不确定是否 / it is unclear whether（对自己方法）
- 这确实是个局限 / this is indeed a limitation（未加转折就收尾）

## B. 过度让步 / 认框架（禁止）
- 我们承认这只是 / we agree this is merely / 确实只是组合 / just a combination（认了 novelty 攻击的框架）
- reviewer 说得对,我们的方法 [弱点]（认了没转折）
- 我们同意 [核心 claim] 有问题 / we agree that [C1] is problematic

## B2. 表演式诚实 / 过度让步（软弹药 —— 新增,这次真实跑踩过）
诚实是**不谎报事实**,不是**在正文里反复声明自己诚实**。把"我很诚实"写出来 = 显得心虚 + 递软肋 + 让论文看着更弱。命中即改写(去表白,保留事实):
- we honestly concede / we disclose ... honestly / we did not spin it / honest scope / honest caveat
- we will not manufacture (results) / we prefer to concede ... rather than assert / we are careful not to over-claim
- 每条让步贴 `(conceded)` 标签 / this is a fair criticism（反复)
- 同一 caveat/proxy 反复自我说明("we are explicit that ... not synthetic")——事实陈述一次即可
- 让步展开成一大段(应:一句带过 + 立刻转回强度/scope/补偿证据)
**正确写法**:陈述局限一次→立刻给 scope 或补偿证据→收口。别把诚实做成表演。

## C. 空承诺 vs 合法编辑承诺（区分,别一刀切）
**禁（=弹药）**：用承诺**搪塞 reviewer 要的实质/实验工作**——
- 我们会补跑 X 实验 / we will run/add experiments / provide new results（对 P0 实质 concern）
- 如果被接收我们将 / if accepted we will
- 篇幅所限无法（当作不做的借口）

**合法（不是弹药）**：对**编辑请求**（定义术语/重画图/加引用/调小节顺序）用 camera-ready 将来时——
- `In the camera-ready version, we will define/redraw/add-citation/reorder X`（手稿编辑本就用将来时,直接回应"请定义/加 X"）

## C2. 假装已改（禁止,overclaim）
把**未落地**的手稿编辑写成已完成——命中即改回将来时：
- "is now stated / the revised X reads: '…' / we have revised X to '…'"（rebuttal 阶段论文往往还没 revise → 谎报已完成）
- 正确：`In the camera-ready version, we will …`

## D. 开新攻击面（禁止）
- 为回应 R_i 而主动提及 R_j 没提的弱点
- "另一个可能的问题是…"（自己给自己找茬）
- 引入 paper 里没有、也没证据支撑的新 claim（无 warrant 的断言）

## E. 不诚实（红线,直接失败非改写）
- 把没做的实验说成做了 / 把 [TBD] 写成已完成
- 编造的数字 / 编造或不相关的引用
- 把 FAIL 报成 PASS / 夸大提升幅度

---
grep 实现:对上述句式(中英)做正则扫描 `drafts/final_rebuttal.md`,输出命中行号。A–D 命中 → 改写;E 命中 → campaign 失败(造假),回去重做。
