#!/usr/bin/env bash
# Backward-compatible entry point; scans BOTH EAR subprojects.
set -euo pipefail
exec python3 "$(dirname "$0")/../../scripts/secret_scan.py" "$@"
