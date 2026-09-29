# EAR — Effective Auto Research

自动化科研 Idea 发现流水线。给一个研究方向，后台跑完整 pipeline，输出经过批判分析、多维筛选、审稿人模拟和理论-实验对齐检查的 venue-ready 提案。

所有产出为中文，技术术语保留英文。

---

## 能力分级

本表按"仓库里有没有对应实现"分档。**Implemented = 代码在仓库里、跑 pipeline 就会执行；Experimental = 已实现但未做过对照测量；Roadmap = 尚未实现。** 请不要把 Roadmap 项当作本项目当前的能力。

### Implemented

| 能力 | 入口 |
|---|---|
| 四级信源文献调研 + Gap Identification Matrix（带类型枚举与置信度） | `/lit-survey` |
| 两段式生成：landscape 四维批判 → idea 必须锚定 CRITIQUE-ID | `/idea-gen` Phase 2a/2b |
| 多层过滤：可行性 → 查新 → 影响力 → Researcher-Fit Filter（12/20）→ 反 anti-pattern | `/idea-gen` Phase 3-5 |
| 查新 + 会场审稿模拟（3 审稿人 + meta review）+ 战略契合，合成分排序 | `/idea-screen` |
| Problem Anchor 冻结与 drift detection | `/idea-refine` Phase 0 |
| Skeleton（State A→B）+ 逐轮 skeleton gap check | `/idea-refine` Phase 0.5 / 3.3 |
| Theory-Experiment Alignment Matrix（claim 类型 → 验证协议 → 最小规模 → 可行性判定） | `/idea-refine` Phase 1.4.TE |
| Deep Expansion Pass（公式 / 伪代码 / 接口维度 / 超参范围） | `/idea-refine` Phase 5.5 |
| Socratic 对话模式（理解声明作为打分前置条件） | `/idea-refine -- mode: socratic-*` |
| 三条外部模型路径：本机 codex CLI（无需 key）/ OpenAI API / Codex MCP，失败自动降级 | `--codex-cli` → `tools/codex_call.sh`；`--gpt-only` → `tools/gpt_call.sh` |
| 断点续跑、全程无人值守、外部模型不可用时自动降级 | `PIPELINE_STATE.json` / 各 skill 的 fallback |

### Experimental

处于打磨阶段的能力，接口与默认参数可能调整。

| 能力 | 工具 / 入口 | 说明 |
|---|---|---|
| `IDEA_NODES.jsonl`：每个 idea 作为可审查对象（生成算子、锚定证据、否证条件、剪枝 mask、成本、派生谱系） | `tools/idea_nodes.py`，schema 见 `docs/IDEA_NODE_SCHEMA.md` | 统一的候选记录格式，支撑剪枝统计与派生谱系 |
| 候选重复标记（概念归一 + 词法/结构重叠 + 血缘跳过 + 样板文本过滤，输出候选对供模型裁定） | `tools/dedup_ideas.py` | 阈值为经验值，建议以 `--top` 排序结果为主要依据 |
| 高熵区域挖掘（同一 claim 的立场熵 × **可比性惩罚**，排除设定不同导致的伪冲突） | `tools/entropy_map.py` | 可比性惩罚可按子领域调整权重 |
| 失效模式挖掘（跨论文共享的失效条件聚合） | 同上 | 失效条件按文本归一聚类，结果建议人工复核 |
| token 成本埋点 | `tools/gpt_call.sh` → `outputs/COST_LOG.jsonl` | 覆盖 `--gpt-only` 与 `--codex-cli` 两条路径；Codex MCP 路径不返回用量 |
| Prompt 级多样性约束（≥50% idea 锚定不同批判、单批判 ≤3 个 idea、风险分层） | `idea-gen` Phase 2b | 约束在生成阶段施加，配合 `dedup_ideas.py` 复核 |
| Researcher-Fit Filter 的 12/20 阈值 | `idea-gen` Phase 4 | 阈值可按研究者偏好调整 |
| Deep Expansion Pass 的增益 | `idea-refine` Phase 5.5 | 把"评价方向"与"填充实现细节"拆成两个独立阶段 |
| **UCT 引导的候选扩展 + mask 先验剪枝**（Selection / Expansion / Backup 三阶段，**无随机 rollout**，用 value 估计代替） | `/idea-search`、`tools/mcts_search.py`，设计见 `docs/SEARCH_DESIGN.md` | UCT 常数 c=1.414 为标准取值，可按需调整 |
| reward 混入可验证信号（`retrieval` / `feasibility_rule` / `falsifiability` / `cost_efficiency` / `distinctness`，默认 alpha=0.5） | 同上，`report --provenance` 逐项打印来源 | 各成分等权平均，alpha 控制 LLM 评分的占比 |
| Trajectory Analysis | `lit-survey -- trace: true` | 默认关闭，用 `-- trace: true` 启用 |

