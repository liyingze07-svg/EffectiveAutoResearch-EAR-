# 示例运行：LLM-as-a-Judge 方向

**脱敏精简版。** 保留流程证据（阶段时间戳、批判清单格式、筛选分数、降级记录、以及一次 novelty 判断被推翻的完整记录），裁剪掉各 idea 的机制细节与完整提案。

- **方向**：LLM-as-a-Judge 的偏差、校准与社会选择理论
- **目标会场**：EMNLP 2026
- **外部模型**：gpt-5.5 via Codex MCP，`model_reasoning_effort=xhigh`
- **实际耗时**：首轮 16:31 → 17:25（54 分钟，含 4 个阶段）；次日追加了全量重筛与精炼

## 这个例子值得看的三件事

### 1. novelty 分数会被推翻，而且幅度很大

首轮筛选给 IDEA-06 的 novelty 是 **8/10**。第二轮更深的检索发现了三篇在首轮 `lit-survey` 中**被漏检**的紧邻工作，该 idea 的 novelty 降到 **4/10**，推荐结论从 CAUTION 翻成 **ABANDON**；另一个 idea 从 8 降到 5。

完整记录见 `SCREENING_RANKED.excerpt.md`。这是本项目 `README.md`"已知局限"里那句话的实证：**"没查到相似工作"只说明当前检索范围内没发现碰撞**。看 `closest_work.delta` 比看 novelty 分数有用得多。

### 2. idea 锚定到批判，而不是锚定到 gap

`CRITICAL_ANALYSIS.excerpt.md` 是 Phase 2a 的产物（完整版 16 条，此处保留 3 条）。注意每条批判都指名了**它推翻的是哪些已发表工作的哪个假设**，Phase 2b 的每个 idea 必须声明自己攻击哪一条。

### 3. 剪枝记录本身是产物

`IDEA_NODES.jsonl` 用当前的节点 schema（见 `docs/IDEA_NODE_SCHEMA.md`）重建了这次 run 的 6 个候选，**包括被剪掉的两个**及其 `prune.mask`。跑：

```bash
python3 ../../tools/idea_nodes.py --path IDEA_NODES.jsonl validate
python3 ../../tools/idea_nodes.py --path IDEA_NODES.jsonl stats
python3 ../../tools/dedup_ideas.py --path IDEA_NODES.jsonl pairs --top 3
```

## 一个必须说明的前提

这次 run 的分数由 gpt-5.5 通过 Codex MCP 给出，**不是同行评审，也不预测录用结果**。读任何分数之前先看 `scores.degraded`：外部模型不可用时的自评分与正常评分不可比。
