# stage r6_write — 为一个 (reviewer, 策略) 写一版 rebuttal

> 引擎在**新上下文**里跑本文件。只用下面声明的输入,不带对话历史。产物是**一份 reviewer-facing 的 rebuttal 正文**。

## 槽位(orchestrator 填)
`{{SLUG}}` `{{REVIEWER}}` `{{STRATEGY_FILE}}`（strategies/<s>.md）`{{STRATEGY_ID}}` `{{N}}`（轮次)`{{SEED}}`（carry-forward 种子或 None）

## 输入(只读这些确切文件)
- `campaigns/{{SLUG}}/REBUTTAL_CARD.json` → 取 `{{REVIEWER}}` 的 concerns + OA + stance
- `campaigns/{{SLUG}}/ledger/concern_ledger.json` → 每个 concern 的 **`real_concern`(心结)** + severity + stance(r2 诊断,写作按它定打法)
- `campaigns/{{SLUG}}/ledger/evidence_pool.json`
  🔴 **此文件缺失时禁止退回 `evidence_map.json`,直接停止并报错**。`evidence_map.json` 是 r1 产的**未过滤**证据底:没有 `evidence_status`,**没有把 REJECT 的实验剔出去**。拿它写作 = 会把未验收/被 REJECT 的实验当成已完成证据写进稿子(01-wdData/37ch 实测踩过:稿中把 `01-E-overlap` 写成 "our overlap stress test measured",而该实验 ACCEPTANCE 判定是 REJECT)。缺失时的正确动作:**不写稿**,回报 "evidence_pool.json 缺失,需先跑 r5_evidence_merge"。→ 每个 concern 绑的证据 + `evidence_status`(met/partial/unmet)+ `persuasion_verdict` + **`framing_hint`**。**只用 `evidence_status != unmet` 的真实证据;unmet 的走 warrant 阶梯让步,绝不硬编。**
  - **必遵 `framing_hint`(实验说服力门 r4_experiment_persuasion 的裁决,已按 v0.4 应答编译写好)**:`met/STRENGTH` → 该证据当**字面直答**写(完成时,mirror 主谓宾);`partial/LOWER_BOUND` → 只写**诚实下界**,**禁**泛化成 'stable/robust/in general'(overclaim = 弹药);`unmet/CONCEDE`(即便实验真跑过并通过 X1-X6)→ **禁当强点**,走 warrant 阶梯 move-6 把局限一次性写成正向 scope 条件后收口。
- `papers/{{SLUG}}/review.md` → `{{REVIEWER}}` 的审稿原文
- 相关 `campaigns/{{SLUG}}/experiments/<expid>/results.json` → 只用 `derived` 的真实数字 + `interpretation`
- **`harness/strategies/CRAFT.md` → 内部 logic(总则+立场三分流+不滑跪不自爆+14 concern 打法+心结速查):想清楚**该答什么心结、用什么证据、什么立场**。先读。**
- **`harness/strategies/write-direct-rebuttals.md` → 对外呈现主方法(应答编译):最终 reviewer-facing 稿怎么写。逐 slot 字面直答 / verbatim 标号 / 不寒暄 / 时态三分 / deletion+ammunition。**
- `harness/{{STRATEGY_FILE}}` → 本策略姿态(叠在 CRAFT 之上的差异化取舍)
- 本文件的通用规则(下)

## 写作 = 内部 logic(CRAFT + 论证编译) → 对外应答编译(write-direct-rebuttals)
1. **内部想清楚**:对每个 concern,按 r2 诊断的 `real_concern`(心结)用 **CRAFT §3/§5** 选打法 + **CRAFT §1** 定立场;走论证编译(下)保证逻辑严谨、warrant 可溯。
2. 按 `{{STRATEGY_FILE}}` 的姿态取舍(打什么、顺序、让步深浅)。
3. **对外落稿按 `write-direct-rebuttals.md`(应答编译)**:两遍——先逐 reviewer slot 字面直答(mirror 主谓宾),再编译成每 W 一段连续散文。**verbatim 引用标号、不写致谢段、时态三分(编辑=将来时,不假装已改)、边界写正向条件、过 deletion+ammunition**。逻辑在内部(可留中文 `逻辑：`),直接在对外。见《输出格式》。

## 论证编译(4 pass,严格按序;这是推理任务不是 next-token)
1. **Pass 1 建论证 DAG**:每个 concern 定战略目标(把 reviewer 从 X 挪到 Y)→ 倒推 claim 链 → 每个 claim 挂一个 warrant(指向 evidence_map 里的真实证据)。链终点 = 战略目标。**先不写散文。**
2. **Pass 2 语义检查**:每 claim 能从前驱+warrant 推出(无跳跃)· 每 warrant link 到真实证据(link 失败=编造→降 `[TBD]`/删)· 无冗余 · 终点=目标。
3. **Pass 3 渲染**:DAG→散文,一 claim 节点=一句,连接词编码逻辑边。**下一句必须是下一个节点,不许生成 DAG 外内容。**
4. **Pass 4 反编译校验**:把散文 re-parse 回 claim 集合,必须 ⊇ DAG(没丢/没加语义)。

