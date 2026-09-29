# Campaign: demo-argument-compiler

你是在本文件夹启动的 Claude Code，要为论文「Learning to Rebut: A First-Principles Argument Compiler」(投 ICLR 2026) 写出一份**在冻结涨分门下预测涨分**的 rebuttal。**先读 `GOAL.md`(任务书)、`REBUTTAL_CARD.json`、`SPEC.md`(冻结验收)。** 输入在本文件夹 `inputs/`(paper + reviews)。

## 要挪动的审稿人
| id | rating | conf | sound | present | contrib | review |
|---|---|---|---|---|---|---|
| R1 | 5 | 4 | 2 | 3 | 2 | inputs/reviews/R1.md |
| R2 | 3 | 4 | 2 | 2 | 2 | inputs/reviews/R2.md |
| R3 | 6 | 3 | 3 | 3 | 3 | inputs/reviews/R3.md |
目标：对 P0 reviewer [R1, R2] 达成 DeepSeek+Codex 合议 raise(min_delta=1)

## 核心信念（两条,别忘）
- **写作是论证编译,不是 next-token 生成**。每个段落有战略目标(把 reviewer 信念从 X 挪到 Y);段落 = 一条 claim 链的编译产物(先建论证 DAG → 查逻辑/冗余/第一性原理 → 渲染 → 反编译校验)。
- **涨分门是唯一 the bar**。不是"写得漂亮",是"DeepSeek+Codex 都预测这个 reviewer 会加分"。你 DRIVE,独立验证器 ACQUIT。

## 东西在哪
- 冻结涨分门：`$AUTOREBUTTAL_ROOT/harness/shared-assets/verifier/`（DeepSeek V4 Pro θ₀ + Codex judge,**不许改/软化/挑拣,不许看内部拟合**）。
- 弹药清单：`$AUTOREBUTTAL_ROOT/harness/shared-assets/ammunition-checklist.md`（终稿 grep 必须 0 命中）。
- rebuttal 分类学 + tips：`$AUTOREBUTTAL_ROOT/harness/shared-assets/rebuttal-tips.md`（concern 分类 + 各类应对 + Poor-Response-Pattern 排雷）。
- 输入：本文件夹 `inputs/`（paper 全文 + reviews + 已有实验 log + 作者备注）。
- 产出：`ledger/`（evidence_map / concern_ledger / round*-gate.json / ACQUITTAL.json）、`drafts/`（每轮每策略的 rebuttal）、`loop_state.md` + `iteration_log.md`。

## 复用的外部 infra
- 涨分门 DeepSeek 侧：`$AUTOREBUTTAL_ROOT/rebuttal_verifier/verify_rebuttal.py`（`verify_one`/`verify_batch`）。
- 第二判官 Codex：`mcp__codex__codex`（OpenAI 系,与 DeepSeek 独立）。
- 补实验（若允许）：复用 ExpAuto 的 codegen/runner/recompute。

## 铁律
- **绝不编实验数字、绝不编引用**；每个 claim 可追溯真实证据,做不到写 `[TBD]`。
- **你 DRIVE,独立验证器 ACQUIT**：跑完别自判——另起 VERIFY 窗口读 `VERIFY.md` 出裁决。绝不看涨分门内部拟合。
- 写作严格走论证编译;每句从段落战略目标长出来,不自由发挥。
- 终稿弹药 grep==0；不开新攻击面；不超字数。
- 停机用 DeepSeek+Codex 合议 raise；达不到 4 轮 → 诚实让步出口,别拟合噪声。
