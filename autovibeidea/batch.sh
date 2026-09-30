#!/usr/bin/env bash
# Legacy entry point. Keep one execution policy for every batch run.
set -euo pipefail
exec bash "$(dirname "$0")/batch_codex.sh" "$@"
