# stage r3b_experiment_ante — 实验前置门(ANTE;跑之前判"要不要跑")

> **不是自由 prompt——复用冻结 `consensus_gate`,orchestrator 在 Python 里跑(`orchestrate.experiment_ante`)。**
> 在**烧 GPU 之前**回答你原始诉求的前半:**什么时候需要加实验**,以及**加了能不能说服**。
> 策略 = **合议才拦**(保守,偏向"便宜就跑"):只有异家族合议清清楚楚才 NOT_NEEDED / REDESIGN。

## 它判什么(每个实验请求,逐服务的 concern)
用**同一根** `bar_met`,对两个反事实小桩各判一次(和 S-exp 同机器、同分区路由):
1. **便宜 warrant 桩**:"reviewer concern X;不加新实验的最佳已有 warrant(论文定位 / 已有资产 / 文献 / 界定让步)" → 过 bar?
2. **实验 best-case 桩**:"reviewer concern X;我们要跑 E,best-case 真结果 = 预注册成功判据" → 过 bar?

## 决策(聚合到实验级)
| 情形 | decision | loop 动作 |
|---|---|---|
| **所有** 服务的 concern 便宜 warrant 都 STRENGTH | **NOT_NEEDED** | 不必加实验(便宜 warrant 已够)→ 踢出队列,r3 走澄清/已有证据 |
| 便宜不够,但 **≥1** concern 的 best-case STRENGTH | **GREENLIGHT** | 放行去跑(进 run→accept→persuade 循环) |
| 连 best-case 都没有一个 STRENGTH | **REDESIGN** | 别烧 GPU——直接进重设计 planner(可行则换更强设计,不可行则诚实让步) |

- **为何 best-case 用预注册判据**:它同时成了实验的**预注册 falsifier**——真跑完 POST 拿真结果比对,打不到就判 CONCEDE,反 p-hacking。
- **合议才拦**:STRENGTH = 分区路由下两家族合议清(OA=3 Codex 主判);单判官说不行不足以 NOT_NEEDED/REDESIGN。off-distribution 保守。

## 输入(只读)
- `campaigns/{{SLUG}}/ledger/experiment_queue.json`(request + serves + expected_or_falsifier)、`evidence_map.json`(便宜 warrant 来源)、`REBUTTAL_CARD.json`(reviewer OA)、`rebuttal_verifier/consensus_gate.py`。

## 输出:内存决策 + `experiments/<expid>/loop.json` 的 ANTE 段(`{decision, per_concern:[{reviewer,concern,cheaper_clears,bestcase_clears}]}`)。

## DO-NOT
- 不新增 bar(只 `bar_met`);best-case 桩是**假设**,只 gate "要不要跑" 的决定,**不是**可引用的 claim。
- 不因单判官假阴性就毙实验;不把"省事"当 NOT_NEEDED(那是 DeepSeek/Codex 合议判的,不是驱动拍的)。
