# SPEC — demo-argument-compiler（冻结验收契约 · 第三方 · 实例化后不得修改）

本文件在写第一句 rebuttal 之前由 **meta 层填死**,是独立验证器判 ACQUIT/REJECT 的唯一依据。**writer 不得编辑本文件,不得查看涨分门内部去拟合。** 任何模糊 → 验证器朝"拒绝"方向解释。

- paper：Learning to Rebut: A First-Principles Argument Compiler　venue：ICLR 2026
- 论文主张（证据基底）：- C1: 我们提出机制 M,把 A 和 B 的冲突解决,这是核心贡献
- C2: 在 benchmark X 上相对最强 baseline 提升 13.6 分
- C3: 理论分析给出 M 的收敛保证(Thm 1)
- 审稿人（判据锚点）：| id | rating | conf | sound | present | contrib | review |
|---|---|---|---|---|---|---|
| R1 | 5 | 4 | 2 | 3 | 2 | inputs/reviews/R1.md |
| R2 | 3 | 4 | 2 | 2 | 2 | inputs/reviews/R2.md |
| R3 | 6 | 3 | 3 | 3 | 3 | inputs/reviews/R3.md |
- 目标：对 P0 reviewer [R1, R2] 达成 DeepSeek+Codex 合议 raise(min_delta=1)
- 字数上限：per-reviewer 5000 chars
- 涨分门配置：`$AUTOREBUTTAL_ROOT/harness/shared-assets/verifier/`（DeepSeek V4 Pro θ₀ + Codex judge,**逐字冻结、不得改**）。

## A. 涨分（跨家族合议 · the bar）
最优策略的 rebuttal，对 对 P0 reviewer [R1, R2] 达成 DeepSeek+Codex 合议 raise(min_delta=1) 里指定的**每一个 P0 reviewer**，在冻结涨分门下：
- **DeepSeek V4 Pro** 预测 `reaction=raise`（`quality=high`），**且**
- **Codex**（同 review + rebuttal + persona，独立 prompt）也预测 `raise`。
两个不同家族判官**都** raise 才算 A 通过（合取,严——因为 goal 模式在硬优化,出口要严,防单判官被刷穿）。persona 必须带 `initial_rating` + soundness/presentation/contribution 子分 + confidence（README 证实带 persona 显著提分）。

## B. 覆盖（P0/P1 一个都不漏）
每个 P0/P1 concern 在终稿里被明确回应（回应、指位置、补证据、或优雅让步之一）。缺 P2 不致命。

## C. 证据诚实（任一不过即失败）
1. 进正文里**从实验数据汇总出的数字**（均值/斜率/比值…）用 `recompute_check` 从 raw 重算 <1%；无 raw 算式的量（理论常数等）不要求重算。
2. **每条引用真实存在且相关**——存在性核过、写进白名单;禁止编造引用。
3. **每个 claim 可追溯**：说"paper 已证明 X"能定位到节/图/表;说"我们做了实验 Y"能定位到 raw。无支撑的 claim → 必须是 `[TBD]` + action item,不得写成已完成。
4. 可选哪些证据展示，但**禁止编造/美化/把没做的说成做了**。

## D. 无弹药 + 无新攻击面
1. 终稿弹药 grep（`$AUTOREBUTTAL_ROOT/harness/shared-assets/ammunition-checklist.md`）= 0：无自揭短、无"我们不声称"、无过度让步框架句式。
2. 不为回应某个 reviewer 而承认另一个 reviewer 没提到的新弱点（不开新攻击面）。
3. 字数不超 per-reviewer 5000 chars；正文无 `[TBD]`。

## E. 独立性
绑定 ACQUIT 由**独立 VERIFY 窗口**（见 `VERIFY.md`）重跑涨分门 + 重核 C/D，**不是 writer 自判**;writer 自发的 verdict 无效。验证器逐条出 PASS/FAIL + 门返回的 reaction/reasoning + 证据路径。

**ACQUIT ⇔ A ∧ B ∧ C ∧ D ∧ E 全过。** the bar = 跨家族合议涨分。诚实闸只拦「有算式的数字对不上 raw」「引用不存在」「claim 无支撑却写成已完成」这种实打实造假；**协议措辞小差不当致命——提示改对即可,别整篇 REJECT**。

**诚实让步出口**：若 4 轮仍不能合议涨分,但终稿 B/C/D/E 全过（覆盖全、证据诚实、零弹药、独立），且是"最诚实的让步式 rebuttal" → `{"verdict":"ACQUIT","track":"honest-concede","raise_achieved":false}`。不是每篇都能涨分,诚实收兵优于拟合噪声。

本文件实例化后冻结。
