#!/bin/bash
# EAR 快速启动脚本（Codex 版）
# 用法:
#   ./run.sh                           # 交互模式
#   ./run.sh "研究方向"                  # 全流程
#   ./run.sh "研究方向" VLDB             # 指定会议
#   ./run.sh --survey "研究方向"         # 只跑文献调研
#   ./run.sh --gen "研究方向"            # 只跑想点子
#   ./run.sh --screen "idea描述" ICML    # 只跑筛选
#   ./run.sh --refine "idea描述"         # 只跑精炼
#   ./run.sh --daemon "研究方向" VLDB    # 后台运行 (nohup)
#   ./run.sh --status                    # 查看运行状态

set -e
cd "$(dirname "$0")"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 解析 --gpt-only flag（可出现在任意位置）
GPT_ONLY=false
CODEX_CLI_MODE=false
FILTERED_ARGS=()
for arg in "$@"; do
    if [ "$arg" = "--gpt-only" ]; then
        GPT_ONLY=true
        export CODEX_MODE=gpt-api
    elif [ "$arg" = "--codex-cli" ]; then
        CODEX_CLI_MODE=true
        export CODEX_MODE=codex-cli
    else
        FILTERED_ARGS+=("$arg")
    fi
done
set -- "${FILTERED_ARGS[@]}"
if [ "$CODEX_CLI_MODE" = "true" ]; then
    echo -e "${YELLOW}Codex CLI 模式已启用 (CODEX_MODE=codex-cli)${NC}"
    echo "  外部模型调用将走 tools/codex_call.sh（本机 codex 登录态，无需 API key）"
    echo ""
fi

if [ "$GPT_ONLY" = "true" ]; then
    echo -e "${YELLOW}GPT-only 模式已启用 (CODEX_MODE=gpt-api)${NC}"
    echo "  skill 内部需要额外二次推理时将优先尝试 tools/gpt_call.sh"
    echo ""
fi

# 检查 Codex CLI
if ! command -v codex &> /dev/null && ! command -v codex.exe &> /dev/null; then
    echo "错误: 未找到 codex 命令。请先安装 Codex CLI:"
    echo "  npm install -g @openai/codex"
    exit 1
fi

if command -v codex.exe &> /dev/null; then
    CODEX_CMD="$(command -v codex.exe)"
else
    CODEX_CMD="$(command -v codex)"
fi

# 确保 outputs 目录存在
mkdir -p outputs refine-logs

# 辅助函数: 用 Codex 执行 skill
run_skill() {
    local SKILL_FILE="$1"
    local ARGS="$2"
    bash tools/run_codex_skill.sh \
        --skill "$SKILL_FILE" \
        --args "$ARGS" \
        --role "一个自动化科研 Agent"
}

MODE="${1:---interactive}"
DIRECTION="$1"
VENUE="${2:-ICML}"

case "$MODE" in
    --interactive|-i)
        echo -e "${GREEN}EAR Codex 交互模式${NC}"
        echo "推荐优先使用这些 shell 入口命令:"
        echo "  ./run.sh \"研究方向\" ICML                     全流程"
        echo "  ./run.sh --survey \"研究方向\"                  文献调研"
        echo "  ./run.sh --gen \"研究方向\"                     想点子"
        echo "  ./run.sh --screen \"idea\" VLDB                多维筛选"
        echo "  ./run.sh --refine \"idea\"                      深度精炼"
        echo ""
        "$CODEX_CMD" --search "Read CODEX_COMPAT.md and README.md in the current workspace, then help operate this EAR repository in Codex-only mode."
        ;;
    --survey)
        echo -e "${GREEN}运行文献调研: $2${NC}"
        run_skill "skills/lit-survey/SKILL.md" "$2"
        ;;
    --gen)
        echo -e "${GREEN}运行想点子: $2${NC}"
        run_skill "skills/idea-gen/SKILL.md" "$2"
        ;;
    --screen)
        echo -e "${GREEN}运行多维筛选 (venue: ${3:-ICML}): $2${NC}"
        run_skill "skills/idea-screen/SKILL.md" "$2 -- venue: ${3:-ICML}"
        ;;
    --refine)
        echo -e "${GREEN}运行深度精炼: $2${NC}"
        run_skill "skills/idea-refine/SKILL.md" "$2"
        ;;
    --daemon)
        DIRECTION="$2"
        VENUE="${3:-ICML}"
        echo -e "${GREEN}EAR 后台模式${NC}"
        echo -e "方向: $DIRECTION"
        echo -e "会议: $VENUE"
        echo "日志: outputs/pipeline.log"
        echo ""
        cat > outputs/.run_pipeline.sh << 'RUNEOF_HEAD'
