# stage r4_experiment_persuasion — 实验说服力门(POST；S 门左移·逐 concern)

> **不是自由 prompt——复用冻结的 `consensus_gate`,和 r7 涨分门完全同构。** orchestrator 在 Python 里跑
> (`orchestrate.experiment_persuasion`),不即兴。**这道门不新增 bar**:它把 r7 那根 `bar_met`
> 提前、逐 concern、对**真实验结果**再问一次。

## 它回答什么(和 r4_accept 的分工)
- **r4_accept(X1-X6)= 实验诚不诚实**(真跑没造假)。过了只证明数字可信。
- **本门 = 实验说不说服**(真结果到底有没有解决它服务的那个 concern,到该 reviewer 分区 bar 要的强度)。
- 一个实验可以 X1-X6 全过(真数据真复跑)却 **null / 双刃 / 打偏心结** —— 诚实但不说服。
  这种结果**绝不能当强点写**(= b3 弹药 C/C2/D),要在 r6 写作**之前**改成下界框架或诚实让步。

## 输入(只读)
- `campaigns/{{SLUG}}/experiments/<expid>/ACCEPTANCE.json` —— 只处理 `verdict ∈ {ACCEPT, PARTIAL}` 的实验;
  取其 `serves`(如 `"vCzF-W4 (long free-form CoT generalization)"` 列表)确定服务的 (reviewer, concern)。
- 同目录 `results.json` —— 只用 `derived` 的**真实数字** + `headline`/`interpretation`(runner 写的诚实解读,非说服优化)。
- `campaigns/{{SLUG}}/REBUTTAL_CARD.json` —— 每个 reviewer 的 `initial_overall`(定分区 bar)。
- `campaigns/{{SLUG}}/ledger/concern_ledger.json`(若有)—— 用 `real_concern` 增强 concern 文本。
- 冻结机器:`rebuttal_verifier/consensus_gate.py`(`deepseek_judge` / `codex_prompt` / `parse_codex` / `bar_met` / `consensus`)。

## 机制(逐个服务的 (reviewer, concern),和 r7 **分区路由**同构)
1. **诚实建桩(只用真数字,不润色)**:把该 concern 的 reviewer 原述 + `results.json.derived` 的真实结果拼成一段
   最小 stub("Reviewer concern: … / We ran an experiment and observed: <真实 derived> / Acceptance: X1-X6 …")。
   **stub 由 orchestrator 用模板确定性拼装,不让任何 LLM 自由写**(防把弱结果吹成强结果)。
2. **case 按 concern 收窄**:`review` 字段 = **该 concern 的原述**(不是整份 review),这样 `bar_met` 判的是
   "这份证据解不解决**这一个** concern",而不是"整篇 rebuttal 完不完整"。`initial_overall` = 该 reviewer OA。
3. **分区路由判(严格镜像 r7 的 `consensus`)**:`primary_judge` 定谁主判——
   **OA=3 border → `authoritative`,Codex 主判(**永远调 Codex**,DeepSeek 只留否决权)**;OA≤2/≥4 → `strict`,两家族都清。
   ⚠️ **不许在 OA=3 让弱 DeepSeek cheap-reject 单方判死**(那是 README §7 说 DeepSeek 最弱、r7 特意让 Codex 主判的分区);
   只有 **strict 分区**(非 OA=3)DeepSeek 是对等家族,它 bar 不过才是合法 cheap-reject。判官 model **必 ≠ 写手**。

## 判据(三档,由**分区主判**决定,不再由 DeepSeek 单方定)
| verdict | 条件(`consensus` 真字段,`prim_ok` = 该分区主判是否清) | 下游 |
|---|---|---|
| **STRENGTH** | `consensus.stop == True`(分区路由下合议清) | r5 记 `met`;r6 当**直接答**写 |
| **LOWER_BOUND** | 没 stop,但**主判清了**(被另一家族否决 / strict 只半清) | r5 记 `partial` + `framing_hint`;r6 写**诚实下界**,禁泛化 overclaim |
| **CONCEDE** | **该分区的权威主判自己都不清**(OA=3 = Codex 不清) | r5 记 `unmet`(即便 X1-X6 ACCEPT);r6 走 warrant 阶梯让步,**禁当强点** |
- 非 STRENGTH 时,把主判的 `why_not_persuasive`(blocker/veto/reasoning)+ `judge_advice` 写进 PERSUASION.json,喂给 **redesign planner** 产"为什么 + 怎么重设计"。
- 判官引擎失败(`__CODEX_ERROR__`/`__TIMEOUT__`)→ 保守判 `LOWER_BOUND`,**绝不因引擎挂了白送 STRENGTH**。
- 无法解析 serves 的 reviewer/OA → 记 warning,该 target 跳过(不静默当 met)。

## 在循环里的位置
本门是 **`EXPERIMENT_LOOP.md` 的停机判据**:`STRENGTH → 停机(WON)`;非 STRENGTH → 驱动 `r4_experiment_redesign` 重设计重跑,到 max_iter/不可行 → 诚实让步。

## `framing_hint`(v0.4 应答编译语言,喂给 r6)
- **STRENGTH** → 「对该 concern **字面直答**:完成时('we ran X and observed Y')+ mirror 主谓宾,不 hedge。」
- **LOWER_BOUND** → 「证据只撑**有界** claim:诚实写下界,**禁**泛化成 'stable/robust/in general'(= b3 弹药,见 02-judgeswap);
  跑过的用过去时,手稿改动用 'In the camera-ready we will …'。」
- **CONCEDE** → 「此结果**不解决**该 concern,**禁当强点**(= b3 弹药 C/D)。走 warrant 阶梯 move-6:
  把局限**一次性**写成**正向技术 scope 条件**后收口;只有合法编辑才加 'In the camera-ready we will …'。」

## 输出(写这个确切文件)
`campaigns/{{SLUG}}/experiments/<expid>/PERSUASION.json`:
```json
{ "expid":"...", "acceptance":"ACCEPT|PARTIAL", "overall":"STRENGTH|PARTIAL|CONCEDE|NONE",
  "targets":[ { "reviewer":"vCzF", "concern":"W4", "serves":"vCzF-W4 (...)", "oa":3,
                "verdict":"STRENGTH|LOWER_BOUND|CONCEDE", "framing_hint":"…",
                "deepseek_ok":true, "codex_verdict":"raise|same|lower|null", "judge_error":null } ],
  "gate":"<GATE_SHA>" }
```

## DO-NOT(硬)
- 不新增 bar:分区强度判据只走 `consensus_gate.bar_met`(单一真相源,改判据仍是三处同改那三处)。
- 不让 LLM 自由写 stub;stub 只含真实 `derived` 数字 + concern 原述。
- 判官 ≠ 写手;停机式判据仍跨家族合议(单 Codex 拟合不算 STRENGTH)。
- CONCEDE/LOWER_BOUND 的实验**结果仍留盘可审计**,只是不当"清 concern 的证据"进池。
