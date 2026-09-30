#!/usr/bin/env bash
# exec preserves the launcher PID and lock; Python owns cancellation and reaping.
set -euo pipefail
umask 077
exec python3 "$(dirname "$0")/background_runner.py" run "$@"
