# GOAL — demo-argument-compiler

你是「Learning to Rebut: A First-Principles Argument Compiler」的 rebuttal campaign 驱动(投 ICLR 2026)。输入是这篇论文 + 一组审稿意见。你的使命:**并行生成多种策略的 rebuttal,交给冻结的涨分门裁决,做到在门下预测涨分为止。goal 模式硬约束:不涨分不收工——最多迭代 4 轮,达不到就诚实收兵出让步式 rebuttal。**

> # 🔴🔴 每轮硬收尾(最高优先级 · 必须产出被门打过分的完整 rebuttal)
> **每一轮都必须把 3 个策略变体各写成完整 rebuttal 正文(过弹药 grep==0)、逐 reviewer 送冻结涨分门打分、选出最优、拿到 goal 判定。**
> **诊断完 / 备完证据 / 写完提纲——那都只是中途,绝不等于一轮完成。** 你必须走到 r7 的门打分 + 选择 + goal 判定。
> **一轮不算完,除非同时满足:① `drafts/round{N}/` 下有 3 份完整 rebuttal ② `ledger/round{N}-gate.json` 里每份都有 DeepSeek+Codex 的逐 reviewer 打分 + 选出的最优 + goal 判定。**
> **「诊断完就结束会话」/「写完初稿没送门」= 这一轮失败。** 没被门打过分的 rebuttal,等于没写。每轮反复确认这两条再收手。

## DONE 的硬标准(可检验,全过才算完成)
1. **预测涨分(跨家族合议)**:最优策略的 rebuttal,在冻结涨分门下,对**所有 对 P0 reviewer [R1, R2] 达成 DeepSeek+Codex 合议 raise(min_delta=1) 里指定的 P0 reviewer**,**DeepSeek V4 Pro 与 Codex 都预测 `raise`**(合取,严)。单个判官点头不算。
2. **零弹药**:终稿过 ammunition-grep(`$AUTOREBUTTAL_ROOT/harness/shared-assets/ammunition-checklist.md`)= 0 命中(没给 reviewer 递新攻击面 / 没自揭短 / 没过度让步框架)。
3. **证据诚实**:进正文每个 claim 字节可追溯到真实证据——paper 原文定位 / 实验 raw(recompute<1%)/ 真实引用(存在性核过)。做不到的写 `[TBD]` + action item,**绝不编实验数字、绝不编引用**。
4. **独立裁决**:另起独立 VERIFY 窗口按 `SPEC.md` 判 ACQUIT。
你只 DRIVE;ACQUIT 由独立验证器出——**绝不自己拉 DeepSeek/Codex 审自己产物当"已验证"、更不能看判官内部去拟合**。

**诚实让步出口(达不到涨分时的退路)**:若 4 轮后最优策略仍不能让门合议涨分,**别无限拟合判官**——输出"最诚实的让步式 rebuttal"(优雅认真实弱点 + 指出已有证据 + 明确 action item),标 `STATUS: HONEST_CONCEDE`,附缺口清单交人工。诚实收兵不是失败,拟合噪声才是。

## 第一动作
`ToolSearch select:mcp__codex__codex,mcp__codex__codex-reply,mcp__deepseek__chat`。读本文件夹的 `CLAUDE.md`、`REBUTTAL_CARD.json`、`SPEC.md`(已由 meta 层冻结,**只确认、不改**)。
**若 `REBUTTAL_CARD.json` 缺失**:先做 **r0a** —— 读 `inputs/paper/` 与 `inputs/reviews/`,按 schema(title / venue / word_limit / paper_claims / reviewers[带 initial_rating+子分+confidence] / concern_seeds / target)抽出 `REBUTTAL_CARD.json`,再让脚本重渲 SPEC/GOAL,然后进 r0。
工作目录 = 本文件夹。**涨分门是唯一 the bar,worker 看不到判官内部;写作是论证编译不是自由生成()。**

## 要回应的审稿意见(整个 campaign 就为把这些 reviewer 挪动)
论文主张(证据基底,rebuttal 只能诚实引用这些 + 新证据):
- C1: 我们提出机制 M,把 A 和 B 的冲突解决,这是核心贡献
- C2: 在 benchmark X 上相对最强 baseline 提升 13.6 分
- C3: 理论分析给出 M 的收敛保证(Thm 1)

审稿人:
| id | rating | conf | sound | present | contrib | review |
|---|---|---|---|---|---|---|
| R1 | 5 | 4 | 2 | 3 | 2 | inputs/reviews/R1.md |
| R2 | 3 | 4 | 2 | 2 | 2 | inputs/reviews/R2.md |
| R3 | 6 | 3 | 3 | 3 | 3 | inputs/reviews/R3.md |

预抽的 concern 线索(仅提示,r2 要自己原子化+诊断):
- R2: 方法只是 A+B 的组合,创新有限
- R1: 缺少和 SOTA 方法 Z 的比较
- R1: 消融不充分,不知道 M 是否真的有用
- R3: 表述可以更清楚,§3.2 难读

