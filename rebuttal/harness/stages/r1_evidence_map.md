# stage r1_evidence_map — 证据基底

> 新引擎上下文。paper + card → `evidence_map.json`(可诚实引用的一切)。

## 槽位 `{{SLUG}}`
## 输入(只读):`papers/{{SLUG}}/Tex/`、`campaigns/{{SLUG}}/REBUTTAL_CARD.json`、扫已有实验结果目录。

## 规则
1. 每个 `paper_claim` 定位到真实 §/图/表/定理(claim_anchors)。
2. 每个 `concern_seed` 给 `response_mode`(clarify/existing/experiment/concede/literature，按可行性阶梯)+ `evidence`(真实定位/已有结果文件路径/需要的 expid)+ `ready`(现在齐 or 等实验)。
3. **只定位真实存在的证据,别编**;引不到 → concede。

## 输出:`campaigns/{{SLUG}}/ledger/evidence_map.json`(`{claim_anchors:[], concern_evidence:[]}`)。receipt:`{n_anchors, n_concern, n_ready, n_wait_experiment}`。
