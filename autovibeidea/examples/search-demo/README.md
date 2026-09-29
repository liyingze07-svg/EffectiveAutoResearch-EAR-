# 搜索演示

展示 `/idea-search` 的一轮完整循环：`init → expand → backup → mask → report`。

**数据说明**：6 个根候选来自 `examples/judge-run/` 的真实运行；子候选（`*-c*`）是**为演示构造的**，
不是某次真实 LLM 生成的产物。构造它们的目的是复现两个具体行为，见下。

## 看点 1：可验证信号压过 LLM 评分

两个子候选：

| 节点 | composite（LLM 给分） | feasibility_rule | 总 reward |
|---|---|---|---|
| `IDEA-04-c1` 分歧成分的干预式识别 | 7.8 | 1.0 | **0.801** |
| `IDEA-04-c2` 分歧分解的样本复杂度下界 | **8.1**（更高） | **0.0** | **0.700**（更低） |

`c2` 的 LLM 分更高，但它的理论 claim（样本复杂度 `Ω(d log n / ε²)`）按 claim 类型查表需要
"≥5 个标注比例的标签效率实验"，在给定约束下判定为 `NOT_FEASIBLE` 且未采纳出路，
于是 `feasibility_rule = 0`，总 reward 反而更低，随后被 `not_feasible` mask 剪掉。

**这就是混入非 LLM 信号的全部意义**：模型偏好"听起来更厉害的定理"，规则查表知道它验不起。

## 看点 2：critique_saturated 只剪超出上限的最弱叶子

`CRITIQUE-02` 下累积到 4 个候选叶子（上限 3）时，只有 reward 最低的那个被标记：

```
[critique_saturated] 批判 CRITIQUE-02 已有 4 个候选叶子（上限 3），本节点 reward 排名第 4，超出上限
```

父节点和高 reward 的子节点都保留。这条边界是必要的——早期实现对该锚定下的**所有**节点一律标记，
会把父节点连同其下最优子节点一起剪掉。

## 复现

```bash
cd examples/search-demo
python3 ../../tools/mcts_search.py --path IDEA_NODES.jsonl --state SEARCH_STATE.json report --provenance
python3 ../../tools/mcts_search.py --path IDEA_NODES.jsonl --state SEARCH_STATE.json mask
python3 ../../tools/mcts_search.py --path IDEA_NODES.jsonl --state SEARCH_STATE.json select -k 3
```

`SEARCH_REPORT.txt` 是 `report` 的实际输出。设计与 mask/reward 定义见 `docs/SEARCH_DESIGN.md`。

## 这个演示不能说明什么

- **不能说明剪枝是对的。** 5 个 mask 的误剪率需人工复核。
- 子候选是构造的，因此这里的 Q 值分布不代表真实运行的分布。
