#!/bin/bash
# tools/gpt_call.sh — OpenAI API curl wrapper compatible with mcp__codex__codex call semantics
#
# Usage:
#   New thread:   bash tools/gpt_call.sh --model MODEL --prompt "..." [--output FILE]
#   Resume thread:   bash tools/gpt_call.sh --model MODEL --prompt "..." --thread FILE [--output FILE]
#   Configuration:        bash tools/gpt_call.sh --model MODEL --config '{"model_reasoning_effort":"xhigh"}' --prompt "..."
#
# Thread semantics:
#   --thread FILE specifies a JSON file containing the complete conversation history (messages array).
#   On the first call, omit --thread; the script creates a thread file in /tmp/ and prints its path to stderr.
#   To continue, pass the same path; the script appends messages and calls the API again.
#   This is equivalent to the threadId semantics of mcp__codex__codex-reply.
#
# API Key：
#   Precedence: $OPENAI_API_KEY environment variable > contents of ~/.openai_key
#
# Exit codes: 0=success  1=API error  2=configuration error
#
# Dependencies: curl, python3 (for JSON parsing)

set -e

# ---------- Argument parsing ----------
MODEL="gpt-4o"
PROMPT=""
THREAD_FILE=""
OUTPUT_FILE=""
PHASE="${PHASE:-unknown}"
COST_LOG="${COST_LOG:-outputs/COST_LOG.jsonl}"
CONFIG="{}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --model)    MODEL="$2";       shift 2 ;;
        --prompt)   PROMPT="$2";      shift 2 ;;
        --thread)   THREAD_FILE="$2"; shift 2 ;;
        --phase)    PHASE="$2"; shift 2 ;;
        --output)   OUTPUT_FILE="$2"; shift 2 ;;
        --config)   CONFIG="$2";      shift 2 ;;
        *)
            echo "Unknown argument: $1" >&2
            echo "Usage: gpt_call.sh --model M --prompt \"...\" [--thread FILE] [--output FILE] [--config JSON]" >&2
            exit 2
            ;;
    esac
done

if [ -z "$PROMPT" ]; then
    echo "Error: --prompt is required" >&2
    exit 2
fi

# ---------- Load API key ----------
API_KEY="${OPENAI_API_KEY:-}"
if [ -z "$API_KEY" ] && [ -f "$HOME/.openai_key" ]; then
    API_KEY=$(cat "$HOME/.openai_key" | tr -d '[:space:]')
fi
if [ -z "$API_KEY" ]; then
    echo "Error: OpenAI API key not found. Set OPENAI_API_KEY or save the key in ~/.openai_key" >&2
    exit 2
fi

# ---------- Parse reasoning_effort from config ----------
REASONING_EFFORT=$(python3 -c "
import json, sys
try:
    cfg = json.loads('''$CONFIG''')
    effort = cfg.get('model_reasoning_effort', '')
    if effort:
        print(effort)
except:
    pass
" 2>/dev/null || true)

# ---------- Initialize thread file ----------
NEW_THREAD=false
if [ -z "$THREAD_FILE" ]; then
    THREAD_FILE=$(mktemp /tmp/gpt_thread_XXXXXX.json)
    echo "[]" > "$THREAD_FILE"
    NEW_THREAD=true
fi

if [ ! -f "$THREAD_FILE" ]; then
    echo "[]" > "$THREAD_FILE"
fi

# ---------- Build message array ----------
# Append the user message safely with python3
UPDATED_MESSAGES=$(python3 << PYEOF
import json, sys

with open("$THREAD_FILE", "r") as f:
    messages = json.load(f)

messages.append({"role": "user", "content": """$PROMPT"""})

print(json.dumps(messages))
PYEOF
)

# ---------- Build API request body ----------
REQUEST_BODY=$(python3 << PYEOF
import json

messages = $UPDATED_MESSAGES
body = {
    "model": "$MODEL",
    "messages": messages,
    "max_completion_tokens": 16384
}

# If reasoning_effort is nonempty and supported by the model (o1/o3/o4 families), append it
effort = "$REASONING_EFFORT"
if effort and any(m in "$MODEL" for m in ["o1", "o3", "o4"]):
    body["reasoning_effort"] = effort

print(json.dumps(body))
PYEOF
)

# ---------- Call OpenAI API ----------
_T0=$(date +%s)
_RESP_TMP=$(mktemp /tmp/gpt_resp_XXXXXX.json)
curl -s -X POST "https://api.openai.com/v1/chat/completions" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d "$REQUEST_BODY" -o "$_RESP_TMP"
_T1=$(date +%s)
RESPONSE=$(cat "$_RESP_TMP")

# ---------- Parse response ----------
ASSISTANT_CONTENT=$(python3 << PYEOF
import json, sys

resp = json.loads("""$RESPONSE""")

if "error" in resp:
    print(f"API error: {resp['error']['message']}", file=sys.stderr)
    sys.exit(1)

content = resp["choices"][0]["message"]["content"]
print(content)
PYEOF
)

# ---------- Record cost (token usage is available only through this script, not through Codex MCP)----------
python3 - "$_RESP_TMP" "$PHASE" "$MODEL" "$((_T1 - _T0))" "$COST_LOG" <<'PYEOF'
import json, sys, os
from datetime import datetime, timezone

resp_path, phase, model, elapsed, log_path = sys.argv[1:6]
try:
    with open(resp_path, encoding="utf-8") as f:
        resp = json.load(f)
except Exception:
    sys.exit(0)          # Do not block the main workflow when the response cannot be parsed
usage = resp.get("usage") or {}
record = {
    "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "phase": phase,
    "model": model,
    "tokens_in": usage.get("prompt_tokens"),
    "tokens_out": usage.get("completion_tokens"),
    "tokens_total": usage.get("total_tokens"),
    "reasoning_tokens": (usage.get("completion_tokens_details") or {}).get("reasoning_tokens"),
    "wall_clock_s": int(elapsed),
    "source": "gpt_call.sh",
}
os.makedirs(os.path.dirname(log_path) or ".", exist_ok=True)
with open(log_path, "a", encoding="utf-8") as f:
    f.write(json.dumps(record, ensure_ascii=False) + "\n")
PYEOF
rm -f "$_RESP_TMP"

# ---------- Update thread file (append assistant message)----------
python3 << PYEOF
import json

with open("$THREAD_FILE", "r") as f:
    messages = json.load(f)

# Append the user message first (consistent with the above)
already_user = any(m["role"] == "user" and m["content"].startswith("${PROMPT:0:30}") for m in messages[-2:])
if not already_user:
    messages.append({"role": "user", "content": """$PROMPT"""})

messages.append({"role": "assistant", "content": """$ASSISTANT_CONTENT"""})

with open("$THREAD_FILE", "w") as f:
    json.dump(messages, f, ensure_ascii=False, indent=2)
PYEOF

# ---------- Output results ----------
if [ -n "$OUTPUT_FILE" ]; then
    echo "$ASSISTANT_CONTENT" > "$OUTPUT_FILE"
else
    echo "$ASSISTANT_CONTENT"
fi

# For a new thread, print its file path to stderr so the caller can capture it
if [ "$NEW_THREAD" = "true" ]; then
    echo "THREAD_FILE: $THREAD_FILE" >&2
fi
