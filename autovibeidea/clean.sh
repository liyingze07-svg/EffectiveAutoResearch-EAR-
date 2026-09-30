#!/bin/bash
# EAR cleanup/backup script
# Usage:
#   ./clean.sh              # Back up current results to prepare for the next research run
#   ./clean.sh --list       # List files that would be backed up without making changes
#   ./clean.sh --name "AI4DB_v1"  # Custom backup name

set -e
cd "$(dirname "$0")"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Backup name
CUSTOM_NAME=""
LIST_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --name) CUSTOM_NAME="$2"; shift 2 ;;
        --list) LIST_ONLY=true; shift ;;
        --help|-h)
            echo "EAR cleanup/backup script"
            echo ""
            echo "Usage:"
            echo "  ./clean.sh                       Back up current results to archive/"
            echo "  ./clean.sh --list                List files without making changes"
            echo "  ./clean.sh --name \"AI4DB_v1\"     Custom backup name"
            echo ""
            echo "Backup contents:"
            echo "  outputs/        → archive/{name}/outputs/"
            echo "  refine-logs/    → archive/{name}/refine-logs/"
            echo ""
            echo "Preserved:"
            echo "  skills/          Skill definitions"
            echo "  venue-profiles/  Venue reviewer profiles"
            echo "  tools/           Tool scripts"
            echo "  docs/            Documentation"
            echo "  archive/         Previous backups"
            exit 0
            ;;
        *) echo "Unknown argument: $1"; exit 1 ;;
    esac
done

# Generate the backup directory name
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
if [ -n "$CUSTOM_NAME" ]; then
    BACKUP_DIR="archive/${CUSTOM_NAME}_${TIMESTAMP}"
else
    # Try extracting the direction from PIPELINE_STATE.json for the name
    if [ -f outputs/PIPELINE_STATE.json ]; then
        DIRECTION=$(python3 -c "import json; print(json.load(open('outputs/PIPELINE_STATE.json')).get('direction','unknown')[:30])" 2>/dev/null || echo "unknown")
        # Sanitize characters that are unsafe in file names
        SAFE_NAME=$(echo "$DIRECTION" | tr ' /:?*"<>|' '_' | tr -s '_')
        BACKUP_DIR="archive/${SAFE_NAME}_${TIMESTAMP}"
    else
        BACKUP_DIR="archive/run_${TIMESTAMP}"
    fi
fi

# Directories and files to back up
TARGETS=()
[ -d "outputs" ] && [ "$(ls -A outputs/ 2>/dev/null)" ] && TARGETS+=("outputs")
[ -d "refine-logs" ] && [ "$(ls -A refine-logs/ 2>/dev/null)" ] && TARGETS+=("refine-logs")

if [ ${#TARGETS[@]} -eq 0 ]; then
    echo "Nothing to clean up (outputs/ and refine-logs/ are both empty)"
    exit 0
fi

# List-only mode
if $LIST_ONLY; then
    echo -e "${YELLOW}The following files will be backed up to ${BACKUP_DIR}/${NC}"
    echo ""
    for target in "${TARGETS[@]}"; do
        echo "📁 ${target}/"
        find "$target" -type f -printf "   %p (%s bytes)\n" 2>/dev/null
    done
    echo ""
    TOTAL_SIZE=$(du -sh "${TARGETS[@]}" 2>/dev/null | tail -1 | cut -f1)
    echo "Total size: ~${TOTAL_SIZE}"
    echo ""
    echo "Run ./clean.sh to perform the backup"
    exit 0
fi

# Perform the backup
echo -e "${GREEN}Backing up current results...${NC}"
echo "Destination: ${BACKUP_DIR}/"
echo ""

mkdir -p "$BACKUP_DIR"

for target in "${TARGETS[@]}"; do
    echo "  Move ${target}/ → ${BACKUP_DIR}/${target}/"
    mv "$target" "${BACKUP_DIR}/"
done

# Recreate empty directories
mkdir -p outputs refine-logs

echo ""
echo -e "${GREEN}✅ Backup complete${NC}"
echo ""
echo "Backup location: ${BACKUP_DIR}/"
ls -la "${BACKUP_DIR}/"
echo ""
echo "View previous backups: ls archive/"
echo "Restore a backup: mv ${BACKUP_DIR}/outputs/* outputs/"
echo ""
echo "You can now start a new research run:"
echo "  ./run.sh --daemon \"new research direction\" ICML"
