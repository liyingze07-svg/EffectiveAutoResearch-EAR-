#!/usr/bin/env bash
# tools/codex_call.sh — Use local Codex CLI as the external model, with the same interface as tools/gpt_call.sh.
#
# Uses codex exec without requiring an MCP host: noninteractive, authenticated, resumable.
#
# Usage:
#   bash tools/codex_call.sh --prompt "..." --output /tmp/r.txt [--thread /tmp/t.id]
#                            [--model <only if the model is available to this account>] [--phase idea-gen/2a]
#                            [--config '{"model_reasoning_effort":"xhigh"}']
#
# Thread semantics: --thread points to a file storing thread_id.
#   Missing or empty file -> create a session (equivalent to mcp__codex__codex) and save thread_id there
#   File already contains an id -> resume the session (equivalent to mcp__codex__codex-reply)
#
# Cost: append usage from each call to $COST_LOG (default: outputs/COST_LOG.jsonl).
# Exit codes: 0=success  1=call failure  2=configuration error

set -uo pipefail
umask 077

MODEL=""
PROMPT=""
THREAD_FILE=""
OUTPUT_FILE=""
PHASE="${PHASE:-unknown}"
CONFIG="{}"
COST_LOG="${COST_LOG:-outputs/COST_LOG.jsonl}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --model)   MODEL="$2";       shift 2 ;;
        --prompt)  PROMPT="$2";      shift 2 ;;
        --thread)  THREAD_FILE="$2"; shift 2 ;;
        --output)  OUTPUT_FILE="$2"; shift 2 ;;
        --phase)   PHASE="$2";       shift 2 ;;
        --config)  CONFIG="$2";      shift 2 ;;
        *) echo "Unknown argument: $1" >&2; exit 2 ;;
    esac
done

[[ -z "$PROMPT" ]] && { echo "Error: missing --prompt" >&2; exit 2; }
command -v codex >/dev/null 2>&1 || {
    echo "Error: codex CLI not found. Install: npm install -g @openai/codex@latest" >&2; exit 2; }

