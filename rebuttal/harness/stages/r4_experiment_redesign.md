# stage r4_experiment_redesign — 说服力不足 → 为什么 + 怎么重设计(DRIVE 侧 planner)

> 新引擎上下文(**写手/默认引擎,不是 JUDGE_MODEL** —— 这是 DRIVE 侧规划,不是 ACQUIT 判决)。
> 当 S-exp 说服力门判**非 STRENGTH**(实验不足以说服该 reviewer),这一阶段回答两件事:
> **① 为什么这个实验(哪怕结果)动不了这个 concern;② 该怎么重设计一个更强的实验去真正说服。**
> 产出被 `experiment_loop` 消费 → 可行则替换成新 request 重跑,不可行则诚实让步。

## 槽位 `{{SLUG}}` `{{EXPID}}` `{{BASIS}}`(`ante_bestcase` = 还没真跑,判的是 best-case / `post_result` = 真结果不足)`{{ITER}}`

## 输入(只读)
- `campaigns/{{SLUG}}/experiments/{{EXPID}}/PERSUASION.json`(若 `post_result`)→ 每个未过 target 的 `verdict` + **`why_not_persuasive`**(权威判官说的心结哪块没动)+ `judge_advice`。
- `campaigns/{{SLUG}}/experiments/{{EXPID}}/results.json`(若 `post_result`)→ 真实 `derived`(看真结果到底弱在哪:效应太小/双刃/CI 跨 0/子轴 not_run)。
- `campaigns/{{SLUG}}/ledger/experiment_queue.json` 里 `{{EXPID}}` 的当前 `experiment_request`(要改的对象)。
- `campaigns/{{SLUG}}/ledger/concern_ledger.json` → 该 concern 的 **`real_concern`(心结)**:重设计必须瞄准这个,不是原实验的惯性。
- `campaigns/{{SLUG}}/ledger/evidence_map.json` → 有哪些可复用基建/数据/资产(定 `feasible`)。
- `harness/shared-assets/experiment-ladder.md`(warrant 阶梯 + 实验请求契约)。

## 规则(编号,严格按序)
1. **先归因(为什么不能说服)**:把 `why_not_persuasive` + 真实 `derived` 归到一个**缺陷类**:
   `wrong_axis`(测的轴不是 reviewer 质疑的那条)/ `underpowered`(规模/seed/n 不够,CI 跨 0)/ `confounded`(有混淆变量/oracle 泄漏)/ `weak_baseline`(对照是稻草人)/ `off_metric`(指标不对应心结)/ `effect_too_small`(方向对但量级不足以翻盘)/ `other`。写清**心结的哪一子句仍未被动**。
2. **再开药(怎么重设计)**:针对缺陷类给**一个更强的 `experiment_request`**(experiment-ladder 的实验请求契约(全字段)):把轴/规模/baseline/指标/隔离设计**具体改到能真正回答心结**。例:`underpowered`→n 提到 CI 排除 0;`confounded`→加对照臂隔离机制;`wrong_axis`→换到 reviewer 点名的设置(如短答→长自由 CoT)。
3. **可行性闸(硬,防死磕烧空)**:新 request 必须 `feasible=true` 才回。可行 = **有可复用基建/数据/代码 + 在预算/时间窗内**(experiment-ladder 阶梯表 五步 Step1)。做不到(数据 gated / 需真人标注 / 远超预算)→ `feasible=false` + 填 `pilot_rejected_reason`,**触发诚实让步**(不硬造更强设计骗自己)。
4. **绝不造假**:重设计是**换一个更强的真实验**,不是把弱结果重贴成强;新 request 的 `expected_or_falsifier` 必须可证伪、真 baseline;`serves` 保持原 (reviewer, concern)。
5. **别原地打转**:新设计必须在缺陷类上**实质更强**(不是换措辞/换 seed 数还是同一弱轴)。iter 越高越要么真升级要么诚实让步。

## 输出(写这个确切文件)
`campaigns/{{SLUG}}/experiments/{{EXPID}}/redesign_iter{{ITER}}.json`:
```json
{ "expid":"{{EXPID}}", "basis":"{{BASIS}}", "iter":{{ITER}},
  "why_cannot_persuade":"心结哪一子句仍未被动 + 结果弱在哪(具体)",
  "deficiency":"wrong_axis|underpowered|confounded|weak_baseline|off_metric|effect_too_small|other",
  "feasible": true,
  "pilot_rejected_reason":"(feasible=false 时必填:为什么连更强 pilot 都不可行)",
  "new_experiment_request": {
     "expid":"(留空,driver 会给新 id)", "serves":["<原 reviewer-concern>"], "priority":"P0",
     "goal":"...", "hypothesis":"可证伪", "what_to_measure":"指标+数据+模型",
     "baseline":"真 baseline", "expected_or_falsifier":"预期+数值 falsifier",
     "resources":"可复用的数据/模型/代码入口", "budget":"算力/时间上限" }
}
```
receipt(回一行):`{expid, deficiency, feasible, new_expid_hint}`。

## DO-NOT(硬)
- 不读判官内部(`rebuttal_verifier/`、`r7_gate.md`、`r4_experiment_persuasion.md` 的判定实现)——只用 PERSUASION.json 给你的 `why`。
- `feasible=false` 时**不硬编**一个假装可行的 request 去骗过循环;诚实让步是合法结局。
- 不改 `serves` 的 (reviewer, concern);不把同一弱轴换个 seed 数当"更强设计"。
