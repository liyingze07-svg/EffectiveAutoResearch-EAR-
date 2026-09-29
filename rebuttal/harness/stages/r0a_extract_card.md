# stage r0a_extract_card — 抽卡

> 新引擎上下文。paper + reviews → `REBUTTAL_CARD.json`。

## 槽位 `{{SLUG}}`
## 输入(只读):`papers/{{SLUG}}/review.md`、`papers/{{SLUG}}/Tex/main.tex`+`sections/*.tex`、扫代码/实验索引(判 concern 可行性)。

## 规则
1. reviewer 的 `initial_overall`(/5)、`soundness`、`confidence` 照 review.md **原值抽,别猜**。
2. `paper_claims` 必须来自论文正文;`concern_seeds` 必须来自 review 原文,**原子化**(一条 weakness/question 一条)。
3. 每个 concern 标 `type` + `likely_needs_experiment`(诚实:只有"明确要新实验/数据/baseline"且代码可能支持才 true)+ `note`(需实验→补什么;否则→已有证据/澄清/让步)。
4. `target.require_raise_on` = OA≤3 的 reviewer;`maintain` = OA≥4。绝不编。

## 输出:`campaigns/{{SLUG}}/REBUTTAL_CARD.json`(schema 见 `templates/REBUTTAL_CARD.schema.json`)。receipt:`{slug, n_reviewers, n_concerns, n_need_experiment, target}`。
