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
#   ./run.sh --stop                      # Stop the background process tree

set -euo pipefail
umask 077
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
    elif [ "$arg" = "--unsafe" ]; then
        export EAR_UNSAFE=1
    elif [ "$arg" = "--allow-network" ]; then
        export EAR_ALLOW_NETWORK=1
    else
        FILTERED_ARGS+=("$arg")
    fi
done
set -- "${FILTERED_ARGS[@]}"
if $GPT_ONLY && $CODEX_CLI_MODE; then
    echo "Choose either --gpt-only or --codex-cli, not both." >&2
    exit 2
fi
MODE="${1:---interactive}"
case "$MODE" in
    --survey|--gen|--screen|--refine|--daemon)
        [[ -n "${2:-}" ]] || { echo "Error: $MODE requires a direction or idea." >&2; exit 2; } ;;
    --interactive|-i|--status|--stop|--help|-h) ;;
    --*) echo "Unknown option: $MODE (use --help)" >&2; exit 2 ;;
esac
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
if [[ "$MODE" != --help && "$MODE" != -h && "$MODE" != --status && "$MODE" != --stop ]] && ! command -v codex &> /dev/null && ! command -v codex.exe &> /dev/null; then
    echo "Error: codex command not found. Install Codex CLI first:"
    echo "  npm install -g @openai/codex"
    exit 1
fi

if command -v codex.exe &> /dev/null; then
    CODEX_CMD="$(command -v codex.exe)"
else
    CODEX_CMD="$(command -v codex || true)"
fi

# Ensure the outputs directory exists
if [[ "$MODE" != --help && "$MODE" != -h && "$MODE" != --status && "$MODE" != --stop ]]; then
    mkdir -p outputs refine-logs
fi

# Helper: execute a skill with Codex
run_skill() {
    local SKILL_FILE="$1"
    local ARGS="$2"
    bash tools/run_codex_skill.sh \
        --skill "$SKILL_FILE" \
        --args "$ARGS" \
        --role "an automated research agent"
}

DIRECTION="${1:-}"
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
        source tools/execution_policy.sh
        ear_execution_policy
        ear_data_notice
        "$CODEX_CMD" "${CODEX_SECURITY_ARGS[@]}" "Read CODEX_COMPAT.md and README.md in the current workspace, then help operate this EAR repository in Codex-only mode."
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
        command -v flock >/dev/null || { echo "Install flock (util-linux) for background mode." >&2; exit 2; }
        exec 9>outputs/.pipeline.lock
        flock -n 9 || { echo "A background pipeline already holds outputs/.pipeline.lock" >&2; exit 1; }
        # Clear only previous status markers after obtaining the per-workspace lock.
        rm -f outputs/DONE outputs/FAILED outputs/pipeline.pid outputs/pipeline.run.json
        nohup bash tools/run_background.sh "$DIRECTION" "$VENUE" > outputs/launcher.log 2>&1 &
        BGPID=$!
        echo "Background process PID: $BGPID"
        echo $BGPID > outputs/pipeline.pid
        echo -e "${GREEN}Pipeline started in the background.${NC}"
        echo "  Check progress: ./run.sh --status"
        echo "  View logs: tail -f outputs/pipeline.log"
        echo "  Stop: ./run.sh --stop"
        ;;
    --stop)
        exec python3 tools/background_runner.py stop
        ;;
    --status)
        STATUS_RC=0
        echo -e "${GREEN}EAR status${NC}"
        echo ""
        if [ -f outputs/FAILED ]; then
            STATUS_RC=1
            echo "Pipeline failed (exit code below); see outputs/pipeline.log and outputs/launcher.log"
            cat outputs/FAILED
        elif [ -f outputs/DONE ]; then
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
        exit "$STATUS_RC"
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
        echo "  ./run.sh --stop                         Stop the background task and its descendants"
        echo ""
        echo "Options:"
        echo "  --gpt-only                              GPT-only mode (affects only the fallback policy for additional reasoning within skills)"
        echo "  --codex-cli                             Use local Codex CLI as the external model (no API key required)"
        echo "  --allow-network                         Allow shell network access and live web search (opt-in)"
        echo "  --unsafe                                Disable sandboxing (explicit opt-in; isolated hosts only)"
        echo "  Default: workspace-write sandbox, no approvals, shell network disabled."
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
