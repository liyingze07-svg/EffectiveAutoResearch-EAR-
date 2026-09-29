# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EAR is an automated research idea discovery and refinement pipeline. It chains four core skills to go from a research topic to a venue-ready proposal:

```
/lit-survey → /idea-gen → /idea-screen → /idea-refine
```

One-shot orchestration: `/idea-pipeline "research direction" -- venue: ICML`
Background launch: `/start "research direction" -- venue: NeurIPS`

If the direction is not yet fixed, run `/idea-filter "constraints and interests"` first — it converges vague interests into 1-3 locked directions plus a focused pipeline prompt.

## Running the Pipeline

```bash
./run.sh "research direction" VLDB        # full pipeline
./run.sh --daemon "direction" NeurIPS     # background
./run.sh --survey / --gen / --screen / --refine   # individual phases
./run.sh --refine "idea -- mode: socratic-auto"   # Socratic 对话精炼（全自动）
./run.sh --refine "idea -- mode: socratic-human"  # Socratic 对话精炼（人工参与）
./run.sh --gpt-only "direction" ICML      # 不依赖 Codex MCP，直连 OpenAI API
./run.sh --status                          # 状态检查
nohup ./batch.sh > batch_run.log 2>&1 &   # 批量（先编辑 batch.sh 的 TASKS）
./clean.sh [--name "MyRun_v1"]            # 归档当前产出
```

## Prerequisites

必需其一：

1. **本机 codex CLI（推荐，无需 API key）**：`npm install -g @openai/codex@latest` + `codex login`，跑 `./run.sh --codex-cli`。外部调用走 `tools/codex_call.sh`。
2. `OPENAI_API_KEY` / `~/.openai_key`，跑 `./run.sh --gpt-only`。
3. Codex MCP：`claude mcp add codex -s user -- codex mcp-server` —— **codex CLI ≥0.158.0 已移除 `mcp-server` 子命令，此方式在新版上失效**（表现为 `CONNECTION_CLOSED`）。
可选：Zotero MCP、Obsidian MCP（供 `/lit-survey` 检索本地论文库与笔记）。

## Skills

| Skill | Purpose | Invocation |
|-------|---------|-----------|
| `/idea-filter` | 约束驱动的方向收敛 → 1-3 个锁定方向 + focused pipeline prompt | `/idea-filter "低资源、偏理论"` |
| `/lit-survey` | Literature survey → `LANDSCAPE.md` + `LANDSCAPE.json` | `/lit-survey "topic"` |
| `/idea-gen` | 批判清单 → 8-12 ideas → 4-6 filtered → `IDEAS_FILTERED.md` | `/idea-gen "direction"` |
| `/idea-screen` | Novelty + reviewer simulation + strategic fit → `SCREENING_RANKED.md` | `/idea-screen "idea" -- venue: ICML` |
| `/idea-refine` | 迭代精炼（≤3 轮或 Socratic 对话）→ `FINAL_PROPOSAL.md` | `/idea-refine "idea"` |
| `/idea-pipeline` | Full pipeline orchestrator | `/idea-pipeline "direction" -- venue: VLDB` |
| `/start` | 后台启动完整 pipeline，立即返回 PID | `/start "direction" -- venue: ICML` |
| `/fossil-hunt` | 寻找领域内长期未被质疑的"化石组件" → 排序目标列表 | `/fossil-hunt "domain"` |
| `/exp-design` | 从第一性原理设计论文实验（有效性 + 有用性两支柱） | `/exp-design "method"` |
| `/experiment-audit` | 审计实验代码：数据泄露、baseline 公平性、评测作弊、方法-代码一致性 | `/experiment-audit "dir" -- proposal: path` |
| `/idea-search` | UCT 引导的候选扩展与剪枝（需先有 `IDEA_NODES.jsonl`） | `/idea-search -- budget: 8` |

Skills 定义在 `skills/<name>/SKILL.md`，`.claude/commands/` 下是指向它们的符号链接（改 SKILL.md 即生效，不需要同步副本）。

## Tools

| Tool | Purpose |
|------|---------|
| `tools/arxiv_fetch.py` | arXiv 元数据抓取（`/lit-survey` 内部使用）。对 406/429/5xx 退避重试，失败时给出明确的回退指引而非 traceback。实测 arXiv 可能对新查询持续 406，此时应回退 WebSearch |
| `tools/gpt_call.sh` | OpenAI API curl 封装，模拟 thread 语义（`CODEX_MODE=gpt-api` 时使用）。用 `--phase` 标注阶段，token 用量写入 `outputs/COST_LOG.jsonl` |
| `tools/codex_call.sh` | 用本机 `codex exec` 作为外部模型（`CODEX_MODE=codex-cli` 时使用），接口同 `gpt_call.sh`。`--thread` 文件存 thread_id，有 id 则 `codex exec resume` 续写；同样采集 token |
| `tools/run_codex_skill.sh` | 用 Codex CLI 执行某个 SKILL.md |
| `tools/idea_nodes.py` | 维护 `outputs/IDEA_NODES.jsonl`（idea 作为可审查对象）。`validate` 会拦截缺锚定、缺否证条件、缺分数来源、mask 非法等问题 |
| `tools/dedup_ideas.py` | 标记候选重复 idea 对。**只做标记，机制是否真重复由模型裁定**后再 `mark` |
| `tools/entropy_map.py` | 从 `LANDSCAPE.json` 算高熵区域（立场熵 × 可比性惩罚）与跨论文失效模式 |
| `tools/mcts_search.py` | UCT 引导的搜索驱动。**注意：无随机 rollout**，用 value 估计代替，对外描述见 `docs/SEARCH_DESIGN.md` |

