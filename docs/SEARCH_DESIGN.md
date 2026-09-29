# 搜索设计：UCT 引导的扩展 + mask 先验剪枝

## 这是不是 MCTS

标准 MCTS 四阶段，本实现有三个：

| 阶段 | 状态 | 实现方式 |
|---|---|---|
| Selection | ✅ | UCT1：`Q(n) + c·sqrt(ln N_parent / N_n)`，未访问节点视为 ∞（必须先访问一次） |
| Expansion | ✅ | **由外部模型执行**。工具只输出"下一个该扩展谁"与扩展指令，生成由 `/idea-search` 调 LLM 完成 |
| Simulation (rollout) | ❌ **没有** | 无法为一个研究 idea 随机模拟到终局 |
| Backup | ✅ | 评估值沿父链回传，更新 `visits` 与 `value_sum` |

因此准确表述是 **"UCT 引导的最佳优先扩展，用 value 估计代替 rollout"**（AlphaZero 式的 value 替代 rollout，而非带随机模拟的完整 MCTS）。README 的能力分级里按这个表述写。

## 为什么搜索的对象是"扩展预算"

每次扩展 = 一次或多次 LLM 调用 = 真实花费。所以这里的搜索不是在搜一个静态空间，而是
**在候选之间分配有限的 LLM 调用预算**：先扩展哪个候选、什么时候放弃一条分支。
`--budget` 计的是扩展次数，`report` 会把它与 `IDEA_NODES.jsonl` 里的实测 token 一起打印。

## mask：先验剪枝

剪枝发生在**扩展之前**，避免在注定要废的分支上花预算。五个 mask 全部基于可验证信号：

| mask | 触发条件 | 信号性质 |
|---|---|---|
| `collision` | `closest_work.ref` 有但 `delta` 为空（查新未完成）；或 `evidence_collision=true`（检索确认同机制工作已发表） | 外部检索事实 |
| `not_feasible` | 存在 `feasibility=NOT_FEASIBLE` 且无 `resolution` 的理论 claim；或 `hypothesis` 无 `falsifier` | 规则查表 / 结构完整性 |
| `fit_below_threshold` | `researcher_fit < 12` | 规则阈值 |
| `duplicate` | 由 `tools/dedup_ideas.py` 裁定后写入 | 计算 + 裁定 |
| `critique_saturated` | 同一锚定证据下的**候选叶子**超过 3 个，标记其中 reward 最低的那些 | 结构性多样性约束 |

`critique_saturated` 有两条边界，都是为了让它表达"别再往这条分支投预算"而不是"丢掉已有成果"：

1. **只看叶子。** 已分裂出存活子节点的父节点代表一条分支，不是与兄弟重复的候选——剪掉它会连带废掉其下全部子节点。
2. **保留 reward 最高的前 3 个**，只标记超出部分。早期实现对该锚定下的所有节点一律标记，会把父节点和最优子节点一起剪掉。

被剪节点**不删除**，`prune.all_hits` 记录全部命中原因，便于事后统计剪枝精度（见 `ABLATIONS.md` D 组）。

## reward：必须交代信号来源

```
reward = alpha × v_model + (1 - alpha) × v_verifiable        # alpha 默认 0.5
```

`v_model = scores.composite / 10`，**由 LLM 给出**。

`v_verifiable` 是以下成分的均值（缺失的不参与）：

| 成分 | 来源 | 性质 |
|---|---|---|
| `retrieval` | 检索是否找到同机制已发表工作 / `delta` 是否写出 | 外部事实 |
| `feasibility_rule` | claim 类型 → 验证协议查表的通过比例 | 规则 |
| `falsifiability` | 是否写出否证条件 | 结构 |
| `cost_efficiency` | 实测 token 用量（相对同批候选） | 实测 |
| `distinctness` | 与**非同血缘**候选的词法/概念重叠（与 `dedup_ideas.py` 的血缘规则一致） | 计算 |

`report --provenance` 会逐节点打印这张来源表，并在某节点无任何可验证成分时明确警告。

### 为什么必须混入非 LLM 信号

**如果 reward 完全来自 LLM 评分，扩大搜索只会放大评分模型的偏好**，候选会向"评分模型喜欢的那类提案"塌缩。已有实证支持这一担忧：用执行奖励做 RL 的工作报告过平均奖励上升而最佳结果未改善。

实测的一个例子（见 `examples/` 的搜索演示）：两个子候选中，LLM 分更高的那个（composite 8.1 vs 7.8）因为理论 claim 查表判定 `NOT_FEASIBLE`，总 reward 反而更低（0.700 vs 0.801）。**这正是混入可验证信号要达到的效果。**