# Read reasoning effort from config JSON and map it to a Codex -c override
EFFORT=$(python3 -c '
import json,sys
try: print(json.loads(sys.argv[1]).get("model_reasoning_effort", ""))
except Exception: sys.exit(2)
' "$CONFIG") || { echo "Invalid --config JSON" >&2; exit 2; }

ARGS=(exec --skip-git-repo-check --json)
[[ -n "$MODEL"  ]] && ARGS+=(--model "$MODEL")
[[ -n "$EFFORT" ]] && ARGS+=(-c "model_reasoning_effort=\"$EFFORT\"")

# Resume or create a session
RESUME_ID=""
if [[ -n "$THREAD_FILE" && -s "$THREAD_FILE" ]]; then
    RESUME_ID=$(tr -d '[:space:]' < "$THREAD_FILE")
fi
if [[ -n "$RESUME_ID" ]]; then
    ARGS=(exec resume "$RESUME_ID" --skip-git-repo-check --json)
    [[ -n "$MODEL"  ]] && ARGS+=(--model "$MODEL")
    [[ -n "$EFFORT" ]] && ARGS+=(-c "model_reasoning_effort=\"$EFFORT\"")
fi

ARGS+=(-c 'sandbox_mode="read-only"' -c 'approval_policy="never"' -c 'web_search="disabled"')
LAST_MSG=$(mktemp /tmp/codex_last_XXXXXX.txt)
EVENTS=$(mktemp /tmp/codex_events_XXXXXX.jsonl)
ERRORS=$(mktemp /tmp/codex_err_XXXXXX.txt)
trap 'rm -f "$LAST_MSG" "$EVENTS" "$ERRORS"' EXIT
ARGS+=(-o "$LAST_MSG")

_T0=$(date +%s)
echo "DATA NOTICE: this prompt/history is sent through Codex; CLI session files may retain it." >&2
# stdin must be /dev/null: without a TTY, Codex blocks waiting for additional input
codex "${ARGS[@]}" "$PROMPT" </dev/null >"$EVENTS" 2>"$ERRORS"
RC=$?
_T1=$(date +%s)

# Codex writes **errors to the JSON event stream on stdout as well** (not stderr);
# the common stderr message "Reading additional input from stdin..." is harmless and also appears on successful calls.
ERRMSG=$(python3 -c "
import json,sys
msgs=[]
try:
    for line in open('$EVENTS', encoding='utf-8'):
        try: d=json.loads(line)
        except Exception: continue
        if d.get('type') in ('error','turn.failed'):
            m=d.get('message') or (d.get('error') or {}).get('message') or ''
            try:
                inner=json.loads(m)
                m=(inner.get('error') or {}).get('message') or m
            except Exception: pass
            if m: msgs.append(m)
        item=d.get('item') or {}
        if item.get('type')=='error' and item.get('message'):
            msgs.append(item['message'])
except Exception: pass
seen=[]
for m in msgs:
    if m not in seen: seen.append(m)
print(' | '.join(seen[:3]))
" 2>/dev/null)

if [[ $RC -ne 0 || -n "$ERRMSG" ]]; then
    echo "codex call failed (exit code $RC)" >&2
    [[ -n "$ERRMSG" ]] && echo "  Reason: $ERRMSG" >&2
    if [[ "$ERRMSG" == *"not supported when using Codex with a ChatGPT account"* ]]; then
        echo "  Tip: Codex authenticated with ChatGPT can only use models available to that account." >&2
        echo "        Omit --model to use the default model (codex exec prints model: ... at startup)." >&2
    fi
    grep -v "Reading additional input from stdin" "$ERRORS" 2>/dev/null | head -3 >&2
    rm -f "$LAST_MSG" "$EVENTS"
    exit 1
fi

# Save thread_id (when creating a session)
if [[ -n "$THREAD_FILE" && -z "$RESUME_ID" ]]; then
    TID=$(python3 -c "
import json,sys
for line in open('$EVENTS', encoding='utf-8'):
    try: d = json.loads(line)
    except Exception: continue
    if d.get('type') == 'thread.started' and d.get('thread_id'):
        print(d['thread_id']); break
" 2>/dev/null)
    if [[ -n "$TID" ]]; then
        printf '%s' "$TID" > "$THREAD_FILE"
        echo "THREAD_FILE: $THREAD_FILE" >&2
        echo "THREAD_ID: $TID" >&2
    fi
fi

# Record cost
python3 - "$EVENTS" "$PHASE" "${MODEL:-codex-default}" "$((_T1 - _T0))" "$COST_LOG" <<'PYEOF'
import json, os, sys
from datetime import datetime, timezone

events, phase, model, elapsed, log_path = sys.argv[1:6]
usage = {}
for line in open(events, encoding="utf-8"):
    try: d = json.loads(line)
    except Exception: continue
    if d.get("type") == "turn.completed" and isinstance(d.get("usage"), dict):
        usage = d["usage"]
if not usage:
    sys.exit(0)
rec = {
    "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "phase": phase, "model": model,
    "tokens_in": usage.get("input_tokens"),
    "tokens_out": usage.get("output_tokens"),
    "tokens_total": (usage.get("input_tokens") or 0) + (usage.get("output_tokens") or 0),
    "cached_input_tokens": usage.get("cached_input_tokens"),
    "reasoning_tokens": usage.get("reasoning_output_tokens"),
    "wall_clock_s": int(elapsed),
    "source": "codex_call.sh",
}
os.makedirs(os.path.dirname(log_path) or ".", exist_ok=True)
with open(log_path, "a", encoding="utf-8") as f:
    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
PYEOF

CONTENT=$(cat "$LAST_MSG")
[[ -n "$OUTPUT_FILE" ]] && printf '%s' "$CONTENT" > "$OUTPUT_FILE"
printf '%s\n' "$CONTENT"
rm -f "$LAST_MSG" "$EVENTS"
exit 0
