---
name: idea-search
description: "在已有候选 idea 上做 UCT 引导的预算分配搜索：mask 先验剪枝 → 选出最该扩展的候选 → 生成机制层面不同的子候选 → 评分回传。Use when user says \"搜索 idea\", \"扩展候选\", \"idea search\", \"树搜索\", \"分配预算\", \"深挖这个方向\", or wants to systematically expand and prune a pool of existing candidates instead of generating a fresh batch."
argument-hint: "[-- budget: N] [-- alpha: 0.5] [-- k: 3] [-- venue: ICML]"
allowed-tools: Bash(*), Read, Write, Grep, Glob, WebSearch, WebFetch, mcp__codex__codex, mcp__codex__codex-reply
---

# Idea Search — UCT 引导的候选扩展与剪枝

参数：$ARGUMENTS

## 前置条件

`outputs/IDEA_NODES.jsonl` 必须已存在且非空（由 `/idea-gen` 产出）。若不存在，先跑 `/idea-gen`。

```bash
python3 tools/idea_nodes.py validate || echo "节点文件有问题，先修"
```

## 常量

- **BUDGET = 8** — 扩展次数上限（`-- budget: N` 覆盖）。**一次扩展 = 一次或多次 LLM 调用 = 真实花费**
- **ALPHA = 0.5** — reward 中 LLM 评分的权重（`-- alpha:` 覆盖）。调高会让搜索更依赖模型偏好
- **K = 3** — 每次扩展产出的子候选数（`-- k:` 覆盖）
- **REVIEWER_MODEL = `gpt-5.4`** — （**模型可用性依赖账号**：用 ChatGPT 账号登录的 codex 只能用账号自带模型，指定不支持的模型会被 400 拒绝。走 `--codex-cli` 时**不要传 `--model`**，让 codex 用默认模型；走 `--gpt-only` 时该模型必须对你的 OpenAI API key 可用。）

设计说明与 mask/reward 的完整定义见 `docs/SEARCH_DESIGN.md`。**这不是带随机 rollout 的完整 MCTS**（用 value 估计代替 rollout），对外描述时不要写成"MCTS 发现研究问题"。

> **外部模型路径（三选一，按环境变量 `CODEX_MODE` 路由）**
> - 未设置 → 优先 `mcp__codex__codex` / `mcp__codex__codex-reply`。**注意 codex CLI ≥0.158.0 已移除 `mcp-server` 子命令**，新版环境下这两个工具必然不可用，直接走下面两条之一，不要视为故障。
> - `CODEX_MODE=codex-cli` → `bash tools/codex_call.sh --thread <thread文件> --output <输出文件> --phase <阶段> --model REVIEWER_MODEL --config '{"model_reasoning_effort":"xhigh"}' --prompt "..."`。新建线程时 thread 文件为空即可，脚本会把 thread_id 写回该文件；后续同线程调用传同一个文件即自动 `resume`。**无需 API key**。
> - `CODEX_MODE=gpt-api` → `bash tools/gpt_call.sh`（同样的参数形态，需 `OPENAI_API_KEY`）。
>
> 三条路径都不可用时，才降级为 Claude 自评，并在节点上置 `scores.degraded=true`。

## Workflow

### Phase 0: 初始化

```bash
python3 tools/mcts_search.py init --budget <BUDGET> --alpha <ALPHA>
```

### Phase 1: 先验剪枝（每轮循环开始时必做）

```bash
python3 tools/mcts_search.py mask          # 先看命中
python3 tools/mcts_search.py mask --apply  # 确认后写入
```

**在扩展之前剪枝**，否则预算会花在注定要废的分支上。逐条核对命中原因：

- `collision` / `not_feasible` / `fit_below_threshold`：规则判定，直接接受
- `critique_saturated`：说明该锚定证据下候选已足够，接受剪枝并考虑改换锚定
- 若你判断某条命中是误剪，**不要跳过 mask**，而是去修正节点数据本身（补上 `delta`、补上 `falsifier`、或为 `NOT_FEASIBLE` 的 claim 写入 `resolution`），然后重跑 mask

把本轮剪枝数量与 mask 分布记入 `outputs/PIPELINE_LOG.md`。

### Phase 2: 选择

```bash
python3 tools/mcts_search.py select -k <K>
```

输出会给出：被选中的节点、它的 `visits`/`Q`/`UCT`、reward 的成分拆解、以及一段扩展指令。

**如果输出里有"无可验证成分，reward 完全来自 LLM 评分"的警告**：先去补齐该节点的 `closest_work.delta`、`hypothesis.falsifier` 或 `theory_claims`，再重新 select。在只有 LLM 分数的情况下搜索，只会放大评分偏差。