### Roadmap

**尚未实现**，列在这里是为了说明设计方向，不是当前能力：

| 计划 | 现状 |
|---|---|
| 完整 MCTS（含随机 rollout） | 不在计划内——研究 idea 无法随机模拟到终局，现有实现用 value 估计代替 rollout，见 `docs/SEARCH_DESIGN.md` |
| reward 的结果信号 | 现有可验证成分刻画的是提案属性；接入 pilot 实验结果是下一步 |
| Scaling regime 挖掘视角 | 无。Phase 2a 仍是四个维度。Contradiction 视角已由高熵区域部分覆盖 |
| 把 pilot experiment 制度化为 pipeline 阶段 | 无。目前 pilot 由人手工跑，是链路中唯一能接触真实实验结果的环节 |
| 创新模式库（gap × pattern 两个正交轴） | 当前只有"批判维度"一个轴（4 个算子） |
| 演进链条作为生成主表示 | 无。Trajectory Analysis 仅为 landscape 的可选小节 |
| 完整 token 成本基线 | Codex MCP 路径不返回用量数据 |

---

## 快速开始

```bash
git clone <this-repo> && cd EAR
./run.sh --daemon "你的研究方向" NeurIPS   # 后台跑全流程（推荐）
./run.sh --status                          # 查看进度
tail -f outputs/pipeline.log               # 实时日志
```

在支持 slash command 的 agent 环境（如 Codex REPL）里也可以直接调用：

```
/start "offline RL 在图像观测下的样本效率瓶颈" -- venue: NeurIPS
```

---

## Slash Commands

本仓库不附带任何 agent 工具的私有配置目录。若你的 agent 支持把 markdown 挂成 slash command，
在仓库根目录执行一次即可（以命令目录为 `<CMD_DIR>` 为例）：

```bash
mkdir -p <CMD_DIR>
for d in skills/*/; do
  n=$(basename "$d")
  ln -sf "../../skills/$n/SKILL.md" "<CMD_DIR>/$n.md"
done
```

用符号链接而非复制，改 `SKILL.md` 即时生效、不会失同步。
不挂载也可以直接使用：所有 skill 都是自包含的 markdown，把对应文件内容交给模型即可。


| 命令 | 用途 |
|------|------|
| `/start "方向" -- venue: ICML` | **后台启动完整 pipeline**（最常用） |
| `/idea-filter "约束与兴趣"` | 方向还没定时的前置步骤：从模糊兴趣收敛出 1-3 个锁定方向 |
| `/idea-pipeline "方向" -- venue: ICML` | 前台运行完整 pipeline |
| `/lit-survey "方向"` | 只跑文献调研 |
| `/idea-gen "方向"` | 只跑想点子（含批判分析） |
| `/idea-screen "idea" -- venue: ICML` | 只跑多维筛选 |
| `/idea-refine "idea"` | 只跑深度精炼 |
| `/idea-refine "idea -- mode: socratic"` | Socratic 对话式精炼 |
| `/idea-search -- budget: 8` | 在已有候选上做 UCT 引导的预算分配搜索（mask 先验剪枝 + 扩展 + 回传） |
| `/fossil-hunt "领域"` | 寻找领域内长期无人质疑的"化石组件" |
| `/exp-design "方法描述"` | 从第一性原理设计论文实验 |
| `/experiment-audit "代码目录"` | 审计实验代码的学术诚信问题 |

---

## Pipeline 流程

