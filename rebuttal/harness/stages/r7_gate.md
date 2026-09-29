# stage r7_gate — 涨分门(判官调用)

> 不是自由 prompt——用冻结的 `consensus_gate`。orchestrator 调用,不即兴。

## 输入:`{review, reviewer_profile(v2风格,含OA), initial_overall, rebuttal}`
## 机制(见 `rebuttal_verifier/consensus_gate.py`)
1. **DeepSeek** 侧(Python):`deepseek_judge(case, template='auto')` → OA=3 走诊断器 / 其余走 v2。
2. **Codex** 侧(权威主判,OA=3 用高 reasoning):`codex_prompt(case,'auto')` 喂 `mcp__codex__codex` → `parse_codex`。
3. `consensus(ds, codex, case)` → 分区路由:OA=3 authoritative(Codex 主)/ 其余 strict(两家都清)。
4. `bar_met` 按分区(见 GOAL.md)。
5. 前置守卫:`ammo_hits(rebuttal) == []`(弹药门);persona **绝不喂最终 label**。

## 输出:`campaigns/{{SLUG}}/ledger/round{{N}}-gate.json`(每 reviewer 每策略的 ds+codex judgment + consensus + 选中)。
## 规则:worker 看不到本阶段内部 prompt;判官冻结不改;停机必须跨家族合议。
