#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

SKILL_FILE=""
SKILL_ARGS=""
SYSTEM_ROLE="一个自动化科研 Agent"

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
            echo "未知参数: $1" >&2
            echo "用法: tools/run_codex_skill.sh --skill skills/foo/SKILL.md --args \"...\" [--role \"...\"]" >&2
            exit 2
            ;;
    esac
done

if [[ -z "$SKILL_FILE" ]]; then
    echo "错误: --skill 参数必填" >&2
    exit 2
fi

if [[ ! -f "$SKILL_FILE" ]]; then
    echo "错误: 找不到 skill 文件: $SKILL_FILE" >&2
    exit 2
fi

CODEX_BIN="${CODEX_BIN:-}"
if [[ -z "$CODEX_BIN" ]]; then
    if command -v codex.exe >/dev/null 2>&1; then
        CODEX_BIN="$(command -v codex.exe)"
    elif command -v codex >/dev/null 2>&1; then
        CODEX_BIN="$(command -v codex)"
    else
        echo "错误: 未找到 codex 命令。请先安装 Codex CLI。" >&2
        exit 1
    fi
fi

COMPAT_CONTENT="$(cat CODEX_COMPAT.md)"
SKILL_CONTENT="$(sed '1{/^---$/,/^---$/d}' "$SKILL_FILE")"

PROMPT=$(cat <<EOF
你是${SYSTEM_ROLE}。请严格按照下列工作流执行，不要只描述计划，直接开始实际操作。

## Codex Runtime Compatibility
${COMPAT_CONTENT}

## Workflow Instructions
${SKILL_CONTENT}

## Execution Parameters
${SKILL_ARGS}

现在开始：先阅读并理解上面的工作流，再立即执行。
EOF
)

# 模型选择：默认**不传** -m，使用 codex 账号自带的默认模型。
# 曾经这里硬编码 `-m gpt-5.4`，但用 ChatGPT 账号登录的 codex 会以 400 拒绝：
#   "The 'gpt-5.4' model is not supported when using Codex with a ChatGPT account."
# 需要指定模型时用 CODEX_MODEL=... 覆盖（仅在该模型对当前账号可用时才设）。
CODEX_ARGS=(exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox)
if [[ -n "${CODEX_MODEL:-}" ]]; then
    CODEX_ARGS+=(-m "$CODEX_MODEL")
fi

# prompt 作为位置参数传入，并把 stdin 接到 /dev/null：
# codex exec 在非 TTY 且 stdin 未关闭时会打印 "Reading additional input from stdin..." 并等待。
exec "$CODEX_BIN" "${CODEX_ARGS[@]}" "$PROMPT" </dev/null
