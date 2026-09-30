#!/bin/bash
# EAR quick-start script (Codex edition)
# Usage:
#   ./run.sh                           # interactive mode
#   ./run.sh "research direction"                  # full pipeline
#   ./run.sh "research direction" VLDB             # specified venue
#   ./run.sh --survey "research direction"         # literature survey only
#   ./run.sh --gen "research direction"            # idea generation only
#   ./run.sh --screen "idea description" ICML    # screening only
#   ./run.sh --refine "idea description"         # refinement only
#   ./run.sh --daemon "research direction" VLDB    # run in the background (nohup)
#   ./run.sh --status                    # Check run status

set -e
cd "$(dirname "$0")"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Parse the --gpt-only flag (allowed anywhere)
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
    echo -e "${YELLOW}Codex CLI mode enabled (CODEX_MODE=codex-cli)${NC}"
    echo "  External model calls use tools/codex_call.sh (local Codex login; no API key required)"
    echo ""
fi

if [ "$GPT_ONLY" = "true" ]; then
    echo -e "${YELLOW}GPT-only mode enabled (CODEX_MODE=gpt-api)${NC}"
    echo "  Skills first try tools/gpt_call.sh when an additional reasoning pass is needed"
    echo ""
fi

# Check Codex CLI
if ! command -v codex &> /dev/null && ! command -v codex.exe &> /dev/null; then
    echo "Error: codex command not found. Install Codex CLI first:"
    echo "  npm install -g @openai/codex"
    exit 1
fi

if command -v codex.exe &> /dev/null; then
    CODEX_CMD="$(command -v codex.exe)"
else
    CODEX_CMD="$(command -v codex)"
fi

# Ensure the outputs directory exists
mkdir -p outputs refine-logs

# Helper: execute a skill with Codex
run_skill() {
    local SKILL_FILE="$1"
    local ARGS="$2"
    bash tools/run_codex_skill.sh \
        --skill "$SKILL_FILE" \
        --args "$ARGS" \
        --role "an automated research agent"
}

MODE="${1:---interactive}"
DIRECTION="$1"
VENUE="${2:-ICML}"

case "$MODE" in
    --interactive|-i)
        echo -e "${GREEN}EAR Codex interactive mode${NC}"
        echo "Recommended shell entry points:"
        echo "  ./run.sh \"research direction\" ICML                     full pipeline"
        echo "  ./run.sh --survey \"research direction\"                  literature survey"
        echo "  ./run.sh --gen \"research direction\"                     idea generation"
        echo "  ./run.sh --screen \"idea\" VLDB                multidimensional screening"
        echo "  ./run.sh --refine \"idea\"                      in-depth refinement"
        echo ""
        "$CODEX_CMD" --search "Read CODEX_COMPAT.md and README.md in the current workspace, then help operate this EAR repository in Codex-only mode."
        ;;
    --survey)
        echo -e "${GREEN}Running literature survey: $2${NC}"
        run_skill "skills/lit-survey/SKILL.md" "$2"
        ;;
    --gen)
        echo -e "${GREEN}Running idea generation: $2${NC}"
        run_skill "skills/idea-gen/SKILL.md" "$2"
        ;;
    --screen)
        echo -e "${GREEN}Running multidimensional screening (venue: ${3:-ICML}): $2${NC}"
        run_skill "skills/idea-screen/SKILL.md" "$2 -- venue: ${3:-ICML}"
        ;;
    --refine)
        echo -e "${GREEN}Running in-depth refinement: $2${NC}"
        run_skill "skills/idea-refine/SKILL.md" "$2"
        ;;
    --daemon)
        DIRECTION="$2"
        VENUE="${3:-ICML}"
        echo -e "${GREEN}EAR background mode${NC}"
        echo -e "Direction: $DIRECTION"
        echo -e "Venue: $VENUE"
        echo "Log: outputs/pipeline.log"
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
  --role "an automated research agent" \
  2>&1 | tee outputs/pipeline.log
date -Iseconds > outputs/DONE
RUNEOF_BODY
        chmod +x outputs/.run_pipeline.sh
        nohup bash outputs/.run_pipeline.sh > /dev/null 2>&1 &
        BGPID=$!
        echo "Background process PID: $BGPID"
        echo $BGPID > outputs/pipeline.pid
        echo -e "${GREEN}Pipeline started in the background.${NC}"
        echo "  Check progress: ./run.sh --status"
        echo "  View logs: tail -f outputs/pipeline.log"
        echo "  Stop: kill \$(cat outputs/pipeline.pid)"
        ;;
    --status)
        echo -e "${GREEN}EAR status${NC}"
        echo ""
        if [ -f outputs/DONE ]; then
            echo -e "${GREEN}✅ Pipeline complete${NC}"
            cat outputs/DONE
        elif [ -f outputs/pipeline.pid ] && kill -0 "$(cat outputs/pipeline.pid)" 2>/dev/null; then
            echo "🔄 Pipeline running (PID: $(cat outputs/pipeline.pid))"
        else
            echo "⏹ Pipeline not running"
        fi
        echo ""
        if [ -f outputs/PIPELINE_STATE.json ]; then
            echo "State file:"
            cat outputs/PIPELINE_STATE.json
        fi
        echo ""
        if [ -f outputs/PIPELINE_LOG.md ]; then
            echo "Latest log entries:"
            tail -20 outputs/PIPELINE_LOG.md
        fi
        ;;
    --help|-h)
        echo "EAR - automated AI research idea discovery workflow"
        echo ""
        echo "Usage:"
        echo "  ./run.sh                              interactive mode"
        echo "  ./run.sh \"research direction\"                    full pipeline (default ICML)"
        echo "  ./run.sh \"research direction\" VLDB               full pipeline (specified venue)"
        echo "  ./run.sh --survey \"research direction\"            literature survey only"
        echo "  ./run.sh --gen \"research direction\"               idea generation only"
        echo "  ./run.sh --screen \"idea\" ICML          screening only"
        echo "  ./run.sh --refine \"idea\"               refinement only"
        echo "  ./run.sh --daemon \"research direction\" VLDB      run in the background (nohup)"
        echo "  ./run.sh --status                       Check run status"
        echo ""
        echo "Options:"
        echo "  --gpt-only                              GPT-only mode (affects only the fallback policy for additional reasoning within skills)"
        echo "  --codex-cli                             Use local Codex CLI as the external model (no API key required)"
        echo "  Append -- mode: socratic to --refine for Socratic dialogue refinement"
        echo "  Append -- mode: socratic-human to --refine for human-in-the-loop Socratic refinement"
        echo ""
        echo "Supported venues: ICML, VLDB, NeurIPS, SIGMOD"
        echo "Output directories: outputs/, refine-logs/"
        ;;
    *)
        # Default: if the first argument is not a flag, treat it as a direction and run the full pipeline
        echo -e "${GREEN}EAR full pipeline${NC}"
        echo -e "Direction: $DIRECTION"
        echo -e "Venue: $VENUE"
        echo ""
        run_skill "skills/idea-pipeline/SKILL.md" "\"$DIRECTION\" -- venue: $VENUE"
        ;;
esac