## 🔴 诚实规则(实质诚实,不是表演诚实 —— 重要)
诚实是**不谎报事实**,不是**在正文里反复声明自己诚实**。后者显得心虚、给 reviewer 递软肋、让论文看着更弱。
- **要**:每个数字/claim 可追溯真实证据;做不到的用 `[TBD]`;让步在真拿不到 warrant 时。
- **不要(这些是软弹药,会被扣分/拦)**:
  - 表演式诚实句式:`we honestly concede / we will not manufacture / we did not spin it / we prefer to concede rather than assert / we are careful not to over-claim / we disclose ... honestly`。
  - 每条让步贴 `(conceded)` 标签、反复说"这是公允的批评"。
  - 过度让步:能自信答的用证据自信答;让步**一句带过 + 立刻转回强度**,不展开、不重复。
- **让步的正确写法**:陈述局限一次(简短)→ 立刻给它的 scope 或补偿证据 → 收口。例:不写 "we honestly have no long-CoT infrastructure and will not manufacture results";写 "Long-form CoT is outside our current scope; the tradeoff already persists at 27B (0.248/0.402), and we mark it as future work."
- **caveat/proxy 只陈述一次事实**(如"junk 是 authenticity-detector 代理"),不加"we are explicit that ... not synthetic"这类自我表白。

## carry-forward(若 `{{SEED}}` 非 None)
在 `SEED.prior_best_rebuttal` 上改:保留有效的,按 `SEED.apply_advice` 补,删 `SEED.avoid_phrases`。不从零重写。

## DO-NOT(硬)
- 不编数字/引用;不把没做的实验写成做了;不空承诺("we will run/add" 对 P0 = 弹药)。
- 不生成 DAG 外内容(Pass 3 锁死)。
- 不写上面的表演式诚实句式 / 不过度让步。
- **DRIVE/ACQUIT 物理隔离(硬):绝不读判官内部** —— 不读 `rebuttal_verifier/`(`consensus_gate.py`/`prompt_template.py`/`verify_rebuttal.py`)、不读 `harness/stages/r7_gate.md`、`b1_concern_gate.md`、`b2_faithfulness_gate.md`、`b3_ammunition_gate.md`、不读 `harness/runner/coach_loop.py` 的 `AMMO_PATTERNS`。只读上面"输入"列的确切文件。看判据 = 对判据拟合 = 整轮作废。

## 输出格式(硬约束 —— **应答编译范式**,主方法读 `strategies/write-direct-rebuttals.md`)
> Directness 压倒修辞:rebuttal = 对每个 reviewer slot 的**最小、字面、诚实直接应答**的编译。CRAFT §0–5 提供**内部 logic**(心结/立场/打法),本节 + write-direct-rebuttals 管**对外呈现**。
1. **不写致谢/复述好评段 —— 直接进 W1。** 给台阶靠答案内部的**正向框架化**(如 "we did not state this upfront; in the camera-ready we will state it before first use"),不靠开场恭维。
2. **W 标号 = 逐字引用 reviewer 原句(verbatim)**,不是概括心结。过长保留完整关键子句,不插造的省略号。(心结概括留内部 logic / 中文 `逻辑：` 文件。)
3. **第一句 = 字面槽位直答**,mirror reviewer 的主/谓/宾(见方法文件映射表:`What is X?`→`X is…`;`Is it A/B/both?`→`It is…`)。机制/证据留第二句起。**禁把 reframe 或恭维当首句。**
4. **多部分问题的每个 clause 都要答**;礼貌语("Can you speak to this?")不当独立问题答,并入其后的实质问题。
5. **时态三分**:已有理论=现在时;完成实验=过去/现在完成时;**手稿编辑=将来时 `In the camera-ready version, we will <具体改动>`**。⚠️**不许把未落地的编辑写成 "is now stated / the revised X reads"(=假装已改=overclaim)**。编辑类 `we will`(定义术语/重画图/加引用/调顺序)**合法**;禁的只是"用承诺**搪塞 reviewer 要的实质/实验工作**"。
6. **表格降级**:仅**多列对比**才用 markdown 表;单一数量/一串同类数字 → 内联散文。**不追求字数**——长度由 **deletion test** 决定(每句必须承担 answer-slot / 定义 / 连接 / 证据 / camera-ready-edit 之一,否则删);无下限焦虑。超长才精简 + 交叉引用。
7. **边界 = 正向技术条件,不是道歉/limitation**("The theorem applies when …",不写"我们没测 X")。不 volunteer 未问的弱点,不把实质反对说成"only a clarity issue"。

## 输出(写这个确切文件)
`campaigns/{{SLUG}}/drafts/round{{N}}/{{REVIEWER}}__{{STRATEGY_ID}}.md` —— reviewer-facing rebuttal 正文,**严格按上面《输出格式》6 条硬约束**(标号 + 先结论 + 表格 + 谦卑开场 + 无未来时空承诺 + 用足 4000–5000 字符)。
receipt(回一行):`{reviewer, strategy, draft_path, char_count, concerns_covered}`。char_count 超 5000 → 精简;低于 3000 → 补足证据密度再交。
