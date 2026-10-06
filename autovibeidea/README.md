# AutoVibeIdea

> **从一个研究方向，推进到一份有文献依据、论证结构与实现细节的研究方案。**

一个想法要成为研究方案，需要回答的不只是“做什么”：它从哪个问题出发，与已有工作有什么区别，核心论断怎样成立，又该通过什么实验来验证？

AutoVibeIdea 将这些问题组织成一条连续的研究规划工作流。输入研究方向与目标会议，从文献调研开始，经过批判性分析、候选生成、多维筛选和迭代精修，逐步形成结构化的 Proposal 草稿。你既可以运行完整流程，也可以单独使用调研、生成、筛选或精修环节。

**生成阶段要求想法关联具体的批判点，精修阶段围绕冻结的研究问题展开，最终方案之外还保留分析、审查与修改记录。**

本项目属于 [EAR — Effective Auto Research](../README.md)。请使用完整的 EAR 仓库；共享的环境检查与安全工具位于仓库根目录。

[快速开始](#quick-start) · [核心工作流](#workflow) · [输出文件](#outputs) · [能力状态](#capabilities) · [斜杠命令](#commands) · [运行配置](#runtime)

---

## 一个方向，三层产出

提供一个研究方向，以及你希望面向的目标会议，例如：

```text
研究方向：sample-efficiency bottlenecks in offline RL with image observations
          以图像为观测的离线强化学习中的样本效率瓶颈
目标会议：NeurIPS
```

工作流围绕三个层次组织产出，正文使用英文：

| 产出层次 | 回答的问题 | 主要文件 |
| --- | --- | --- |
| **文献版图与问题分析** | 已有工作做到了哪里？哪些结构性问题值得继续研究？ | `LANDSCAPE.md`、`LANDSCAPE.json`、`CRITICAL_ANALYSIS.md` |
| **候选想法与筛选结果** | 有哪些切入点？它们在创新性、会议适配、策略价值与可行性上如何比较？ | `IDEAS_RAW.md`、`IDEAS_FILTERED.md`、`SCREENING_REPORT.md`、`SCREENING_RANKED.md` |
| **精修后的研究方案** | 问题、论证、验证设计和实现细节如何连成一份完整计划？ | `refine-logs/FINAL_PROPOSAL.md`、逐轮审查与修改记录 |

可以先看[脱敏运行示例](examples/judge-run/README.md)，了解中间材料的实际形式。示例中保留了一次第二轮检索后，创新性评分从 8 调整为 4 的记录，展示新增检索结果如何影响后续判断。

---

<a id="quick-start"></a>

## 快速开始

### 1. 克隆仓库，先看一次完整的离线演示

离线演示只需要 **Python 3.10+**，无需模型账户、API Key 或第三方 Python 包。已经克隆 EAR 时，可以跳过克隆步骤。

```bash
git clone https://github.com/liyingze07-svg/EffectiveAutoResearch-EAR-.git EAR
cd EAR

python3 scripts/doctor.py --offline
python3 scripts/offline_demo.py
```

预期输出：

```text
PASS: idea validation/report, five contracts, and synthetic rebuttal dry-run.
```

程序会打印临时目录，其中包含研究想法搜索报告与模拟审稿回复任务的产物。这一步用于检查安装、流程衔接和输出结构，不调用模型。

### 2. 准备在线运行环境

| 项目 | 要求 |
| --- | --- |
| 系统 | Linux / WSL2 |
| Shell | Bash |
| Python | 3.10 或更新版本；Python 工具使用标准库 |
| 模型驱动 | 已登录的 Codex CLI；下方安装命令需要 Node.js 和 npm |
| 后台任务控制 | `flock`（util-linux）、`nohup`，以及 Linux pidfd 支持（Linux 5.3+） |
| 可选检索集成 | Zotero MCP、Obsidian MCP；未配置时，可在启用网络后使用公开网页来源 |

`doctor` 会检查后台控制条件和其他启动器依赖。身份认证、模型访问权限与服务可用性不属于本地检查范围。

从 EAR 仓库根目录执行：

```bash
npm install -g @openai/codex
codex login                                      # 已完成认证时可跳过

python3 scripts/doctor.py --component autovibeidea
cd autovibeidea
```

所有 `run.sh` 模式都以 Codex 为驱动，包括 `--gpt-only`。只有选择额外的 OpenAI API 审查路径时，才需要单独配置 API Key。

### 3. 启动研究规划

推荐通过 `--codex-cli` 在独立的 Codex 会话中进行审查：

```bash
./run.sh --allow-network --codex-cli --daemon "your research direction" NeurIPS
```

将 `"your research direction"` 替换为你的研究方向，将 `NeurIPS` 替换为目标会议。

| 参数 | 作用 |
| --- | --- |
| `--allow-network` | 启用实时文献检索所需的联网能力和嵌套模型调用，不关闭沙箱 |
| `--codex-cli` | 使用本地登录，通过独立的 Codex 会话请求额外审查，无需另配 API Key |
| `--daemon` | 在后台运行，并通过启动器管理任务状态 |

在线调用会使用账户额度，并可能产生费用。独立审查会话可能与生成端使用相同模型；具体路由和回退行为见下方说明。

### 4. 查看进度与停止任务

在 `autovibeidea/` 目录中执行：

```bash
# 查看任务状态
./run.sh --status

# 持续查看运行日志
tail -f outputs/pipeline.log
```

查看日志时，`Ctrl-C` 只会结束日志查看，不会停止后台任务。需要取消运行时，单独执行：

```bash
./run.sh --stop
```

该命令会停止后台任务并清理子进程。准备切换到新方向时，先结束当前任务，再归档已有产物。

### 选择适合你的审查路径

生成驱动与额外审查可以使用不同的调用路径：

| 路径 | 额外审查方式 | 配置要点 |
| --- | --- | --- |
| **`--codex-cli`：推荐入口** | 通过 `tools/codex_call.sh` 启动独立 Codex 会话 | 复用本地登录；可能与生成端使用相同模型或服务商 |
| **`--gpt-only`** | 通过 `tools/gpt_call.sh` 发起纯文本 OpenAI API 调用 | 配置 `OPENAI_API_KEY` 或 `~/.openai_key`；主驱动仍是 Codex |
| **不显式指定路径** | Shell 兼容工作流可能在生成会话内执行评估 | 不额外指定审查后端 |
| **宿主提供的 MCP** | 使用宿主代理及其集成能力 | Shell 启动器不依赖此配置 |

`--codex-cli` 与 `--gpt-only` 二选一。配置好 API Key 后，可在 `autovibeidea/` 中使用 API 审查路径：

```bash
# 不要与当前工作区中的已有任务同时运行
./run.sh --allow-network --gpt-only "your research direction" NeurIPS
```

外部审查不可用时，技能可能回退到自我评估，并放宽评分阈值。实际使用的路径和降级情况可以从 `outputs/PIPELINE_LOG.md`、审查产物，以及有记录时的 `scores.degraded` 中查看。模型路由通过技能指令指定，是否完成了对应调用以运行记录为准。

更多配置见 [CODEX_COMPAT.md](CODEX_COMPAT.md)。

---

<a id="workflow"></a>

## 核心工作流：先找问题，再打磨方案

AutoVibeIdea 将选题拆成五个阶段，并提供方向收敛与候选搜索两个可选环节。下面展示技能定义的完整路径；实际生成的文件取决于启用阶段与运行情况。

```text
研究方向 + 目标会议
        │
        ├─ 尚未确定方向？ /idea-filter 先收敛兴趣与约束
        ▼
① 文献调研 /lit-survey
   整理研究版图，建立研究空白矩阵
        ▼
② 批判驱动生成 /idea-gen
   先分析结构性弱点，再生成绑定 CRITIQUE-ID 的候选想法
        ▼
③ 多维筛选 /idea-screen
   创新性核查 + 目标会议审稿模拟 + 策略评估 + 可行性评分
        │
        ├─ 需要继续探索？ /idea-search 按预算扩展候选
        ▼
④ 深度精修 /idea-refine
   冻结问题 → 梳理论证 → 对齐验证 → 逐轮审查 → 补全细节
        ▼
⑤ 总结报告
   FINAL_PROPOSAL.md + IDEA_DISCOVERY_REPORT.md
```

### ① 文献调研：让研究方向落到具体的问题版图上

`/lit-survey` 从四级来源开展检索：

```text
Zotero MCP → Obsidian MCP → 本地 PDF → WebSearch / arXiv
```

调研结果整理为 `outputs/LANDSCAPE.md` 与 `LANDSCAPE.json`，其中包含**研究空白识别矩阵（Gap Identification Matrix）**，记录空白类型及置信度。

这一步为后续想法提供共同背景：先把已有工作、问题和空白放在一起，再讨论从哪里切入。需要查看领域演化线索时，还可以启用实验性的轨迹分析：`/lit-survey "direction" -- trace: true`。

### ② 批判驱动生成：每个想法都要说明“从哪个问题出发”

`/idea-gen` 将生成拆成两个环节，而不是直接从方向跳到一串选题标题。

**先分析，再提出候选。** 阶段 2a 请求外部模型沿四个维度分析研究版图中的结构性弱点，写入 `outputs/CRITICAL_ANALYSIS.md`，并为批判点分配 `CRITIQUE-ID`。

**让想法与批判点建立对应关系。** 阶段 2b 要求每个候选想法关联一个 `CRITIQUE-ID`，并给出定理或猜想框架（Theorem / Conjecture Scaffold）。阅读候选时，可以回到它所回应的问题，而不是只看一个方法名称。

随后，候选依次经过：

```text
可行性 → 创新性 → 影响力 → 研究者适配度 → 反模式检查
```

研究者适配度筛选检查命题是否可证伪、证据是否可获取、最小可信结果是否能在预算内完成，以及是否符合用户明确给出的能力、兴趣与范围约束。四项各评 1–5 分，当前阈值为 `12/20`；未提供的信息记为暂定评分及待核实项。流程保留完整候选集，并将筛选后保留的 4–6 个想法单独整理：

```text
outputs/IDEAS_RAW.md
outputs/IDEAS_FILTERED.md
```

### ③ 多维筛选：把候选放进同一套比较框架

`/idea-screen` 包含三个模块：**创新性核查、目标会议审稿模拟、策略评估**。审稿模拟采用 3 位审稿人与一次元评审，并结合可行性形成综合排序。

```text
综合评分 = 0.25 × Novelty
         + 0.35 × Venue
         + 0.20 × Strategic
         + 0.20 × Feasibility
```

| 维度 | 权重 | 比较内容 |
| --- | --- | --- |
| Novelty | 25% | 与已有工作的差异及创新性 |
| Venue | 35% | 目标会议配置下的模拟审稿评分 |
| Strategic | 20% | 研究方向与策略的匹配度 |
| Feasibility | 20% | 方案可行性 |

详细分析写入 `outputs/SCREENING_REPORT.md`，集中排序写入 `outputs/SCREENING_RANKED.md`。两份材料分别用于查看判断依据和比较候选。

### 可选：按预算扩展候选，而不是只保留第一轮想法

`/idea-search` 是实验性的候选扩展环节。它先应用先验剪枝，再通过 UCT 选择值得继续展开的节点，生成机制上不同的子候选，并回传价值估计。

```text
先验掩码剪枝 → UCT 选择 → 子候选扩展 → 价值回传
```

这条路径保留搜索树、候选谱系、成本与奖励来源。实现采用 **UCT 引导的扩展与价值估计，不执行随机 rollout**。预算、奖励分量与默认参数见下方“实验性能力”及 `docs/SEARCH_DESIGN.md`。

### ④ 深度精修：守住研究问题，再补全论证与实现

`/idea-refine` 围绕同一个研究问题推进修改，将“研究方向的评估”和“实现细节的展开”分开处理。

| 环节 | 作用 | 对应材料或机制 |
| --- | --- | --- |
| **冻结问题锚点** | 明确当前要解决的问题，并检测后续修改中的方向偏移 | Problem Anchor |
| **提取论证骨架** | 梳理从状态 A 到状态 B 的论证关系，逐轮检查缺口 | `skeleton.md` |
| **梳理理论依据** | 为核心论断整理理论基础 | Theoretical Grounding |
| **对齐理论与实验** | 将论断对应到验证方案、最低规模与可行性判断 | Theory–Experiment Alignment Matrix |
| **逐轮审查与修改** | 通过常规审查循环或苏格拉底式对话精修方案 | `round-N-review.md`、`round-N-refinement.md` |
| **深度展开** | 补全公式、伪代码、接口维度与超参数范围 | Deep Expansion Pass |

常规审查循环最多 3 轮；也可选择苏格拉底式对话模式，要求在评分前先陈述对方案的理解。

其中，**理论—实验对齐矩阵**把核心论断与验证设计放在同一张表里：

```text
论断类型 → 验证方案 → 最低规模 → 可行性判断
```

经过论证梳理、审查和深度展开后，方案写入 `refine-logs/FINAL_PROPOSAL.md`。逐轮记录同步保留，便于查看每次修改解决了什么问题，以及哪些细节在后续轮次中得到补充。

### ⑤ 总结报告：把分散的过程材料汇总起来

最终的 `outputs/IDEA_DISCOVERY_REPORT.md` 汇总整条研究规划流程。结合文献版图、筛选报告与最终 Proposal，可以从最后的方案回到它的来源与演变过程。

---

<a id="outputs"></a>

## 输出文件：最终稿之外，也保留推演过程

根据启用的阶段，工作区会保留以下相应产物。`outputs/` 为空时，表示输出工作区已清理，可开始新任务。

```text
outputs/
  LANDSCAPE.md / .json               文献版图与研究空白矩阵
  CRITICAL_ANALYSIS.md               批判性分析，包含 CRITIQUE-01...N
  IDEAS_RAW.md / IDEAS_FILTERED.md    完整候选集与筛选后保留的想法
  SCREENING_REPORT.md                多维筛选的详细分析
  SCREENING_RANKED.md                候选排序
  IDEA_DISCOVERY_REPORT.md           完整工作流总结

  ENTROPY_MAP.json                   高熵区域与失效模式，可选
  IDEA_NODES.jsonl                   结构化候选、剪枝掩码、谱系与成本
  COST_LOG.jsonl                     Token 用量与实际运行耗时
  SEARCH_STATE.json                  搜索预算、alpha 与 UCT 常数
  SEARCH_REPORT.md                   搜索树、奖励来源与剪枝统计

  pipeline.log                      启动后可持续跟踪的运行日志
  PIPELINE_LOG.md                    各阶段的自主决策记录
  PIPELINE_STATE.json                恢复运行的检查点

refine-logs/
  skeleton.md                       状态 A → 状态 B 的论证骨架
  round-N-review.md                  第 N 轮审查
  round-N-refinement.md              第 N 轮修改
  round-N-expanded.md                深度展开输出
  FINAL_PROPOSAL.md                 最终研究方案草稿
  REFINEMENT_REPORT.md               精修报告
  score-history.md                  评分历史
```

想先看研究脉络，从 `LANDSCAPE.md` 和 `CRITICAL_ANALYSIS.md` 开始；想比较切入点，查看两份筛选报告；想直接讨论方案，打开 `FINAL_PROPOSAL.md`，再按需回看逐轮记录。

### 归档当前任务，开始下一个方向

任务完成或停止后，在 `autovibeidea/` 目录执行：

```bash
# 预览待归档内容
./clean.sh --list

# 将当前输出归档
./clean.sh --name "MyRun_v1"
```

归档文件会移动到 `archive/` 下带时间戳的目录。请先结束当前任务，再执行清理与归档。

---

<a id="capabilities"></a>

## 能力状态

这里按实现状态区分功能：**已实现**表示已在技能提示词中定义，或已有工具支持；**实验性**表示机制、阈值与接口仍在迭代；**路线图**说明尚未实现的方向和当前不计划采用的设计。

### 已实现：研究规划的主干流程

| 能力 | 入口 |
| --- | --- |
| 四级来源文献调研；包含空白类型与置信度的研究空白识别矩阵 | `/lit-survey` |
| 两阶段生成：四维批判性分析，再将每个想法关联到 `CRITIQUE-ID` | `/idea-gen` 阶段 2a / 2b |
| 分层筛选：可行性、创新性、影响力、研究者适配度与反模式检查 | `/idea-gen` 阶段 3–5 |
| 创新性核查、3 位审稿人及元评审模拟、策略匹配度与综合排序 | `/idea-screen` |
| 冻结问题锚点，并检测方案偏移 | `/idea-refine` 阶段 0 |
| 状态 A → B 的论证骨架，以及逐轮骨架缺口检查 | `/idea-refine` 阶段 0.5 / 3.3 |
| 理论—实验对齐矩阵：论断类型、验证方案、最低规模与可行性判断 | `/idea-refine` 阶段 1.4.TE |
| 深度展开：公式、伪代码、接口维度与超参数范围 | `/idea-refine` 阶段 5.5 |
| 苏格拉底式精修，先陈述理解再评分 | `/idea-refine -- mode: socratic-*` |
| 外部模型调用：本地 Codex CLI、OpenAI API、Codex MCP，以及回退机制 | `tools/codex_call.sh`、`tools/gpt_call.sh`、宿主 MCP |
| 检查点恢复、无人值守执行与外部模型不可用时的回退 | `PIPELINE_STATE.json`、各技能的回退机制 |

### 实验性：让候选可追踪、可比较、可继续搜索

| 能力 | 机制与当前设置 | 工具 / 入口 |
| --- | --- | --- |
| **结构化想法节点** | 记录生成者、证据锚点、证伪条件、剪枝掩码、成本与谱系，支持统一管理和统计 | `tools/idea_nodes.py`；`docs/IDEA_NODE_SCHEMA.md` |
| **疑似重复候选识别** | 结合概念归一化、词汇与结构重叠、谱系排除和模板文本过滤；候选对经模型裁定后再标记。阈值为经验设置，可优先查看 `--top` 排序 | `tools/dedup_ideas.py` |
| **高熵区域发现** | 使用“论断立场熵 × 可比性惩罚”，减少不同实验设置造成的伪冲突；可比性权重可按子领域调整 | `tools/entropy_map.py` |
| **失效模式发现** | 从不同论文共有的失效条件入手，通过文本归一化聚类，再复核聚类结果 | `tools/entropy_map.py` |
| **Token 成本记录** | 记录 `--gpt-only` 与 `--codex-cli` 的用量；Codex MCP 路径不返回用量 | `tools/gpt_call.sh`、`tools/codex_call.sh` → `COST_LOG.jsonl` |
| **生成阶段的多样性约束** | 至少 50% 的想法关联不同批判点；每个批判点最多对应 3 个想法，并划分风险等级；通过去重工具检查 | `/idea-gen` 阶段 2b；`tools/dedup_ideas.py` |
| **研究者适配度阈值** | 当前为 `12/20`，可按研究者偏好调整 | `/idea-gen` 阶段 4 |
| **深度展开环节的效果探索** | 将方向评估与实现细节补充分开；该环节已接入，收益评估仍属实验性 | `/idea-refine` 阶段 5.5 |
| **UCT 候选扩展与先验掩码剪枝** | 选择、扩展、回传；用价值估计替代随机 rollout。默认 `c=1.414`，可调整 | `/idea-search`；`tools/mcts_search.py` |
| **混合奖励与来源追踪** | 融合 `retrieval`、`feasibility_rule`、`falsifiability`、`cost_efficiency`、`distinctness`；可用分量等权平均，默认 `alpha=0.5` 控制 LLM 评分占比；`--provenance` 展示来源 | `tools/mcts_search.py` |
| **轨迹分析** | 默认关闭，通过 `-- trace: true` 启用 | `/lit-survey` |

### 路线图与设计边界

| 方向 | 当前状态 |
| --- | --- |
| **基于实际结果的奖励信号** | 现有可验证分量描述方案属性；下一步探索将预实验结果纳入奖励 |
| **正式的预实验阶段** | 尚未接入自动工作流；目前预实验由人工运行，实际实验结果由该环节获得 |
| **规模区间发现（Scaling-Regime Discovery）** | 尚未独立实现；阶段 2a 仍沿四个维度分析，高熵发现部分覆盖矛盾识别 |
| **“研究空白 × 创新模式”的正交模式库** | 当前仅有批判维度这一轴，包含 4 个操作算子 |
| **以演化轨迹作为主要生成表示** | 尚未实现；轨迹分析目前只是文献版图中的可选子章节 |
| **完整 Token 成本基线** | 仍缺少 Codex MCP 路径的用量数据 |
| **包含随机 rollout 的完整 MCTS** | 当前不计划采用；研究想法难以通过随机模拟得到终局结果，现有设计使用价值估计，详见 `docs/SEARCH_DESIGN.md` |

---

<a id="commands"></a>

## 斜杠命令：整条运行，也可以只取其中一步

Shell 快速开始不需要挂载斜杠命令。若宿主代理支持 Markdown 命令文件，可以把技能接入代理，在对话中调用完整工作流或单独的研究环节。

| 命令 | 用途 |
| --- | --- |
| `/start "direction" -- venue: ICML` | **在后台启动完整工作流** |
| `/idea-filter "constraints and interests"` | 将模糊兴趣与约束收敛为 1–3 个确定方向 |
| `/idea-pipeline "direction" -- venue: ICML` | 在前台运行完整工作流 |
| `/lit-survey "direction"` | 仅开展文献调研 |
| `/idea-gen "direction"` | 生成研究想法，包含批判性分析 |
| `/idea-screen "idea" -- venue: ICML` | 仅进行多维筛选 |
| `/idea-refine "idea"` | 仅进行深度精修 |
| `/idea-refine "idea -- mode: socratic"` | 使用苏格拉底式对话精修 |
| `/idea-search -- budget: 8` | 在已有候选之间分配扩展预算，执行先验掩码、UCT 扩展与回传 |
| `/fossil-hunt "field"` | 寻找领域中长期沿用、未被充分质疑的组成部分 |
| `/exp-design "method description"` | 从第一性原理出发设计论文实验 |
| `/experiment-audit "code directory"` | 审查实验代码中的学术诚信问题 |

### 将技能挂载到兼容代理

仓库不附带私有代理配置。将 `EAR_COMMAND_DIR` 替换为宿主代理的命令目录，然后在 `autovibeidea/` 下运行：

```bash
EAR_SKILL_ROOT="$(pwd -P)"
EAR_COMMAND_DIR="/absolute/path/to/your/agent/commands"  # 替换此路径
mkdir -p "$EAR_COMMAND_DIR"

for skill_dir in "$EAR_SKILL_ROOT"/skills/*/; do
  skill_name="$(basename "$skill_dir")"
  command_file="$EAR_COMMAND_DIR/$skill_name.md"
  if [ -e "$command_file" ] || [ -L "$command_file" ]; then
    printf 'Keeping existing command: %s\n' "$command_file"
  else
    ln -s "${skill_dir}SKILL.md" "$command_file"
  fi
done
```

绝对路径链接不受命令目录深度影响。已有文件和链接会保持不变；若它们指向旧仓库，可单独检查。符号链接会反映后续技能修改，仓库移动后则需要更新链接。也可以直接将技能以 Markdown 形式提供给代理。

挂载后，在兼容代理中调用：

```text
/start "sample-efficiency bottlenecks in offline RL with image observations" -- venue: NeurIPS
```

---

## 目标会议配置

会议配置用于组织评分校准档位与审稿人画像，使筛选围绕指定的会议展开。

| 会议 | 侧重点 |
| --- | --- |
| ICML / NeurIPS | 机器学习方法与理论 / 广泛的机器学习及跨学科研究 |
| EMNLP | 自然语言处理 |
| VLDB / SIGMOD | 数据库与数据系统 |

需要添加会议时，复制 `venue-profiles/_template.md`，填写评分校准档位与审稿人画像。这些配置是对公开评审标准的主观建模，可以按目标会议调整。

---

## 任务管理与批处理

### 状态、锁与并行运行

后台任务根据执行器退出状态记录结果：成功退出记为 `DONE`，否则记为 `FAILED` 并保存退出码。存在已记录的失败时，`./run.sh --status` 返回非零状态码。

同一工作区使用锁阻止重叠的后台启动。需要并行探索多个方向时，请使用不同的仓库副本，分别保留各自的输出和运行状态。

### 停止任务时如何清理

`./run.sh --stop` 会核验保存的进程身份，再终止任务及其后代进程，包括已脱离的子进程；必要时在两秒后升级为 `SIGKILL`。清理完成后才最终更新状态与工作区锁。

向启动器 PID 发送 `SIGTERM` 会进入相同的清理路径。直接对监控进程使用 `SIGKILL` 无法执行清理，因此取消任务应优先使用 `--stop`。

### 批量运行多个方向

`batch.sh` 是兼容入口，实际转交给 `batch_codex.sh`。通过 `--task-file` 提供研究方向，不再修改旧启动器内嵌的任务数组。

批处理会逐个归档任务。任何任务失败，批处理最终都会返回非零退出码；只有全部任务成功时才返回零。

---

## 工具与开发文档

### 工具索引

| 工具 | 用途 |
| --- | --- |
| `tools/arxiv_fetch.py` | 获取 arXiv 元数据，对 406 / 429 / 5xx 响应进行退避重试；限流时回退到 WebSearch，避免无限等待 |
| `tools/gpt_call.sh` | 带会话线程语义的 OpenAI API 封装；将 Token 用量写入 `outputs/COST_LOG.jsonl` |
| `tools/codex_call.sh` | 通过本地 `codex exec` 调用外部模型，沿用 `gpt_call.sh` 接口；无需单独 API Key，支持会话恢复与 Token 用量采集 |
| `tools/idea_nodes.py` | 管理 `IDEA_NODES.jsonl`：`init / add / update / validate / stats / tree` |
| `tools/dedup_ideas.py` | 标记疑似重复候选对；使用 `mark` 前先完成裁定 |
| `tools/entropy_map.py` | 从 `LANDSCAPE.json` 计算高熵区域与失效模式 |
| `tools/mcts_search.py` | UCT 搜索驱动：`init / mask / select / expand / backup / report` |
| `scripts/selfcheck.sh` | 提交前自检 |

### 深入了解设计

| 文档 | 内容 |
| --- | --- |
| `docs/IDEA_NODE_SCHEMA.md` | 结构化想法节点的字段定义 |
| `docs/SEARCH_DESIGN.md` | UCT 搜索、掩码语义与奖励分量 |
| `docs/WORKFLOW.md` | 详细工作流 |
| `examples/judge-run/` | 真实运行的脱敏片段，包括第二轮检索后创新性评分从 8 调整到 4 的记录 |

---

<a id="runtime"></a>

## 运行配置与数据流

### 默认执行策略

`./run.sh`、`./batch_codex.sh` 与兼容入口 `./batch.sh` 使用共享执行策略：

```bash
codex exec -c 'sandbox_mode="workspace-write"' -c 'approval_policy="never"' \
  -c sandbox_workspace_write.network_access=false -c 'web_search="disabled"'
```

命令在 CLI 沙箱内无人值守执行，超出策略范围的操作会被拒绝，不会自动提升权限。

| 配置 | 行为 |
| --- | --- |
| 默认模式 | `workspace-write`、不请求审批、Shell 网络关闭、网页搜索关闭 |
| `--allow-network` | 显式启用 Shell 网络与实时搜索，用于实时文献检索和嵌套 API / CLI 调用 |
| `--unsafe` | 显式允许不受限制的执行，仅用于已从外部隔离的环境；不作为自动回退 |
| `EAR_ALLOW_NETWORK=1` | 封装脚本中对应的联网环境变量，默认为 `0` |
| `EAR_UNSAFE=1` | 封装脚本中对应的不受限执行环境变量，默认为 `0` |

CLI 与模型之间的通信不受上述 Shell 联网开关控制。沙箱限制写入，但不会隐藏所有宿主机文件，也不会覆盖每个 MCP 工具的权限。

### 审查工具的执行方式

`tools/codex_call.sh` 显式采用只读沙箱、不请求审批，并关闭网页搜索，恢复会话时也使用这些设置。只读模式仍允许执行获准的读取命令。

`tools/gpt_call.sh` 是纯文本 API 客户端，不会将提示词或模型回复作为代码执行。在代理交互式会话中手动调用技能时，则遵循该代理会话本身的策略。

### 隔离式离线演示

在安装了 `bubblewrap` 的 Linux 上，从 `autovibeidea/` 目录运行：

```bash
bash ../scripts/isolated_demo.sh
```

离线运行器不开放凭据或网络。在线研究任务可放在仅包含所需仓库副本和凭据的可丢弃虚拟机中运行，两种环境分别用于离线检查与在线调用。

### 输入、输出与会话记录

在线运行时，提示词、检索文本和相关文件可能发送给配置的模型服务。本地输出与日志目录、API 会话 JSON 文件及 Codex 会话历史中也可能保留这些内容；启动器会在在线执行前打印提示。

完整说明见 [EAR 数据处理文档](../docs/operations.md#execution-safety-and-data-handling)。

---

## 研究适配评估

选题筛选从研究任务本身出发：命题能否被检验或证伪、必要证据能否获取、最小可信结果能否在预算内完成，以及任务是否符合用户明确给出的能力、兴趣与范围约束。生成阶段将四项检查各评为 1–5 分，总分 20，保留 `scores.researcher_fit` 字段；深度筛选阶段进一步核对证据与资源估计，沿用 `strategic` 的 0–10 分输出。未提供的个人偏好、能力或资源记为待确认信息，纯理论研究可用精确命题和证明义务说明其可检验性。

## 致谢

本项目的工程结构受到 [ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) 的启发。`idea-screen` 中的创新性评估模块改编自其创新性检查技能。

## 许可证

MIT. Copyright (c) 2026 Yingze Li, Dong Wang, Ben Wu.

详见 [LICENSE](../LICENSE)。
