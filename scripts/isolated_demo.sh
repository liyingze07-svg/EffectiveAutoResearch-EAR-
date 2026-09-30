#!/usr/bin/env bash
# Linux-only zero-cost demo: read-only checkout, private /tmp, no host home or network.
# Fail closed when bubblewrap/user namespaces are unavailable. No model is invoked.
set -euo pipefail
umask 077
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
command -v bwrap >/dev/null || { echo "Install bubblewrap on Linux to use this optional isolated demo." >&2; exit 2; }
DEMO_OUTPUT="$(mktemp -d -t ear-isolated-demo-XXXXXX)"
MOUNTS=()
for runtime_dir in /usr /bin /lib /lib64; do
    if [[ -L "$runtime_dir" ]]; then
        MOUNTS+=(--symlink "$(readlink "$runtime_dir")" "$runtime_dir")
    elif [[ -d "$runtime_dir" ]]; then
        MOUNTS+=(--ro-bind "$runtime_dir" "$runtime_dir")
    fi
done
bwrap --die-with-parent --new-session --unshare-all --cap-drop ALL \
    --clearenv --setenv PATH /usr/bin:/bin --setenv LANG C.UTF-8 \
    "${MOUNTS[@]}" --proc /proc --dev /dev --tmpfs /tmp \
    --ro-bind "$ROOT" /workspace --bind "$DEMO_OUTPUT" /results --chdir /workspace \
    -- python3 -B scripts/offline_demo.py --output /results/demo
printf 'Host outputs: %s/demo\n' "$DEMO_OUTPUT"
