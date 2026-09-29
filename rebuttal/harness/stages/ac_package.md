# stage ac_package — AC 元评论 + 打包交付

> 新引擎上下文,所有 targeted reviewer 收敛后跑。产 Area-Chair 保密评论 + campaign 交付索引。**只基于真实的 per-reviewer rebuttal 与已验收证据**,不引入任何新 claim / 新数字。

## 槽位 `{{SLUG}}`

## 输入(只读)
- `campaigns/{{SLUG}}/REBUTTAL_CARD.json` → paper meta + targeted reviewers
- `campaigns/{{SLUG}}/ledger/loop_results.json` → 每 reviewer 的 status/strategy/round
- 每个终稿 `campaigns/{{SLUG}}/drafts/<reviewer>.md`
- `campaigns/{{SLUG}}/ledger/ACQUITTAL.json`(若有)
- `campaigns/{{SLUG}}/ledger/evidence_pool.json` → 已并入的证据

## 规则(编号)
1. **AC 评论**跨 reviewer 总结:补了哪些实质证据/改动、主要顾虑如何被解决——**只用**各 rebuttal 里已出现的内容 + 已验收证据,**不加新 claim、不写任何 rebuttal 里没有的数字**。
2. **诚实标注**:凡 `status=HONEST_CONCEDE` 的 reviewer,写清让步了什么、还剩什么 open。
3. **无软弹药**:不表演式诚实、不空承诺(与写作同一 ammunition 规则)。
4. **打包索引**:列每个 reviewer 的终稿路径 + status + 胜出策略 + 轮数。

## 输出(写这两个确切文件)
- `campaigns/{{SLUG}}/AC_COMMENT.md` —— AC 保密元评论正文(散文,简洁)。
- `campaigns/{{SLUG}}/ledger/package.json`
```json
{ "paper":"{{SLUG}}",
  "per_reviewer":[{"id":"WaDR","status":"PASS","strategy":"s1_evidence_locked","rounds":1,"draft_path":"campaigns/.../drafts/WaDR.md"}],
  "experiments_used":["02-E-downstream (ACCEPT)"],
  "open_items":["<HONEST_CONCEDE 剩余项>"],
  "generated_by":"ac_package" }
```
receipt(回一行):`{reviewers, passed, conceded, ac_comment_path}`。

## DO-NOT
- 不引入新 claim / 新数字(只复述已在 rebuttal 里的)。
- 不粉饰 HONEST_CONCEDE;不写空承诺 / 表演式诚实。
