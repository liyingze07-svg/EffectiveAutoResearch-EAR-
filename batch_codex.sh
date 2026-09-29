#!/bin/bash
# Batch runner for EAR.
#
# Runs multiple idea-pipeline jobs sequentially with isolated workspaces and
# archives each result bundle under archive/ to avoid overwrite.
#
# Usage:
#   bash batch_codex.sh
#   bash batch_codex.sh --dry-run
#   bash batch_codex.sh --task-file batch_tasks/example.txt
#   nohup bash batch_codex.sh > logx/batch_launcher.log 2>&1 &

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
DEFAULT_TASK_FILE="$PROJECT_ROOT/batch_tasks/example.txt"
TASK_FILE="$DEFAULT_TASK_FILE"
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --task-file)
            TASK_FILE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            cat <<'EOF'
Batch runner for EAR

Options:
  --task-file PATH   Task list file. Default: batch_tasks/example.txt
  --dry-run          Print parsed tasks and exit without running
  --help             Show this help

Task file format:
  One task per line, fields separated by '|'
  direction|venue|archive_name

Example:
  Conformal handoff for tool-using agents|NeurIPS|Conformal_Handoff
EOF
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            exit 2
            ;;
    esac
done

if ! command -v codex >/dev/null 2>&1 && ! command -v codex.exe >/dev/null 2>&1; then
    echo "Error: codex CLI not found. Install it first: npm install -g @openai/codex" >&2
    exit 1
fi

if command -v codex.exe >/dev/null 2>&1; then
    CODEX_BIN="$(command -v codex.exe)"
else
    CODEX_BIN="$(command -v codex)"
fi

timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

safe_name() {
    local raw="$1"
    local cleaned
    local checksum

    cleaned="$(printf '%s' "$raw" | tr ' /:?*"<>|\\' '_' | tr -s '_' | sed 's/^_//; s/_$//')"
    checksum="$(printf '%s' "$raw" | cksum | awk '{print $1}')"

    if [[ ${#cleaned} -gt 80 ]]; then
        cleaned="${cleaned:0:60}_${checksum}"
    fi

    printf '%s' "$cleaned"
}

parse_task_line() {
    local line="$1"
    local rest

    if [[ "$line" != *"|"* ]]; then
        direction="$line"
        venue=""
        archive_name=""
        return 0
    fi

    archive_name="${line##*|}"
    rest="${line%|*}"

    if [[ "$rest" != *"|"* ]]; then
        direction="$rest"
        venue=""
        return 0
    fi

    venue="${rest##*|}"
    direction="${rest%|*}"
}

LOG_DIR="$PROJECT_ROOT/logx/batch_codex_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"
MASTER_LOG="$LOG_DIR/run.log"

log() {
    echo "[$(timestamp)] $*" | tee -a "$MASTER_LOG"
}

if [[ ! -f "$TASK_FILE" ]]; then
    echo "Error: task file not found: $TASK_FILE" >&2
    exit 1
fi

declare -a TASKS=()
while IFS= read -r raw_line || [[ -n "$raw_line" ]]; do
    line="$(printf '%s' "$raw_line" | sed 's/\r$//')"
    [[ -z "$line" ]] && continue
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    TASKS+=("$line")
done < "$TASK_FILE"

if [[ ${#TASKS[@]} -eq 0 ]]; then
    echo "Error: no tasks found in $TASK_FILE" >&2
    exit 1
fi

log "Task file: $TASK_FILE"
log "Codex binary: $CODEX_BIN"
log "Total tasks: ${#TASKS[@]}"

if $DRY_RUN; then
    for i in "${!TASKS[@]}"; do
        parse_task_line "${TASKS[$i]}"
        echo "[$((i + 1))/${#TASKS[@]}] venue=${venue:-ICML} archive=${archive_name:-run_$((i + 1))}"
        echo "  direction: $direction"
    done
    exit 0
fi

prepare_workspace() {
    local work_dir="$1"
    rm -rf "$work_dir"
    mkdir -p "$work_dir/outputs" "$work_dir/refine-logs"

    for file in CODEX_COMPAT.md README.md CLAUDE.md; do
        if [[ -f "$PROJECT_ROOT/$file" ]]; then
            cp "$PROJECT_ROOT/$file" "$work_dir/"
        fi
    done

    for dir in skills venue-profiles tools docs; do
        if [[ -d "$PROJECT_ROOT/$dir" ]]; then
            cp -r "$PROJECT_ROOT/$dir" "$work_dir/"
        fi
    done
}

archive_result() {
    local work_dir="$1"
    local archive_base="$2"
    local task_log="$3"
    local direction="$4"
    local venue="$5"
    local archive_dir="$PROJECT_ROOT/archive/${archive_base}_$(date +%Y%m%d_%H%M%S)"

    mkdir -p "$archive_dir"

    if [[ -d "$work_dir/outputs" ]]; then
        cp -r "$work_dir/outputs" "$archive_dir/"
    fi
    if [[ -d "$work_dir/refine-logs" ]]; then
        cp -r "$work_dir/refine-logs" "$archive_dir/"
    fi
    if [[ -f "$task_log" ]]; then
        cp "$task_log" "$archive_dir/"
    fi

    cat > "$archive_dir/TASK_META.txt" <<EOF
direction: $direction
venue: $venue
archived_at: $(date -Iseconds)
task_log: $(basename "$task_log")
EOF

    echo "$archive_dir"
}

success_count=0
fail_count=0
declare -a ARCHIVES=()

for i in "${!TASKS[@]}"; do
    parse_task_line "${TASKS[$i]}"

    if [[ -z "${direction:-}" ]]; then
        log "Skipping malformed task line ${i}: missing direction"
        fail_count=$((fail_count + 1))
        continue
    fi

    venue="${venue:-NeurIPS}"
    archive_name="${archive_name:-task_$((i + 1))}"
    safe_archive_name="$(safe_name "$archive_name")"
    work_dir="$LOG_DIR/work_${safe_archive_name}"
    task_log="$LOG_DIR/${safe_archive_name}_pipeline.log"

    log "============================================================"
    log "[$((i + 1))/${#TASKS[@]}] Starting: $archive_name"
    log "Venue: $venue"
    log "Direction: $direction"
    log "Workspace: $work_dir"

    prepare_workspace "$work_dir"
    start_ts=$(date +%s)

    if (
        cd "$work_dir"
        CODEX_BIN="$CODEX_BIN" bash tools/run_codex_skill.sh \
            --skill skills/idea-pipeline/SKILL.md \
            --args "\"${direction}\" -- venue: ${venue}" \
            --role "一个自动化科研 Agent"
    ) >> "$task_log" 2>&1; then
        status="success"
        success_count=$((success_count + 1))
        log "Task finished successfully: $archive_name"
    else
        status="failed"
        fail_count=$((fail_count + 1))
        log "Task failed: $archive_name"
    fi

    duration_min=$(( ( $(date +%s) - start_ts ) / 60 ))
    archive_dir="$(archive_result "$work_dir" "$safe_archive_name" "$task_log" "$direction" "$venue")"
    ARCHIVES+=("$archive_dir")
    log "Duration: ${duration_min} min"
    log "Archived to: $archive_dir"
    log "Status: $status"

    rm -rf "$work_dir"
done

log "============================================================"
log "Batch finished. Success: $success_count, Failed: $fail_count"
for archive_dir in "${ARCHIVES[@]}"; do
    log "Archive: $archive_dir"
done

