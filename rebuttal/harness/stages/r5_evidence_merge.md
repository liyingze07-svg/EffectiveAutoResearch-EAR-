# stage r5_evidence_merge — 把已验收实验并进统一证据池

> 新引擎上下文。evidence_map + 已验收实验 → `evidence_pool.json`。**只信过了 X1-X6 的实验数字,REJECT/缺验收一律不进池。**

## 槽位 `{{SLUG}}`

## 输入(只读)
- `campaigns/{{SLUG}}/ledger/evidence_map.json` → 原始证据(paper 定位 / 已有资产 / 让步)
- `campaigns/{{SLUG}}/ledger/concern_ledger.json` → concern 列表(拿 `id` 做绑定键)
- 每个 `campaigns/{{SLUG}}/experiments/<expid>/ACCEPTANCE.json` + 同目录 `results.json`
- 每个 `campaigns/{{SLUG}}/experiments/<expid>/PERSUASION.json`(r4_experiment_persuasion 产)→ 每个服务的 (reviewer, concern) 的 `verdict`(STRENGTH/LOWER_BOUND/CONCEDE)+ `framing_hint`。**这是"诚实≠说服"的裁决:X1-X6 只证诚实,说服力看这里。**

## 规则(编号,严格按序)
1. **诚实准入**:一个实验的 `derived` 数字**仅当** `ACCEPTANCE.json.verdict ∈ {ACCEPT, PARTIAL}` 才可进池。`PARTIAL` 只并**真跑过的子轴**。`REJECT` 或**缺 ACCEPTANCE** → 该实验**排除**,依赖它的 concern 记 `evidence_status="unmet"`。
2. **说服力定档(用 PERSUASION.json,按服务的 concern 逐条)**:诚实过关后,`evidence_status` 由**说服力门**定,不是默认 met:
   - `STRENGTH` → `evidence_status="met"`(可当直接答的硬证据)。
   - `LOWER_BOUND` → `evidence_status="partial"` + 把 `framing_hint` 原样带进池项(r6 写诚实下界,禁泛化)。
   - `CONCEDE` → `evidence_status="unmet"` + `reason="passed X1-X6 but does not resolve this concern (persuasion gate)"`;**不把它的数字当"清 concern 的证据"并入**(结果仍留盘可审计,r6 走 warrant 阶梯让步,**禁当强点**)。
   - **缺 PERSUASION.json 的已验收实验** → 保守记 `evidence_status="partial"` + flag,**不静默当 met**。
3. **只搬 `derived`**:绝不复制 ACCEPTANCE 没过 X3 重算的 raw 数字;只搬 `results.json.derived` 里的量 + 其 `interpretation`。
4. **可追溯**:每条合并项必记它服务的 `concern_id`、`expid`、`derived` 数字、`results.json` 路径、`interpretation`、`persuasion_verdict`、`framing_hint`。
5. **不造假**:实验缺/被拒/被判 CONCEDE 就**显式写出来**(`evidence_status="unmet"` + 原因),绝不用占位数字充数,绝不把 unmet/CONCEDE 悄悄写成 met。

## 输出(写这个确切文件)
`campaigns/{{SLUG}}/ledger/evidence_pool.json` —— 统一池 = 原 evidence_map 各项 + 已验收实验证据,每项:
```json
{ "concern_id":"C1", "source":"paper|experiment|existing_asset|concession",
  "expid":"02-E-...", "numbers":{"...":0.0}, "results_path":"campaigns/.../results.json",
  "interpretation":"这个数字支持/削弱哪个 claim", "evidence_status":"met|partial|unmet",
  "persuasion_verdict":"STRENGTH|LOWER_BOUND|CONCEDE|null", "framing_hint":"r6 怎么框架化这条(v0.4)" }
```
receipt(回一行):`{merged_from_experiments, accepted, rejected_or_missing, concerns_unmet, conceded_by_persuasion}`。

## DO-NOT
- 不进未验收/被拒实验的任何数字。
- 不把 `unmet`/`CONCEDE` 悄悄写成 `met`;不把缺 PERSUASION 的实验默认 met;不编 `interpretation`/`framing_hint`。