### Phase 3: 扩展（调用外部模型）

用 `mcp__codex__codex` 生成子候选（GPT-only 模式下用 `bash tools/gpt_call.sh --phase idea-search/expand`）：

```
你要为下面这个研究候选产出 K 个**机制层面不同**的子候选。

父候选：
  Title: [title]
  Core hypothesis: [hypothesis.core]
  Falsifier: [hypothesis.falsifier]
  Anchored evidence: [generator.anchor]
  Closest work / delta: [closest_work]

硬约束（违反任何一条的子候选无效）：
1. 与父候选的差异必须在**机制**上——不同的作用路径、不同的可观测量、不同的假设，
   而不是换一组措辞或换一个数据集。
2. 每个子候选必须锚定到具体证据 ID，不得为空。若它攻击的是一条新的批判，注明是哪条。
3. 必须写出 falsifier：**什么实验结果会否证它**。写不出来的子候选不要产出。
4. 必须写出 closest_work 的 ref 与 delta。delta 要具体到机制差异。
5. 如含理论 claim，标明 claim 类型（收敛界 / 泛化界 / 样本复杂度 / 近似比 /
   计算复杂度 / 表达力 / 信息论界 / PAC / 经验假设），并给出对应的标准验证协议与最小实验规模。

输出为 JSON 数组，每个对象含：id, title, generator{operator,anchor,phase},
hypothesis{core,falsifier}, closest_work{ref,delta}, theory_claims[{claim,type,protocol,feasibility}]。
id 用 `<父id>-c<序号>`。
```

把响应存为 JSON 文件后登记：

```bash
python3 tools/mcts_search.py expand <父节点id> --children /tmp/children.json
```

**校验不通过会整批拒绝**（缺锚定、缺 falsifier、`closest_work` 缺 delta 等）。此时不要放宽校验，回到 Phase 3 让模型重写缺失字段。

### Phase 4: 评分与回传

对每个新子候选跑 `/idea-screen`（至少 Module A 查新 + Module C），把分数写回节点，然后：

```bash
python3 tools/mcts_search.py backup <子节点id>
```

`backup` 默认从 `scores.composite` 与可验证成分算出 reward 并沿父链回传。

**写分数时 `scores.source` 与 `scores.degraded` 必填**——降级自评分与正常评分不可比，混在一起会污染整棵树的 Q 值。

### Phase 5: 循环与终止

回到 Phase 1，直到满足任一条件：

- 扩展次数达到 BUDGET
- 所有存活叶子都被访问过且 Q 值不再上升（连续两轮最优 Q 提升 < 0.02）
- 存活节点数为 0（全部被剪）——此时在 `PIPELINE_LOG.md` 记录"搜索空间被剪空"，并回到 `/idea-gen` 换锚定重新生成

### Phase 6: 报告

```bash
python3 tools/mcts_search.py report --provenance > outputs/SEARCH_REPORT.md
```

在 `outputs/PIPELINE_LOG.md` 追加：

```
## [Timestamp] Idea Search Complete
- 扩展次数: N / BUDGET
- 新增候选: M 个（存活 X 个，剪枝 Y 个）
- 剪枝 mask 分布: collision=a, not_feasible=b, fit_below_threshold=c, duplicate=d, critique_saturated=e
- 最优候选: <id> (Q=..., composite=...)
- reward 中位数的 v_model / v_verifiable 拆解: ...
- ⚠️ 若有节点 reward 完全来自 LLM 评分，在此列出
```

## Key Rules

1. **剪枝在扩展之前。** 每轮 Phase 1 必做，不可跳过。
2. **搜索不会提高 idea 质量，只会更有效地分配预算。** 如果 reward 信号本身有偏，搜索会放大它。因此每轮都要看 `--provenance` 的成分拆解。
3. **被剪节点永不删除。** 剪枝记录是产物，用于事后统计剪枝精度。
4. **子候选必须机制不同。** 换措辞的子候选会被 `tools/dedup_ideas.py` 标出来；发现后用 `mark` 剪掉并让模型重写。
5. **本 skill 不做精炼。** 搜索结束后对最优候选跑 `/idea-refine`。
6. 全程不等待用户输入；外部模型不可用时降级为 Claude 自评并在节点上置 `scores.degraded=true`。

## Composing

```
/idea-gen "方向"          → outputs/IDEA_NODES.jsonl（初始候选池）
/idea-search -- budget: 8 → 扩展 + 剪枝 + 排序
/idea-refine "最优候选"    → FINAL_PROPOSAL.md
```
