#!/bin/bash
# EAR batch runner
# Run the idea discovery pipeline sequentially for multiple research directions
# Archive each completed run automatically before starting the next
#
# Usage:
#   nohup ./batch.sh > batch_run.log 2>&1 &   # Run unattended in the background
#   tail -f batch_run.log                       # Check progress

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
# Define your research directions here (executed in order)
# Format: "direction description|venue|archive name"
# ============================================================
TASKS=(
    "<Enter a research direction: describe the problem, field, and constraints in 1-2 sentences>|ICML|MyRun_01"
    # Example: "sample efficiency of offline RL with image observations|NeurIPS|OfflineRL_01"
    # One direction per line; run the full pipeline sequentially and archive automatically
)

# ============================================================

TOTAL=${#TASKS[@]}
log "${GREEN}EAR batch mode: $TOTAL research directions${NC}"
log ""

for i in "${!TASKS[@]}"; do
    IFS='|' read -r DIRECTION VENUE NAME <<< "${TASKS[$i]}"
    SEQ=$((i + 1))

    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log "${GREEN}[$SEQ/$TOTAL] Starting: $NAME${NC}"
    log "  Direction: $DIRECTION"
    log "  Venue: $VENUE"
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Ensure outputs is clean
    mkdir -p outputs refine-logs

    START_TIME=$(date +%s)
    log "Start time: $(date '+%H:%M:%S')"

    # Core: use a short prompt to have the agent read and execute SKILL.md
    if claude -p "You are the EAR automated research agent. Complete the following tasks:

1. Read skills/idea-pipeline/SKILL.md for your complete workflow instructions
2. Follow the Pipeline workflow in that file strictly
3. Research direction: \"${DIRECTION}\"
4. Target venue: ${VENUE}
5. Use all available tools (WebSearch, Write, Read, Bash, Glob, Grep, etc.)
6. Write all output in English
7. Ask no questions; execute fully autonomously
8. After each Phase, record decisions in outputs/PIPELINE_LOG.md

Read skills/idea-pipeline/SKILL.md now and immediately begin Phase 1." --dangerously-skip-permissions --verbose >> "outputs/pipeline.log" 2>&1; then
        log "${GREEN}✅ [$SEQ/$TOTAL] $NAME complete${NC}"
    else
        log "${RED}⚠️ [$SEQ/$TOTAL] $NAME exited abnormally (exit code: $?)${NC}"
    fi

    END_TIME=$(date +%s)
    DURATION=$(( (END_TIME - START_TIME) / 60 ))
    log "Elapsed time: ${DURATION} minutes"

    # Archive this run
    log "Archive: $NAME"
    ./clean.sh --name "${NAME}" 2>&1 | tee -a "$LOG"

    log ""
done

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "${GREEN}🎉 All $TOTAL research directions are complete!${NC}"
log ""
log "View results:"
ls -d archive/*/ 2>/dev/null | while read dir; do
    log "  📁 $dir"
done
