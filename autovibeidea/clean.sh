#!/bin/bash
# EAR 清理/备份脚本
# 用法:
#   ./clean.sh              # 备份当前结果，为下一次科研腾出空间
#   ./clean.sh --list       # 只列出会被备份的文件，不执行
#   ./clean.sh --name "AI4DB_v1"  # 自定义备份名称

set -e
cd "$(dirname "$0")"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 备份名称
CUSTOM_NAME=""
LIST_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --name) CUSTOM_NAME="$2"; shift 2 ;;
        --list) LIST_ONLY=true; shift ;;
        --help|-h)
            echo "EAR 清理/备份脚本"
            echo ""
            echo "用法:"
            echo "  ./clean.sh                       备份当前结果到 archive/"
            echo "  ./clean.sh --list                只列出文件，不执行"
            echo "  ./clean.sh --name \"AI4DB_v1\"     自定义备份名称"
            echo ""
            echo "备份内容:"
            echo "  outputs/        → archive/{name}/outputs/"
            echo "  refine-logs/    → archive/{name}/refine-logs/"
            echo ""
            echo "不会被清理的:"
            echo "  skills/          Skills 定义文件"
            echo "  venue-profiles/  会议审稿人画像"
            echo "  tools/           工具脚本"
            echo "  docs/            文档"
            echo "  archive/         历史备份"
            exit 0
            ;;
        *) echo "未知参数: $1"; exit 1 ;;
    esac
done

# 生成备份目录名
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
if [ -n "$CUSTOM_NAME" ]; then
    BACKUP_DIR="archive/${CUSTOM_NAME}_${TIMESTAMP}"
else
    # 尝试从 PIPELINE_STATE.json 提取方向作为名称
    if [ -f outputs/PIPELINE_STATE.json ]; then
        DIRECTION=$(python3 -c "import json; print(json.load(open('outputs/PIPELINE_STATE.json')).get('direction','unknown')[:30])" 2>/dev/null || echo "unknown")
        # 清理文件名不安全字符
        SAFE_NAME=$(echo "$DIRECTION" | tr ' /:?*"<>|' '_' | tr -s '_')
        BACKUP_DIR="archive/${SAFE_NAME}_${TIMESTAMP}"
    else
        BACKUP_DIR="archive/run_${TIMESTAMP}"
    fi
fi

# 要备份的目录和文件
TARGETS=()
[ -d "outputs" ] && [ "$(ls -A outputs/ 2>/dev/null)" ] && TARGETS+=("outputs")
[ -d "refine-logs" ] && [ "$(ls -A refine-logs/ 2>/dev/null)" ] && TARGETS+=("refine-logs")

if [ ${#TARGETS[@]} -eq 0 ]; then
    echo "没有需要清理的内容 (outputs/ 和 refine-logs/ 都是空的)"
    exit 0
fi

# 列出模式
if $LIST_ONLY; then
    echo -e "${YELLOW}以下文件将被备份到 ${BACKUP_DIR}/${NC}"
    echo ""
    for target in "${TARGETS[@]}"; do
        echo "📁 ${target}/"
        find "$target" -type f -printf "   %p (%s bytes)\n" 2>/dev/null
    done
    echo ""
    TOTAL_SIZE=$(du -sh "${TARGETS[@]}" 2>/dev/null | tail -1 | cut -f1)
    echo "总大小: ~${TOTAL_SIZE}"
    echo ""
    echo "运行 ./clean.sh 执行备份"
    exit 0
fi

# 执行备份
echo -e "${GREEN}备份当前结果...${NC}"
echo "目标: ${BACKUP_DIR}/"
echo ""

mkdir -p "$BACKUP_DIR"

for target in "${TARGETS[@]}"; do
    echo "  移动 ${target}/ → ${BACKUP_DIR}/${target}/"
    mv "$target" "${BACKUP_DIR}/"
done

# 重建空目录
mkdir -p outputs refine-logs

echo ""
echo -e "${GREEN}✅ 备份完成${NC}"
echo ""
echo "备份位置: ${BACKUP_DIR}/"
ls -la "${BACKUP_DIR}/"
echo ""
echo "查看历史备份: ls archive/"
echo "恢复备份: mv ${BACKUP_DIR}/outputs/* outputs/"
echo ""
echo "现在可以开始新一轮科研了:"
echo "  ./run.sh --daemon \"新的研究方向\" ICML"
