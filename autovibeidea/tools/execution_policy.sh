#!/usr/bin/env bash
# Shared by foreground, background, batch, and external-review CLI entry points.
ear_execution_policy() {
    case "${EAR_UNSAFE:-0}:${EAR_ALLOW_NETWORK:-0}" in
        0:0|0:1|1:0|1:1) ;;
        *) echo "EAR_UNSAFE and EAR_ALLOW_NETWORK must be 0 or 1" >&2; return 2 ;;
    esac
    CODEX_SECURITY_ARGS=(-c 'approval_policy="never"')
    if [[ "${EAR_UNSAFE:-0}" == 1 ]]; then
        CODEX_SECURITY_ARGS+=(--dangerously-bypass-approvals-and-sandbox)
        echo "WARNING: --unsafe disables sandboxing; commands can access the host and network." >&2
    else
        CODEX_SECURITY_ARGS+=(-c 'sandbox_mode="workspace-write"'
            -c 'sandbox_workspace_write.writable_roots=[]'
            -c "sandbox_workspace_write.network_access=$([[ "${EAR_ALLOW_NETWORK:-0}" == 1 ]] && echo true || echo false)")
    fi
    if [[ "${EAR_ALLOW_NETWORK:-0}" == 1 || "${EAR_UNSAFE:-0}" == 1 ]]; then
        CODEX_SECURITY_ARGS+=(-c 'web_search="live"')
    else
        CODEX_SECURITY_ARGS+=(-c 'web_search="disabled"')
    fi
}

ear_data_notice() {
    echo "Live run: prompts, paper/review text and tool results may be sent to configured model services." >&2
    echo "Local outputs, threads and CLI history may retain this content. Use only authorized inputs; see README Data handling." >&2
}
