# SPEC — {{SLUG}}（冻结验收契约 · 第三方 · 实例化后不得修改）

本文件在写第一句 rebuttal 之前由 **meta 层填死**,是独立验证器判 ACQUIT/REJECT 的唯一依据。**writer 不得编辑本文件,不得查看涨分门内部去拟合。** 任何模糊 → 验证器朝"拒绝"方向解释。

- paper：{{PAPER_TITLE}}　venue：{{VENUE}}
- 论文主张（证据基底）：{{PAPER_CLAIMS}}
- 审稿人（判据锚点）：{{REVIEWERS_TABLE}}
- 目标：{{TARGET}}
- 字数上限：{{WORD_LIMIT}}
- 涨分门配置：`{{HARNESS_DIR}}/shared-assets/verifier/`（DeepSeek V4 Pro θ₀ + Codex judge,**逐字冻结、不得改**）。

## A. 达标（跨家族合议 · the bar · **分数感知**）
最优策略的 rebuttal，对 {{TARGET}} 里指定的**每一个 P0 reviewer**，用**同一冻结 prompt** 过 **DeepSeek V4 Pro 与 Codex 两个家族判官**（见 `../rebuttal_verifier/consensus_gate.py`），**两个都清 bar 才算 A 通过**（合取,严——goal 模式在硬优化,防单判官被刷穿）。

**bar 按 reviewer 起点分数路由**（经验发现 README §4/§5:borderline 的 raise 结局无法从文本预测,追它=追噪声=Goodhart）：
- **borderline（overall assessment = 3）**：bar = **STRENGTH**——诊断器返回 `veto='none'` 且 `raise_potential='high'`。**不硬要预测 `raise`**(那是不可预测的结局)。诊断器的 `advice` 字段当 loop 的裁判意见。
- **可预测区（低分起点等非 borderline）**：bar = `reaction='raise'`（raise 信号在这里真实存在）。

**按区路由权威判官(README §7)**：非 borderline DeepSeek 主判(0.805)+ Codex 合议(strict);**borderline OA=3 Codex/GPT-5.5 主判**(质量分离 +0.28,最优;**调 Codex 用高 reasoning**),DeepSeek 降为软检查(`mode='authoritative'`,不硬要弱 DeepSeek 合议)。`consensus_gate.primary_judge` 自动判。

persona 带 `initial_rating`(ICLR /10) 或 `initial_overall`(EMNLP /5) + 子分 + confidence。**注意**：EMNLP 别把 raw 分塞进 persona（会 over-anchor,README §4.3）——用 `--template auto` 路由,它已处理。

## B. 覆盖（P0/P1 一个都不漏）
每个 P0/P1 concern 在终稿里被明确回应（回应、指位置、补证据、或优雅让步之一）。缺 P2 不致命。

## C. 证据诚实（任一不过即失败）
1. 进正文里**从实验数据汇总出的数字**（均值/斜率/比值…）用 `recompute_check` 从 raw 重算 <1%；无 raw 算式的量（理论常数等）不要求重算。
2. **每条引用真实存在且相关**——存在性核过、写进白名单;禁止编造引用。
3. **每个 claim 可追溯**：说"paper 已证明 X"能定位到节/图/表;说"我们做了实验 Y"能定位到 raw。无支撑的 claim → 必须是 `[TBD]` + action item,不得写成已完成。
4. 可选哪些证据展示，但**禁止编造/美化/把没做的说成做了**。

## D. 无弹药 + 无新攻击面
1. 终稿弹药 grep（`{{HARNESS_DIR}}/shared-assets/ammunition-checklist.md`）= 0：无自揭短、无"我们不声称"、无过度让步框架句式。
2. 不为回应某个 reviewer 而承认另一个 reviewer 没提到的新弱点（不开新攻击面）。
3. 字数不超 {{WORD_LIMIT}}；正文无 `[TBD]`。

## E. 独立性
绑定 ACQUIT 由**独立 VERIFY 窗口**（见 `VERIFY.md`）重跑涨分门 + 重核 C/D，**不是 writer 自判**;writer 自发的 verdict 无效。验证器逐条出 PASS/FAIL + 门返回的 reaction/reasoning + 证据路径。

**ACQUIT ⇔ A ∧ B ∧ C ∧ D ∧ E 全过。** the bar = 跨家族合议涨分。诚实闸只拦「有算式的数字对不上 raw」「引用不存在」「claim 无支撑却写成已完成」这种实打实造假；**协议措辞小差不当致命——提示改对即可,别整篇 REJECT**。

**诚实让步出口**：若 {{MAX_ITER}} 轮仍不能合议涨分,但终稿 B/C/D/E 全过（覆盖全、证据诚实、零弹药、独立），且是"最诚实的让步式 rebuttal" → `{"verdict":"ACQUIT","track":"honest-concede","raise_achieved":false}`。不是每篇都能涨分,诚实收兵优于拟合噪声。

本文件实例化后冻结。