```
（可选）/idea-filter  ——  方向没定时先收敛出锁定方向
    │
    ▼
Phase 1: 文献调研 (/lit-survey)
    四级信源（Zotero MCP → Obsidian MCP → 本地 PDF → WebSearch/arXiv）
    → outputs/LANDSCAPE.md + LANDSCAPE.json（含 Gap Identification Matrix）
    │
    ▼
Phase 2: 两段式想点子 (/idea-gen)
    2a: 外部模型批判 landscape 的四类结构性弱点 → outputs/CRITICAL_ANALYSIS.md
    2b: 每个 idea 必须锚定一个 CRITIQUE-ID，并给出 Theorem/Conjecture Scaffold
    过滤: 可行性 → 查新 → 影响力 → Researcher-Fit Filter → 反 anti-pattern
    → outputs/IDEAS_RAW.md + IDEAS_FILTERED.md（4-6 个）
    │
    ▼
Phase 3: 多维筛选 (/idea-screen)
    Module A 查新  Module B 审稿人模拟  Module C 战略评估
    合成分 = 0.25×Novelty + 0.35×Venue + 0.20×Strategic + 0.20×Feasibility
    → outputs/SCREENING_REPORT.md + SCREENING_RANKED.md
    │
    ▼
（可选）/idea-search  ——  在候选池上分配扩展预算：先验剪枝 → UCT 选择 → 生成机制不同的子候选
    │
    ▼
Phase 4: 深度精炼 (/idea-refine)
    Problem Anchor 冻结 → Skeleton 抽取 → Theoretical Grounding
    → Theory-Experiment Alignment Matrix → review 循环（≤3 轮或 Socratic 对话）
    → Deep Expansion Pass（完整公式/伪代码/接口维度/超参范围）
    → refine-logs/FINAL_PROPOSAL.md
    │
    ▼
Phase 5: 汇总报告 → outputs/IDEA_DISCOVERY_REPORT.md
```

---

## 输出文件

```
outputs/                             ← 为空 = 干净状态，可直接开始
  LANDSCAPE.md / .json               文献地图 + Gap Matrix
  ENTROPY_MAP.json                   高熵区域 + 失效模式（可选）
  IDEA_NODES.jsonl                   每个 idea 的结构化记录（剪枝 mask / 派生谱系 / 成本）
  COST_LOG.jsonl                     token 与 wall-clock 用量（仅 --gpt-only）
  SEARCH_STATE.json                  搜索参数（预算 / alpha / UCT 常数）
  SEARCH_REPORT.md                   搜索树 + reward 成分来源 + 剪枝统计
  CRITICAL_ANALYSIS.md               landscape 批判清单（CRITIQUE-01...N）
  IDEAS_RAW.md / IDEAS_FILTERED.md   原始 / 存活 idea
  SCREENING_REPORT.md / _RANKED.md   多维评分与排名
  IDEA_DISCOVERY_REPORT.md           全流程汇总
  PIPELINE_LOG.md                    每阶段自主决策记录
  PIPELINE_STATE.json                断点续跑用的 checkpoint

refine-logs/
  skeleton.md                        State A → State B 论证骨架
  round-N-review.md / -refinement.md 每轮评审与修订
  round-N-expanded.md                Deep Expansion 产物
  FINAL_PROPOSAL.md                  最终提案
  REFINEMENT_REPORT.md / score-history.md
```

`./clean.sh` 把当前产出归档进 `archive/`，`./clean.sh --name "MyRun_v1"` 指定归档名。

---

## 支持的会议

| 会议 | 类型 |
|------|------|
| `ICML` / `NeurIPS` | ML 方法与理论 / 广泛 ML + 跨学科 |
| `EMNLP` | NLP |
| `VLDB` / `SIGMOD` | 数据库与数据系统 |

新增会议：复制 `venue-profiles/_template.md`，填写 calibration tiers 和审稿人画像。这些 profile 是对公开评审标准的主观归纳，建议按自己的目标会场调整。

---

## 工具

| 工具 | 用途 |
|---|---|
| `tools/arxiv_fetch.py` | arXiv 元数据抓取。对 406/429/5xx 退避重试；**arXiv 节流时应回退 WebSearch，不要死等** |
| `tools/gpt_call.sh` | OpenAI API 封装，模拟 thread 语义；记录 token 用量到 `outputs/COST_LOG.jsonl` |
| `tools/codex_call.sh` | 用本机 codex CLI（`codex exec`）作为外部模型，接口与 `gpt_call.sh` 一致；**无需 API key**，支持 resume 续线程与 token 采集 |
| `tools/idea_nodes.py` | 维护 `IDEA_NODES.jsonl`：init / add / update / validate / stats / tree |
| `tools/dedup_ideas.py` | 标记候选重复 idea 对（需裁定后再 mark） |
| `tools/entropy_map.py` | 从 `LANDSCAPE.json` 算高熵区域与失效模式 |
| `tools/mcts_search.py` | UCT 引导的搜索驱动：init / mask / select / expand / backup / report |
| `scripts/selfcheck.sh` | 提交前自检 |

