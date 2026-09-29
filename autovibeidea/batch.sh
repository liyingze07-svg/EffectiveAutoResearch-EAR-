#!/bin/bash
# EAR 批量运行脚本
# 顺序执行多个研究方向的 idea discovery pipeline
# 每轮完成后自动归档，再启动下一轮
#
# 用法:
#   nohup ./batch.sh > batch_run.log 2>&1 &   # 后台挂机
#   tail -f batch_run.log                       # 查看进度

set -e
cd "$(dirname "$0")"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

LOG="batch_run.log"

log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG"
}

# ============================================================
# 在这里定义你的研究方向 (按顺序执行)
# 格式: "方向描述|会议|归档名"
# ============================================================
TASKS=(
    "<在此填写研究方向：1-2 句话说明问题、领域和约束>|ICML|MyRun_01"
    # 示例: "sample efficiency of offline RL with image observations|NeurIPS|OfflineRL_01"
    # 每行一个方向，会按顺序依次跑完整 pipeline 并自动归档
)

# ============================================================

TOTAL=${#TASKS[@]}
log "${GREEN}EAR 批量模式: $TOTAL 个研究方向${NC}"
log ""

for i in "${!TASKS[@]}"; do
    IFS='|' read -r DIRECTION VENUE NAME <<< "${TASKS[$i]}"
    SEQ=$((i + 1))

    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log "${GREEN}[$SEQ/$TOTAL] 启动: $NAME${NC}"
    log "  方向: $DIRECTION"
    log "  会议: $VENUE"
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # 确保 outputs 是干净的
    mkdir -p outputs refine-logs

    START_TIME=$(date +%s)
    log "开始时间: $(date '+%H:%M:%S')"

    # 核心: 用短 prompt 让 agent 自己读 SKILL.md 并执行
    if claude -p "你是 EAR 自动化科研 Agent。请完成以下任务:

1. 读取文件 skills/idea-pipeline/SKILL.md，这是你的完整工作流指令
2. 严格按照该文件中的 Pipeline 流程执行
3. 研究方向: \"${DIRECTION}\"
4. 目标会议: ${VENUE}
5. 使用所有可用工具 (WebSearch, Write, Read, Bash, Glob, Grep 等)
6. 所有输出使用中文，技术术语可保留英文
7. 不要询问任何问题，完全自主执行
8. 每个 Phase 完成后将决策记录到 outputs/PIPELINE_LOG.md

现在请读取 skills/idea-pipeline/SKILL.md 并立即开始 Phase 1。" --dangerously-skip-permissions --verbose >> "outputs/pipeline.log" 2>&1; then
        log "${GREEN}✅ [$SEQ/$TOTAL] $NAME 完成${NC}"
    else
        log "${RED}⚠️ [$SEQ/$TOTAL] $NAME 异常退出 (exit code: $?)${NC}"
    fi

    END_TIME=$(date +%s)
    DURATION=$(( (END_TIME - START_TIME) / 60 ))
    log "耗时: ${DURATION} 分钟"

    # 归档本轮结果
    log "归档: $NAME"
    ./clean.sh --name "${NAME}" 2>&1 | tee -a "$LOG"

    log ""
done

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "${GREEN}🎉 全部 $TOTAL 个研究方向已完成！${NC}"
log ""
log "查看结果:"
ls -d archive/*/ 2>/dev/null | while read dir; do
    log "  📁 $dir"
done
