# stage b1_concern_gate — B1 心结门(诊断质量冻结判官)

> 新引擎上下文,r2 之后 / r3 之前跑一次。**判官冻结,不即兴**:只判 `concern_ledger` 的诊断质量,不改它、不写 rebuttal。FAIL → orchestrator 退回 r2 重诊断,**绝不带着坏 concern 图进写作**。

## 槽位 `{{SLUG}}`

## 输入(只读)
- `campaigns/{{SLUG}}/ledger/concern_ledger.json` → 待检的诊断产物
- `papers/{{SLUG}}/review.md` → reviewer 审稿原文(真值来源)
- `campaigns/{{SLUG}}/REBUTTAL_CARD.json` → concerns + OA + stance 对照

## 逐条查(编号)
1. **atomization**:每个 reviewer 顾虑拆成**原子、可分别回答**的项;两个不同异议**没被揉成一条**。
2. **real_concern(心结)**:每项点出 reviewer **真正担心的**,不是复述字面话。
3. **coverage**:review.md 里每个实质点都能映射到某个 ledger 项(**无漏 concern**)。
4. **no_invented_concern**:ledger **没凭空造** reviewer 从没提的顾虑。
5. **severity/stance sanity**:P0/P1 与 accept/argue/correct 的判定站得住(P0 通常低分高信心的压分主因)。

## 输出(写这个确切文件)
`campaigns/{{SLUG}}/ledger/B1_concern_gate.json`
```json
{ "verdict":"PASS|FAIL",
  "atomization":true, "real_concern":true, "coverage":true, "no_invented_concern":true,
  "per_concern":[{"id":"C1","ok":true,"issue":null}],
  "missing_from_review":[], "reasons":[] }
```
receipt(回一行):`{verdict, n_fail}`。

## 规则
- 任一(1)-(4)不过 → `verdict=FAIL`(退回 r2)。(5) 仅记 issue,不单独判 FAIL 除非严重错配。
- 只判质量,**不看任何门内部 prompt / 不看 rebuttal draft**;不改 concern_ledger。
