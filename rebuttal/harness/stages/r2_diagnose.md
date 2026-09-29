# stage r2_diagnose — concern 诊断

> 新引擎上下文。review + card → `concern_ledger.json`。

## 槽位 `{{SLUG}}`
## 输入(只读):`papers/{{SLUG}}/review.md`、`campaigns/{{SLUG}}/REBUTTAL_CARD.json`、`harness/shared-assets/rebuttal-tips.md`(分类学)。

## 规则(每个原子 concern)
1. **诊断心结**:reviewer 写下的 vs 真正担心的;是**误读**(paper 其实有)还是**真实缺口**?有无 **frame-lock**(逐条回答也没用,需先打破框架)?
2. 分类(type)+ 定 **P0/P1/P2**(P0=压分主因,通常低分高信心)。
3. 跨 reviewer 聚类:同一顾虑归一份证据(记哪几个 reviewer 提的)。

## 输出:`campaigns/{{SLUG}}/ledger/concern_ledger.json`(每条:`{id, cluster, reviewers[], type, surface, real_concern, misread_or_gap, frame_lock, priority}`)。receipt:`{n_concern, n_P0, n_frame_lock}`。
