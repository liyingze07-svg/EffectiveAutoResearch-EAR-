---
name: start
description: 在后台启动完整的 idea 发现 pipeline。接受研究方向和目标会议，立即返回 PID 和监控命令，pipeline 全程无人值守运行。Use when user says "跑一下", "开始", "帮我找idea", "start pipeline", "launch", or provides a research direction with a venue.
argument-hint: "[研究方向] -- venue: ICML"
allowed-tools: Bash(*)
---

# EAR — 后台启动

研究方向：$ARGUMENTS

## 执行步骤

### Step 1: 解析参数

从 `$ARGUMENTS` 中提取：

- **DIRECTION**: `--` 之前的所有内容（研究方向，去除首尾引号）
- **VENUE**: `-- venue:` 之后的值，默认 `ICML`

支持格式：
- `"探索 LLM 幻觉理论" -- venue: NeurIPS`
- `LLM tool use hallucination -- venue: VLDB`
- `"方向描述"`（无 venue → 默认 ICML）

### Step 2: 启动后台 Pipeline

执行以下 Bash 命令（完全自动，不等待完成）：

```bash
cd /path/to/project   # 切换到 SKILL.md 所在的项目根目录
mkdir -p outputs logx

# 生成带时间戳的日志路径
LOGFILE="logx/start_$(date +%Y%m%d_%H%M%S).log"

# 后台启动
nohup bash run.sh "$DIRECTION" "$VENUE" > "$LOGFILE" 2>&1 &
echo $! > outputs/pipeline.pid
echo "$LOGFILE" > outputs/pipeline_logfile.txt
```

**关键**：用 `Bash` 工具实际执行上述命令（填入解析到的真实 DIRECTION 和 VENUE），不要只描述。

### Step 3: 立即返回状态

执行后立即输出以下内容给用户（不等待 pipeline 完成）：

```
Pipeline 已在后台启动

方向: [DIRECTION]
会议: [VENUE]
PID:  [实际 PID]
日志: [LOGFILE 路径]

监控命令:
  tail -f [LOGFILE]          # 实时查看进度
  ./run.sh --status          # 查看 pipeline 状态
  cat outputs/PIPELINE_LOG.md # 查看阶段决策记录

预计耗时: 30-60 分钟（取决于 API 速度）

产出文件（完成后）:
  outputs/CRITICAL_ANALYSIS.md   — landscape 批判清单
  outputs/IDEAS_FILTERED.md      — 筛选后的 idea（4-6 个）
  outputs/SCREENING_RANKED.md    — 多维评分排名
  refine-logs/FINAL_PROPOSAL.md  — 最终精炼提案
  outputs/IDEA_DISCOVERY_REPORT.md — 全流程汇总报告
```

### Step 4: 验证启动成功

用 Bash 执行：

```bash
sleep 2 && kill -0 $(cat outputs/pipeline.pid 2>/dev/null) 2>/dev/null && echo "✅ 进程运行中" || echo "⚠️ 进程未找到，检查日志"
# 显示日志前 10 行确认已启动
head -5 "$LOGFILE" 2>/dev/null
```

## 规则

- **立即返回**：启动后不等待 pipeline 完成，直接告诉用户 PID 和监控方法
- **完全自主**：不问用户任何问题，direction 和 venue 从 $ARGUMENTS 提取
- **venue 默认**：若未指定 venue，使用 `ICML`
- **工作目录**：所有命令在包含 `run.sh` 的目录下执行（即项目根目录）
