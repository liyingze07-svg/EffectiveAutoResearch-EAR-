#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

SKILL_FILE=""
SKILL_ARGS=""
SYSTEM_ROLE="an automated research agent"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --skill)
            SKILL_FILE="$2"
            shift 2
            ;;
        --args)
            SKILL_ARGS="$2"
            shift 2
            ;;
        --role)
            SYSTEM_ROLE="$2"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1" >&2
            echo "Usage: tools/run_codex_skill.sh --skill skills/foo/SKILL.md --args \"...\" [--role \"...\"]" >&2
            exit 2
            ;;
    esac
done

if [[ -z "$SKILL_FILE" ]]; then
    echo "Error: --skill is required" >&2
    exit 2
fi

if [[ ! -f "$SKILL_FILE" ]]; then
    echo "Error: skill file not found: $SKILL_FILE" >&2
    exit 2
fi

CODEX_BIN="${CODEX_BIN:-}"
if [[ -z "$CODEX_BIN" ]]; then
    if command -v codex.exe >/dev/null 2>&1; then
        CODEX_BIN="$(command -v codex.exe)"
    elif command -v codex >/dev/null 2>&1; then
        CODEX_BIN="$(command -v codex)"
    else
        echo "Error: codex command not found. Install Codex CLI first." >&2
        exit 1
    fi
fi

COMPAT_CONTENT="$(cat CODEX_COMPAT.md)"
SKILL_CONTENT="$(sed '1{/^---$/,/^---$/d}' "$SKILL_FILE")"

PROMPT=$(cat <<EOF
You are ${SYSTEM_ROLE}. Follow the workflow below strictly; begin executing it rather than only describing a plan.

## Codex Runtime Compatibility
${COMPAT_CONTENT}

## Workflow Instructions
${SKILL_CONTENT}

## Execution Parameters
${SKILL_ARGS}

Begin now: read and understand the workflow above, then execute it immediately.
EOF
)

# Model selection: **omit** -m by default and use the default model available to the Codex account.
# This previously hard-coded `-m gpt-5.4`, but Codex authenticated with ChatGPT rejected it with HTTP 400:
#   "The 'gpt-5.4' model is not supported when using Codex with a ChatGPT account."
# Override with CODEX_MODEL=... when needed (only if the model is available to this account).
CODEX_ARGS=(exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox)
if [[ -n "${CODEX_MODEL:-}" ]]; then
    CODEX_ARGS+=(-m "$CODEX_MODEL")
fi

# Pass the prompt as a positional argument and connect stdin to /dev/null:
# Without a TTY, codex exec prints "Reading additional input from stdin..." and waits if stdin remains open.
exec "$CODEX_BIN" "${CODEX_ARGS[@]}" "$PROMPT" </dev/null
