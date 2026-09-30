#!/usr/bin/env bash
# Preserve the public shell interface; prompts and responses are data, never code.
set -euo pipefail
exec python3 "$(dirname "$0")/gpt_call.py" "$@"