写节点时的两条硬约束：`generator.anchor` 不得为空（每个 idea 必须锚定到具体证据 ID）；`scores.source` 与 `scores.degraded` 必填（降级自评分与正常评分不可比）。`tools/idea_nodes.py validate` 会强制这两条。

## Architecture

**Multi-model design:**
- **Claude**（执行层）：文献检索、文件 I/O、规则过滤、skeleton 抽取、提案编辑、Theory-Experiment 对齐矩阵评估
- **外部 LLM via Codex MCP**（评审/生成层）：landscape 批判（Phase 2a）、批判锚定的头脑风暴（Phase 2b）、查新交叉验证、审稿模拟、迭代评审、Socratic 对话、Deep Expansion Pass。统一使用 `config: {"model_reasoning_effort": "xhigh"}`，默认 `REVIEWER_MODEL = gpt-5.4`
- **Fallback**：所有外部调用失败时降级为 Claude 自评并自动下调评分阈值。路由：`--codex-cli` → `tools/codex_call.sh`（本机 codex 登录态）；`--gpt-only` → `tools/gpt_call.sh`（OpenAI API）

**Screening composite score**：`0.25×Novelty + 0.35×Venue + 0.20×Strategic + 0.20×Feasibility`
≥7.0 → PROCEED | 5.0–6.9 → CAUTION | <5.0 → ABANDON

**Refinement exit criterion**：score ≥9/10 或 `MAX_ROUNDS=3`（标准模式）；或外部模型写出理解声明（Socratic 模式）

**Fault tolerance**：pipeline 全程不等待用户输入（唯一例外是 `-- mode: socratic-human`）。`outputs/PIPELINE_STATE.json` 记录已完成阶段，支持断点续跑。

## Venue Profiles

`venue-profiles/` 是 `/idea-screen` 使用的会场画像：`ICML.md`、`NeurIPS.md`、`EMNLP.md`、`VLDB.md`、`SIGMOD.md`。
新增会场：复制 `_template.md` 填写 calibration tiers 与 reviewer personas。这些 profile 是对公开评审标准的主观归纳，不来自任何会议的内部材料。

## Output Layout

```
outputs/              # 当前运行
  LANDSCAPE.md/.json
  ENTROPY_MAP.json      # 高熵区域 + 失效模式（lit-survey 可选扩展）
  IDEA_NODES.jsonl      # 每个 idea 的结构化记录（含剪枝 mask 与派生谱系）
  COST_LOG.jsonl        # token 与 wall-clock 用量（仅 --gpt-only 路径）
  SEARCH_STATE.json     # 搜索参数；SEARCH_REPORT.md 为搜索报告
  CRITICAL_ANALYSIS.md
  IDEAS_RAW.md / IDEAS_FILTERED.md
  SCREENING_REPORT.md / SCREENING_RANKED.md
  IDEA_DISCOVERY_REPORT.md
  PIPELINE_LOG.md / PIPELINE_STATE.json

refine-logs/          # 精炼历史
  skeleton.md
  round-N-review.md / round-N-refinement.md / round-N-expanded.md
  socratic-turn-T-*.md / socratic-final-review.md
  REVIEW_SUMMARY.md / FINAL_PROPOSAL.md / REFINEMENT_REPORT.md

archive/              # 历史运行（clean.sh 自动归档）
```

## All outputs are in Chinese (中文). Technical terms remain in English.

## 贡献边界

新增功能时同步更新 `README.md` 的能力分级表（`Implemented` / `Experimental` / `Roadmap`）——没有对应实现的能力不要写进 Implemented。

新增或修改评分机制时，注意：本 pipeline 的所有分数均由 LLM 产生，不是同行评审。方法论出处见 `README.md` 的致谢一节，设计取舍见 `DESIGN_RATIONALE.md`。

---

## 关键设计（v2）

- **R1 两段式生成**：Phase 2a 批判 landscape（四类结构性弱点 → `CRITICAL_ANALYSIS.md`），Phase 2b 同线程生成 idea，每个必须锚定 CRITIQUE-ID
- **R2 Deep Expansion Pass（Phase 5.5）**：review 循环结束后扫 `[EXPAND]` 章节，只填公式/伪代码/接口维度/超参范围，不改方向 → `round-N-expanded.md`
- **R3 理论化加强**：`idea-gen` 要求 Theorem/Conjecture Scaffold；`idea-refine` Phase 1.4.T 做 Formalizability Scan + Assumption Inventory
- **R4 外部模型路径**：`CODEX_MODE=gpt-api` → `tools/gpt_call.sh`；`CODEX_MODE=codex-cli` → `tools/codex_call.sh`（codex CLI 移除 `mcp-server` 后的替代路径）
- **R5 Socratic 模式**：外部模型先追问 3-5 条具体机制问题，直到写出理解声明才允许打分（`MAX_DIALOGUE_TURNS=5`）
- **R6 Theory-Experiment Alignment**：Phase 1.4.TE 按 claim 类型查表配验证协议与最小规模，NOT FEASIBLE 的 claim 标 ⚠️ 并给三条出路；Phase 5.5 后二次检查
