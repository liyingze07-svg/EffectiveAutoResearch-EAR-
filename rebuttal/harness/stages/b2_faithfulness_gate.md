# stage b2_faithfulness_gate — B2 忠实门(no_fabrication 硬门)

> 新引擎上下文,跑在**已过涨分/强度门的选中 draft** 上。这是 GOAL.md `no_fabrication` predicate 的机械落地。**判官冻结**。**这里 FAIL 直接拦掉 PASS**——是 E 级(造假)红线执法,不是改写建议。

## 槽位 `{{SLUG}}` `{{REVIEWER}}` `{{DRAFT_PATH}}`

## 输入(只读)
- `{{DRAFT_PATH}}` → 待查的 rebuttal draft
- `campaigns/{{SLUG}}/ledger/evidence_pool.json` → 真实证据 + `evidence_status`
  🔴 **此文件缺失时不得退回 `evidence_map.json`**:后者是 r1 产的**未过滤**证据底,没有 `evidence_status`、没有 ACCEPT/PARTIAL 验收过滤。拿它当证据源 = 第 3 条"实验诚实"失效。缺失时**直接判 `verdict=BLOCKED`**,`reasons` 写明"evidence_pool.json 缺失,r5 证据合并未跑,无法核验实验验收状态",不要给 PASS 也不要给 FAIL。
- 相关 `campaigns/{{SLUG}}/experiments/<expid>/results.json` → `derived` 真实数字

## 逐条查(编号,红线)
1. **数字有源**:draft 里每个定量 claim / 数字都能追到 evidence_pool 或 results.json 的真实 `derived` 值。**无源数字 = 造假**。
   **容差(精度感知,两条满足其一即通过)**:
   - **舍入相容(先判这条)**:把真实 `derived` 值按 draft 里**该数字实际书写的精度**(小数位/有效数字)四舍五入,若等于 draft 写的值 → 通过。
   - **相对误差 <1%**:书写精度足够高时用这条。
   两条都不满足 → 造假。
   > 为什么不是固定 <1%:对小数值,固定相对容差**在数学上不可满足**——真实值 `0.0075218` 在散文里最诚实的一位有效数字写法就是 `0.008`,相对误差必然 6.4%,固定 1% 会把**诚实舍入判成造假**。这是 CHANGELOG 记过两次的同一类"门刚性假阳性"(v0.7/v0.8 放松 X3/X5 的理由相同)。判据要惩罚的是**编造**,不是**舍入**。
2. **引用真实**:每条引用/结果确实存在于论文资产/证据里,**无编造引用**。
3. **实验诚实**:没把任何**无 ACCEPT/PARTIAL 验收**的实验说成"做了"。
4. **无假装事实的 `[TBD]`**:凡当作事实陈述的地方不留 `[TBD]`。
5. **不过度声称**:claim 不超过证据支持范围(无 FAIL→PASS 粉饰、无夸大 delta、无 `unmet` 证据当 `met` 用)。

## 输出(写这个确切文件)
`campaigns/{{SLUG}}/ledger/B2_{{REVIEWER}}_faithfulness.json`
```json
{ "verdict":"PASS|FAIL",
  "checked_numbers":[{"claim":"+2.3% over X","value":"2.3","source":"results.json#derived.delta","ok":true}],
  "invented_citations":[], "unsupported_claims":[], "overstatements":[], "reasons":[] }
```
receipt(回一行):`{verdict, n_unsupported}`。

## 规则(硬)
- **任一无源数字 / 编造引用 → `verdict=FAIL`**:draft 不得 PASS,loop 必须改掉或诚实让步。
- 只机械核对事实对源,**不判说服力、不看涨分门内部**、不改 draft。
- 数字对不上源、或 source 指不到真实文件 = 该项 `ok:false` = FAIL。