#!/bin/bash
set -e
cd "$(dirname "$0")/.."
RUNEOF_HEAD
        cat >> outputs/.run_pipeline.sh << RUNEOF_BODY
bash tools/run_codex_skill.sh \
  --skill skills/idea-pipeline/SKILL.md \
  --args "\"${DIRECTION}\" -- venue: ${VENUE}" \
  --role "一个自动化科研 Agent" \
  2>&1 | tee outputs/pipeline.log
date -Iseconds > outputs/DONE
RUNEOF_BODY
        chmod +x outputs/.run_pipeline.sh
        nohup bash outputs/.run_pipeline.sh > /dev/null 2>&1 &
        BGPID=$!
        echo "后台进程 PID: $BGPID"
        echo $BGPID > outputs/pipeline.pid
        echo -e "${GREEN}Pipeline 已在后台启动。${NC}"
        echo "  查看进度: ./run.sh --status"
        echo "  查看日志: tail -f outputs/pipeline.log"
        echo "  停止运行: kill \$(cat outputs/pipeline.pid)"
        ;;
    --status)
        echo -e "${GREEN}EAR 状态${NC}"
        echo ""
        if [ -f outputs/DONE ]; then
            echo -e "${GREEN}✅ Pipeline 已完成${NC}"
            cat outputs/DONE
        elif [ -f outputs/pipeline.pid ] && kill -0 "$(cat outputs/pipeline.pid)" 2>/dev/null; then
            echo "🔄 Pipeline 运行中 (PID: $(cat outputs/pipeline.pid))"
        else
            echo "⏹ Pipeline 未在运行"
        fi
        echo ""
        if [ -f outputs/PIPELINE_STATE.json ]; then
            echo "状态文件:"
            cat outputs/PIPELINE_STATE.json
        fi
        echo ""
        if [ -f outputs/PIPELINE_LOG.md ]; then
            echo "最新日志:"
            tail -20 outputs/PIPELINE_LOG.md
        fi
        ;;
    --help|-h)
        echo "EAR - AI 科研选题自动化工作流"
        echo ""
        echo "用法:"
        echo "  ./run.sh                              交互模式"
        echo "  ./run.sh \"研究方向\"                    全流程 (默认 ICML)"
        echo "  ./run.sh \"研究方向\" VLDB               全流程 (指定会议)"
        echo "  ./run.sh --survey \"研究方向\"            只跑文献调研"
        echo "  ./run.sh --gen \"研究方向\"               只跑想点子"
        echo "  ./run.sh --screen \"idea\" ICML          只跑筛选"
        echo "  ./run.sh --refine \"idea\"               只跑精炼"
        echo "  ./run.sh --daemon \"研究方向\" VLDB      后台运行 (nohup)"
        echo "  ./run.sh --status                       查看运行状态"
        echo ""
        echo "选项:"
        echo "  --gpt-only                              GPT-only 模式（仅影响 skill 内部二次推理降级策略）"
        echo "  --codex-cli                             用本机 codex CLI 作为外部模型（无需 API key）"
        echo "  在 --refine 中追加 -- mode: socratic    Socratic 对话精炼模式"
        echo "  在 --refine 中追加 -- mode: socratic-human  人工参与 Socratic 精炼"
        echo ""
        echo "支持的会议: ICML, VLDB, NeurIPS, SIGMOD"
        echo "输出目录: outputs/, refine-logs/"
        ;;
    *)
        # 默认: 当第一个参数不是 flag 时，当作研究方向跑全流程
        echo -e "${GREEN}EAR 全流程${NC}"
        echo -e "方向: $DIRECTION"
        echo -e "会议: $VENUE"
        echo ""
        run_skill "skills/idea-pipeline/SKILL.md" "\"$DIRECTION\" -- venue: $VENUE"
        ;;
esac
