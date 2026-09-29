# IDEA_NODES.jsonl — idea 作为可审查对象

## 为什么需要它

在此之前，pipeline 的产出是线性 Markdown。这带来三个问题：

1. **无法回答"这个 idea 为什么被保留 / 被剪掉"**——淘汰理由散落在各阶段报告里，没有统一记录。
2. **无法精确计量成本**——没有"每个候选花了多少"的计量单位。
3. **无法做树搜索**——没有节点、父子关系和剪枝原因，搜索无从下手。

`outputs/IDEA_NODES.jsonl` 是每个 idea 的结构化记录，每行一个 JSON 对象。它是 Roadmap 中 MCTS 剪枝与成本核算的共同地基。

## 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | str | `IDEA-01`，本次 run 内唯一 |
| `parent_id` | str \| null | 派生来源（精炼后的修订版、或从某 idea 分裂出的变体）。根节点为 `null` |
| `run_id` | str | 时间戳，标识一次 pipeline 运行 |
| `status` | enum | `pending` / `supported` / `refuted` / `impl_failed` / `shelved` / `pruned`。**`refuted`（科学上被否证）与 `impl_failed`（代码没跑通）必须区分——前者是有价值的结果，后者不是** |
| `generator.operator` | enum | 由哪个生成算子产出：`critique_anchored` / `fossil_hunt` / `entropy_region` / `failure_mode` / `manual` |
| `generator.anchor` | list[str] | 锚定的证据 ID（`CRITIQUE-03`、`G2`、`FM-05`） |
| `generator.phase` | str | 产出位置，如 `idea-gen/2b` |
| `title` / `thesis` | str | 标题 / 一句话主张（"We show that X by Y"） |
| `evidence` | list | 支持"这个问题存在"的证据：`{kind: paper\|code\|experiment_observation, ref, note}` |
| `closest_work` | obj | `{ref, delta}` — 最接近的已有工作与实质差异。**delta 为空视为未完成查新** |
| `hypothesis.core` | str | 核心假设 |
| `hypothesis.falsifier` | str | **什么结果会否证它**。填不出来说明假设不可falsify |
| `min_experiment` | obj | `{design, budget:{gpu_hours, wall_clock_h}}` |
| `theory_claims` | list | `{claim, type, protocol, feasibility}`，来自 Theory-Experiment Alignment Matrix |
| `scores` | obj | 各维分数 + `composite` + `researcher_fit` + `source`（**谁打的分**）+ `degraded`（**外部模型是否降级为自评**） |
| `prune` | obj | `{pruned, reason, mask}`。`mask` ∈ `collision` / `not_feasible` / `fit_below_threshold` / `duplicate` / `critique_saturated` |
| `review_log` | list | `{round, overall, verdict, top2}` |
| `cost` | obj | `{tokens_in, tokens_out, wall_clock_s, external_calls}` |

## 设计约定

- **`scores.source` 与 `scores.degraded` 是必填的。** 分数脱离来源就没有意义：外部模型不可用时的自评分与正常评分不可比。
- **`prune.mask` 记录的是剪枝的机制原因，不是自然语言理由。** 这样才能统计各 mask 的剪枝量与精度（被剪的里有多少确实该剪）。
- **剪掉的节点不删除**，`status=pruned` 保留在文件里。搜索的价值一半在于知道什么被排除了。

## 用法

```bash
python3 tools/idea_nodes.py init                       # 建空文件
python3 tools/idea_nodes.py add --file node.json       # 追加一个节点（会校验）
python3 tools/idea_nodes.py update IDEA-03 --set status=pruned --set prune.mask=collision
python3 tools/idea_nodes.py validate                   # 全量校验
python3 tools/idea_nodes.py stats                      # 状态/算子/mask/成本汇总
python3 tools/idea_nodes.py tree                       # 打印派生谱系
```
