#!/usr/bin/env bash
# Run EAR from a source checkout without changing the caller's working directory.
set -euo pipefail
EAR_SOURCE_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${EAR_SOURCE_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
exec python3 -m ear "$@"