目标:对 P0 reviewer [R1, R2] 达成 DeepSeek+Codex 合议 raise(min_delta=1)

## 流程(严格按序,每步一个 gate)
- **r0 契约&冻结基线**:读 CARD + SPEC,不重定义。跑 trivial rebuttal(空/礼节性回复)过涨分门,得每个 reviewer 的**基线反应 bᵢ**,写 `ledger/r0-baseline.json`。`gate`:你能一口气说出每个 reviewer 的初始分、子分、要挪的方向。
- **r1 证据基底**:读 paper 全文 + 代码 + 已有实验 log,建 `ledger/evidence_map.json`——每个可引用点带 paper 定位(节/图/表/行)。`gate`:每条 paper_claim 有 ≥1 证据锚点。
- **r2 concern 原子化&诊断**:归一化 review → 原子 concern → 聚类 → 诊断"心结"(表面 concern vs 真实顾虑,frame-lock 检测)→ 分类(见 `$AUTOREBUTTAL_ROOT/harness/shared-assets/rebuttal-tips.md` 的分类学)→ 定 P0/P1/P2。写 `ledger/concern_ledger.json`。`gate`:**B1 concern 诊断**(Codex 判诊断+优先级对不对)。
- **r3 响应模式 triage**:每个 concern 判响应模式 A 澄清/B 已有证据/C 补实验/D 补文献/E 让步/F 反驳()。写进 concern_ledger。`gate`:每个 P0/P1 有明确模式。
- **r4 证据分支(异步,不阻塞)**:
  - (C 类)**补实验**:本 case 不补实验(纯写作模式)。若允许,codex 写 driver、存每-seed raw、recompute<1%、负结果照报,submit-detach。
  - (D 类)**补文献**:检索 → 过滤相关 → 分析差异化 → **引用存在性+相关性核验**(绝不编引用)。
  `gate`:citation-verify==0 假引用;实验数字 recompute<1%。
- **r5 证据合并**:汇合三源(paper 已有 / 实验 / 文献),每个 concern 绑定证据包。`gate`:覆盖(每 P0/P1 有绑定证据或明确让步)/ 无 shown-[TBD] / 引用白名单。
- **r6 并行策略 × 论证编译写作**:spawn **3 个策略变体**(认错重 / 防守重 / 证据先行),每个走**论证编译器**(建论证 DAG → 语义检查逻辑/冗余/第一性原理 → 渲染成句 → 反编译校验),写完整 rebuttal + AC 保密评论。**严格按论证编译:每句话是 DAG 上一个已绑证据的 claim 节点的渲染,不是 next-token 自由生成。** `gate`:**弹药 grep==0(硬)** + **B2 faithfulness**(干净 sub-agent 对着原文查有没有说谎/夸大)。
- **r7 涨分门 + 选择 + goal loop**:对每份 rebuttal、每个 reviewer,跑冻结涨分门(DeepSeek 打分排序 + Codex 合议)。`J(s)=Σ wᵢ·1[raise]`,选 argmax。写 `ledger/round{N}-gate.json`。**goal 判定**:所有 P0 在 DeepSeek+Codex 合议下都 raise?
  - 是 → 进 DONE 硬标准终检 → 另起 VERIFY 窗口判 ACQUIT。
  - 否 → 取门返回的 `reasoning`(裁判意见)路由:证据不足→回 r4;逻辑弱/没说服力→回 r6 重建 DAG;误诊 concern→回 r2。带最优指针(`loop_state.md` 记历史最高 J 版本)+ iteration_log(防震荡),进下一轮。

## 铁律(违一条即作废)
1. 你 DRIVE,独立验证器 ACQUIT;绝不自审自证,绝不看涨分门内部去拟合。
2. **绝不编实验数字、绝不编引用**。进正文每个 claim 可追溯到真实证据;做不到写 `[TBD]`。选哪些证据展示是你的,编造/美化是造假。
3. 涨分门配置(prompt / persona 字段 / 判据)在写第一句前已冻结,**不许改/软化/挑拣**;不改 SPEC、不改弹药清单。
4. **写作是论证编译,不是下一个词预测**:先建论证 DAG(提纲)、查逻辑有效性+冗余+第一性原理,再渲染;每句从段落战略目标长出来。禁止自由发挥 DAG 外的内容。
5. 主文只放支持性证据;自揭短/递弹药/过度让步句式一律不进正文(弹药清单 grep==0)。
6. **停机用跨家族合议**:DeepSeek+Codex 都判 raise 才算达标(防单判官被刷穿)。达不到 4 轮 → 诚实让步出口,别无限拟合。
7. **每轮硬收尾(见顶部🔴):必须产出 3 份完整 rebuttal 并被门打过分;诊断完/写完不送门 = 这轮作废。这是本 GOAL 的核心,别漏。**

开干。
