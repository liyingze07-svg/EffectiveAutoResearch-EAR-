# stage r3_triage_feasibility — 响应模式 + 实验可行性阶梯

> 新引擎上下文。concern_ledger → 响应模式 + 去重实验队列。核心:**实验是 warrant 不是目的**,大多数 concern 不需新实验。

## 槽位 `{{SLUG}}`
## 输入(只读):`concern_ledger.json`、`evidence_map.json`、`harness/shared-assets/experiment-ladder.md`(§0 可行性阶梯)。

## 规则(每个 concern)
1. 判响应模式:A 澄清 / B 已有证据 / C 补实验 / D 补文献 / E 让步 / F 反驳。
2. **先给 concern 定 `priority`(决定补实验的积极程度)**:
   - **P0 = reviewer 明确点名要实验 / 质疑「泛化性·缺实验·缺 baseline·未验证·只在 X 上测过」**的 concern(尤其 OA≤3 的攻坚 reviewer)。这类 concern 的心结就是「拿证据来」,写作糊弄不过去。
   - P1/P2 = 锦上添花或次要澄清。
3. **C 类走 warrant 回退阶梯**(experiment-ladder 阶梯表:1已有→2论证无关→3更便宜代理→4pilot→5文献→6让步→7真做E),但**按 priority 分档**:
   - **P0:默认走档 4 `pilot`(小规模真实验,能复用已有基建/数据/代码就跑)**。只有 pilot 明确不可行——无可复用基建 / 需真人标注 / 远超预算/时间——才降到档 6 让步,且**必须填 `pilot_rejected_reason`**。绝不因「省事 / 写作能绕」直接滑到让步。
   - P1/P2:能复用基建且耗时小才补,否则走已有证据 / 让步。
4. **诚实闸(硬)**:任何 concern 落到「E 让步」之前,必须显式回答「能不能用 pilot 补?」——`pilot_rejected_reason` 为空则**不许**标让步。让步是 pilot 被否决后的兜底,不是默认档。
5. 真需实验的 → 写 `experiment_request`,**按规格去重**成论文级队列,每个带 `serves:[concern/reviewer]` + `priority`。

## 输出:`concern_ledger.json` 补 `response_mode` + `priority`(+ 让步的补 `pilot_rejected_reason`);`campaigns/{{SLUG}}/ledger/experiment_queue.json`（去重 experiment_request,带 serves[] + priority）。receipt:`{n_by_mode, n_experiments_queued, n_pilot_P0}`。