## 文档

| 文件 | 内容 |
|---|---|
| `docs/IDEA_NODE_SCHEMA.md` | idea 节点字段定义 |
| `docs/SEARCH_DESIGN.md` | 搜索设计：UCT、mask 语义与 reward 各成分 |
| `docs/WORKFLOW.md` | 全流程详解 |
| `examples/judge-run/` | 一次真实运行的脱敏节选，含一个 novelty 判断被二轮补检从 8 推翻到 4 的完整记录 |

## ⚠️ 运行方式的安全提示

`./run.sh` / `./batch_codex.sh` 通过 `tools/run_codex_skill.sh` 调起 codex，使用的是：

```
codex exec --dangerously-bypass-approvals-and-sandbox
```

即 **codex 在无沙箱、无逐步确认的模式下执行**，因为 pipeline 需要无人值守地读写 `outputs/`、
`refine-logs/` 并调用检索工具。这意味着它可以在你的机器上执行任意 shell 命令。

如果你不接受这个前提，有两条更克制的路径：

1. **在容器/一次性虚拟机里跑**，把仓库目录挂进去。
2. **不用 shell 入口**，改在 agent REPL 里逐个 skill 调用（`/lit-survey`、`/idea-gen` …）。
   这时由你的 REPL 自己的权限策略管控，本仓库不绕过它。

另外 `tools/codex_call.sh`（`--codex-cli` 路径下 skill 内部的单次外部模型调用）**不带**这个 flag，
它只是一次问答，不执行命令。

## 前置依赖

**必需其一：**

```bash
# 方式 A（推荐）: 本机 codex CLI —— 无需 API key，用 codex 自身的登录态
npm install -g @openai/codex@latest
codex login                       # 已登录则跳过
./run.sh --codex-cli "方向" NeurIPS

# 方式 B: 直连 OpenAI API
export OPENAI_API_KEY=...         # 或写入 ~/.openai_key
./run.sh --gpt-only "方向" NeurIPS

# 方式 C: Codex MCP（仅旧版 codex 可用，见下方说明）
claude mcp add codex -s user -- codex mcp-server
```

> ⚠️ **codex CLI 自 0.158.0 起已移除 `mcp-server` 子命令**，方式 C 在新版上会以
> `Connection closed` 失败。新版请用方式 A：`tools/codex_call.sh` 通过 `codex exec`
> 提供等价能力（含 `resume` 续线程与 token 用量采集），已实测可用。

**可选：** Zotero MCP（搜索本地论文库）、Obsidian MCP（搜索笔记）。两者缺失时自动降级为 WebSearch。

外部模型调用失败时，所有 skill 会 fallback 到本地 agent 自评并自动降级评分阈值，pipeline 不会停下等待输入。

---

## 已知局限

整条流水线的所有信号都来自大语言模型的判断——批判清单、查新结论、审稿模拟分数、精炼分数，没有任何一项来自真实实验。因此：

- **分数不是同行评审。** `refine-logs/score-history.md` 里的分数是外部模型对提案文本的评价，不预测真实录用结果。
- **"没查到相似工作"只说明当前检索范围内没发现碰撞。** 建议读 `SCREENING_REPORT.md` 里"与最接近工作的具体差异"，而不是只看 Novelty 分。
- **可行性是静态估计。** `Theory-Experiment Alignment Matrix` 用领域先验估算每条理论 claim 的验证代价，是低成本近似，不等于跑过实验。


---

## 致谢

本项目的工程形态受 [ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) 影响，`idea-screen` 的 Novelty Assessment 模块改写自其 `novelty-check` skill。
`idea-gen` 的 Researcher-Fit Filter（Longevity / Passion / Application / Uniqueness 四维）改写自公开发表的科研选题方法论，见 [openbs](https://github.com/HeBingsheng/openbs)。

## License

MIT
