#!/usr/bin/env bash
# tools/codex_call.sh — 用本机 codex CLI 充当外部模型，接口与 tools/gpt_call.sh 一致。
#
# 为什么需要它：codex CLI 自 0.158.0 起**已移除 `mcp-server` 子命令**，
# 旧文档里的 `claude mcp add codex -s user -- codex mcp-server` 不再可用。
# `codex exec` 是等价替代：非交互、用 codex 自身的登录态、支持 resume 续会话。
#
# 用法:
#   bash tools/codex_call.sh --prompt "..." --output /tmp/r.txt [--thread /tmp/t.id]
#                            [--model <仅当该模型对当前账号可用>] [--phase idea-gen/2a]
#                            [--config '{"model_reasoning_effort":"xhigh"}']
#
# thread 语义：--thread 指向一个保存 thread_id 的文件。
#   文件不存在或为空 → 新建会话（等价 mcp__codex__codex），并把 thread_id 写入该文件
#   文件已有 id      → resume 续写（等价 mcp__codex__codex-reply）
#
# 成本：每次调用把 usage 追加到 $COST_LOG（默认 outputs/COST_LOG.jsonl）。
# 退出码：0=成功  1=调用失败  2=配置错误

set -uo pipefail

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
        *) echo "未知参数: $1" >&2; exit 2 ;;
    esac
done

[[ -z "$PROMPT" ]] && { echo "错误: 缺少 --prompt" >&2; exit 2; }
command -v codex >/dev/null 2>&1 || {
    echo "错误: 未找到 codex CLI。安装: npm install -g @openai/codex@latest" >&2; exit 2; }

# reasoning effort 从 config JSON 取，映射为 codex 的 -c 覆盖项
EFFORT=$(python3 -c "
import json,sys
try: print(json.loads('''$CONFIG''').get('model_reasoning_effort',''))
except Exception: print('')
" 2>/dev/null)

ARGS=(exec --skip-git-repo-check --json)
[[ -n "$MODEL"  ]] && ARGS+=(--model "$MODEL")
[[ -n "$EFFORT" ]] && ARGS+=(-c "model_reasoning_effort=\"$EFFORT\"")

# 续会话 or 新建
RESUME_ID=""
if [[ -n "$THREAD_FILE" && -s "$THREAD_FILE" ]]; then
    RESUME_ID=$(tr -d '[:space:]' < "$THREAD_FILE")
fi
if [[ -n "$RESUME_ID" ]]; then
    ARGS=(exec resume "$RESUME_ID" --skip-git-repo-check --json)
    [[ -n "$MODEL"  ]] && ARGS+=(--model "$MODEL")
    [[ -n "$EFFORT" ]] && ARGS+=(-c "model_reasoning_effort=\"$EFFORT\"")
fi

LAST_MSG=$(mktemp /tmp/codex_last_XXXXXX.txt)
EVENTS=$(mktemp /tmp/codex_events_XXXXXX.jsonl)
ARGS+=(-o "$LAST_MSG")

_T0=$(date +%s)
# stdin 必须给 /dev/null：非 TTY 时 codex 会阻塞等待额外输入
codex "${ARGS[@]}" "$PROMPT" </dev/null >"$EVENTS" 2>/tmp/codex_err.txt
RC=$?
_T1=$(date +%s)

# codex 把**错误也写进 stdout 的 JSON 事件流**（不是 stderr），
# stderr 里常见的 "Reading additional input from stdin..." 是无害噪声，成功调用同样会出现。
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
    echo "codex 调用失败（退出码 $RC）" >&2
    [[ -n "$ERRMSG" ]] && echo "  原因: $ERRMSG" >&2
    if [[ "$ERRMSG" == *"not supported when using Codex with a ChatGPT account"* ]]; then
        echo "  提示: 用 ChatGPT 账号登录的 codex 只能用该账号自带的模型。" >&2
        echo "        去掉 --model 即可使用默认模型（codex exec 启动时会打印 model: ...）。" >&2
    fi
    grep -v "Reading additional input from stdin" /tmp/codex_err.txt 2>/dev/null | head -3 >&2
    rm -f "$LAST_MSG" "$EVENTS"
    exit 1
fi

# thread_id 落盘（新建会话时）
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

# 成本记录
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
