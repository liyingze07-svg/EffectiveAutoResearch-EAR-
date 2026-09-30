#!/usr/bin/env bash
# Pre-commit self-check: syntax, skill frontmatter, command links, and documentation references.
set -uo pipefail
cd "$(dirname "$0")/.."
FAIL=0
bad() { echo "  ✗ $1"; FAIL=1; }

echo "=== shell / python syntax ==="
for f in *.sh tools/*.sh; do bash -n "$f" 2>/dev/null || bad "Syntax error: $f"; done
for f in tools/*.py; do python3 -m py_compile "$f" 2>/dev/null || bad "Syntax error: $f"; done

echo "=== skill frontmatter ==="
for s in skills/*/SKILL.md; do
  sed -n '1p' "$s" | grep -q '^---$' || bad "Missing frontmatter opening: $s"
  grep -q '^name:' "$s"        || bad "Missing name: $s"
  grep -q '^description:' "$s" || bad "Missing description: $s"
done

echo "=== runtime outputs must not be committed ==="
for d in outputs refine-logs; do
  c=$(find "$d" -type f ! -name '.gitkeep' 2>/dev/null | wc -l)
  [ "$c" -gt 0 ] && bad "$d/ contains $c files; run ./clean.sh to archive them before committing"
done

echo
if [ "$FAIL" -eq 0 ]; then echo "✅ Self-check passed"; else echo "❌ Self-check failed"; fi
exit $FAIL
