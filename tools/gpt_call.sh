#!/bin/bash
# tools/gpt_call.sh — OpenAI API curl 封装，兼容 mcp__codex__codex 调用语义
#
# 用法：
#   新 thread:   bash tools/gpt_call.sh --model MODEL --prompt "..." [--output FILE]
#   续 thread:   bash tools/gpt_call.sh --model MODEL --prompt "..." --thread FILE [--output FILE]
#   配置:        bash tools/gpt_call.sh --model MODEL --config '{"model_reasoning_effort":"xhigh"}' --prompt "..."
#
# Thread 语义：
#   --thread FILE 指定一个 JSON 文件路径，存储完整对话历史（messages 数组）。
#   首次调用不传 --thread，脚本自动在 /tmp/ 创建线程文件，并将路径输出到 stderr。
#   续写时传入相同的文件路径，脚本追加消息后再次调用 API。
#   这与 mcp__codex__codex-reply 的 threadId 语义等价。
#
# API Key：
#   优先级：$OPENAI_API_KEY 环境变量 > ~/.openai_key 文件内容
#
# 退出码：0=成功  1=API 错误  2=配置错误
#
# 依赖：curl, python3（用于 JSON 解析）

set -e

# ---------- 参数解析 ----------
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
            echo "未知参数: $1" >&2
            echo "用法: gpt_call.sh --model M --prompt \"...\" [--thread FILE] [--output FILE] [--config JSON]" >&2
            exit 2
            ;;
    esac
done

if [ -z "$PROMPT" ]; then
    echo "错误: --prompt 参数必填" >&2
    exit 2
fi

# ---------- API Key 加载 ----------
API_KEY="${OPENAI_API_KEY:-}"
if [ -z "$API_KEY" ] && [ -f "$HOME/.openai_key" ]; then
    API_KEY=$(cat "$HOME/.openai_key" | tr -d '[:space:]')
fi
if [ -z "$API_KEY" ]; then
    echo "错误: 未找到 OpenAI API Key。请设置 OPENAI_API_KEY 环境变量或将 key 写入 ~/.openai_key" >&2
    exit 2
fi

# ---------- 解析 config 中的 reasoning_effort ----------
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

# ---------- Thread 文件初始化 ----------
NEW_THREAD=false
if [ -z "$THREAD_FILE" ]; then
    THREAD_FILE=$(mktemp /tmp/gpt_thread_XXXXXX.json)
    echo "[]" > "$THREAD_FILE"
    NEW_THREAD=true
fi

if [ ! -f "$THREAD_FILE" ]; then
    echo "[]" > "$THREAD_FILE"
fi

# ---------- 构建消息数组 ----------
# 用 python3 安全地追加 user 消息
UPDATED_MESSAGES=$(python3 << PYEOF
import json, sys

with open("$THREAD_FILE", "r") as f:
    messages = json.load(f)

messages.append({"role": "user", "content": """$PROMPT"""})

print(json.dumps(messages))
PYEOF
)

# ---------- 构建 API 请求 body ----------
REQUEST_BODY=$(python3 << PYEOF
import json

messages = $UPDATED_MESSAGES
body = {
    "model": "$MODEL",
    "messages": messages,
    "max_completion_tokens": 16384
}

# 若 reasoning_effort 非空且模型支持（o1/o3/o4 系列），追加参数
effort = "$REASONING_EFFORT"
if effort and any(m in "$MODEL" for m in ["o1", "o3", "o4"]):
    body["reasoning_effort"] = effort

print(json.dumps(body))
PYEOF
)

# ---------- 调用 OpenAI API ----------
_T0=$(date +%s)
_RESP_TMP=$(mktemp /tmp/gpt_resp_XXXXXX.json)
curl -s -X POST "https://api.openai.com/v1/chat/completions" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d "$REQUEST_BODY" -o "$_RESP_TMP"
_T1=$(date +%s)
RESPONSE=$(cat "$_RESP_TMP")

# ---------- 解析响应 ----------
ASSISTANT_CONTENT=$(python3 << PYEOF
import json, sys

resp = json.loads("""$RESPONSE""")

if "error" in resp:
    print(f"API 错误: {resp['error']['message']}", file=sys.stderr)
    sys.exit(1)

content = resp["choices"][0]["message"]["content"]
print(content)
PYEOF
)

# ---------- 记录成本（token 用量仅在本脚本路径可得；Codex MCP 路径拿不到）----------
python3 - "$_RESP_TMP" "$PHASE" "$MODEL" "$((_T1 - _T0))" "$COST_LOG" <<'PYEOF'
import json, sys, os
from datetime import datetime, timezone

resp_path, phase, model, elapsed, log_path = sys.argv[1:6]
try:
    with open(resp_path, encoding="utf-8") as f:
        resp = json.load(f)
except Exception:
    sys.exit(0)          # 响应不可解析时不阻断主流程
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

# ---------- 更新 Thread 文件（追加 assistant 消息）----------
python3 << PYEOF
import json

with open("$THREAD_FILE", "r") as f:
    messages = json.load(f)

# 先追加 user 消息（与上面保持一致）
already_user = any(m["role"] == "user" and m["content"].startswith("${PROMPT:0:30}") for m in messages[-2:])
if not already_user:
    messages.append({"role": "user", "content": """$PROMPT"""})

messages.append({"role": "assistant", "content": """$ASSISTANT_CONTENT"""})

with open("$THREAD_FILE", "w") as f:
    json.dump(messages, f, ensure_ascii=False, indent=2)
PYEOF

# ---------- 输出结果 ----------
if [ -n "$OUTPUT_FILE" ]; then
    echo "$ASSISTANT_CONTENT" > "$OUTPUT_FILE"
else
    echo "$ASSISTANT_CONTENT"
fi

# 如果是新 thread，把 thread 文件路径输出到 stderr，方便调用方捕获
if [ "$NEW_THREAD" = "true" ]; then
    echo "THREAD_FILE: $THREAD_FILE" >&2
fi
