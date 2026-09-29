# 筛选结果（节选）

**方向**: LLM-as-a-Judge 偏差、校准与社会选择理论 ｜ **会场**: EMNLP 2026
**筛选数量**: 6 个存活 idea（全量，第二轮）

> 节选说明：保留排名表与"关键调整说明"；各 idea 的 Module A/B/C 详细报告与机制描述已裁剪。

## 最终排名

| Rank | Idea | Novelty | Venue | Strategic | Feasibility | Composite | Recommendation |
|------|------|---------|-------|-----------|-------------|-----------|----------------|
| 1 | IDEA-04 Causal Disagreement Decomposition | 8.0 | 6.67 | 7.6 | 7.0 | **7.25** | **PROCEED** |
| 2 | IDEA-05 IIA Attacks | 8.0 | 5.33 | 7.4 | 8.0 | **6.95** | CAUTION |
| 3 | IDEA-02 Stochastic Social Choice | 9.0 | 5.33 | 7.0 | 6.0 | **6.72** | CAUTION |
| 4 | IDEA-08 Minority-Preserving Aggregation | 8.0 | 4.67 | 7.6 | 6.0 | **6.35** | CAUTION |
| 5 | IDEA-01 Correlated Juries | 5.0 | 4.33 | 6.2 | 7.0 | **5.41** | CAUTION（需强 reposition） |
| 6 | IDEA-06 Selection-Aware Conformal Panels | 4.0 | 3.67 | 5.2 | 5.0 | **4.32** | **ABANDON** |

合成分 = `0.25×Novelty + 0.35×Venue + 0.20×Strategic + 0.20×Feasibility`
≥7.0 → PROCEED ｜ 5.0–6.9 → CAUTION ｜ <5.0 → ABANDON

## 关键调整说明（第二轮筛选揭示）

**第二轮深度 novelty 检索发现三篇紧邻 baseline 在首轮 `lit-survey` 中被漏检**：

| 新发现的 baseline | 影响 idea | Novelty 调整 |
|---|---|---|
| 一篇把 split conformal 与公理（传递性）违反**合一处理**的工作 | IDEA-06 | **8 → 4** |
| 一篇做 single-judge 的 selective conformal 工作 | IDEA-06 | （同上） |
| 一篇实证跨模型误差相关性 r=0.77、有效集成规模仅 1.3 的工作 | IDEA-01 | **8 → 5** |

后果：

- **IDEA-06 从 CAUTION 变为 ABANDON**（composite 由 6 以上降到 4.32）
- **IDEA-01 的核心实证前提被他人先做**，只能靠重新定位存活

## 这份记录说明什么

1. **首轮 novelty=8 是错的**，而且错得足够多以改变结论。首轮检索并没有报告任何失败——它只是没找到。
2. 因此 novelty 分数单独看没有意义。真正可核验的是 `closest_work.delta`（与最接近工作的**具体**差异）和**本次检索覆盖了什么**。
3. 这也是本项目把"与最接近工作的差异"设为必填字段、并在节点 schema 里要求 `closest_work` 的 `ref` 与 `delta` 成对出现的原因（缺 `delta` 会被 `tools/idea_nodes.py validate` 直接拦下）。
