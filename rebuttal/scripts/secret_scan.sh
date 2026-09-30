#!/usr/bin/env bash
# Secret scanner —— output displays masks only and never prints secrets in plaintext.
#
#   scripts/secret_scan.sh            Scan the workspace (tracked + unignored files subject to .gitignore)
#   scripts/secret_scan.sh --staged   Scan only content that will be committed after `git add` (for pre-commit)
#
# Exit codes:0 = clean;1 = hit, must not be committed.
# See OPENSOURCE_SANITIZE_TODO.md for the checklist and background.
set -uo pipefail
cd "$(dirname "$0")/.."

MODE="${1:-worktree}"
if [[ "$MODE" == "--staged" ]]; then
  mapfile -t FILES < <(git diff --cached --name-only --diff-filter=ACM)
else
  mapfile -t FILES < <(git ls-files --cached --others --exclude-standard 2>/dev/null || find . -type f -not -path './.git/*')
fi
[[ ${#FILES[@]} -eq 0 ]] && { echo "No files need to be scanned."; exit 0; }

# Rules:name|regex. Placeholders (REDACTED / xxx / <> / $VAR) are uniformly exempted below.
RULES=(
  "OpenRouter API key|sk-or-v1-[A-Za-z0-9]{20,}"
  "Anthropic/OpenAI key|sk-(ant|proj|live)-[A-Za-z0-9_-]{20,}"
  "generic long sk- secret|sk-[A-Za-z0-9]{32,}"
  "sshpass plaintext password|sshpass +-p"
  "password assignment|(password|passwd|PASSWORD)[[:space:]]*[:=][[:space:]]*[^[:space:]\$<]{6,}"
  "private key file|BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY"
  "Bearer token|Bearer [A-Za-z0-9._-]{24,}"
  "HuggingFace token|hf_[A-Za-z0-9]{30,}"
  "GitHub token|gh[pousr]_[A-Za-z0-9]{30,}"
)
# Exemptions:placeholders, variable references, and **the scanner's own rule text** (grep/regex documentation is not a credential)
# Keep the original multilingual example marker without changing matching behavior.
EXEMPT='REDACTED|xxxxx|XXXXX|placeholder|PLACEHOLDER|your[-_]?key|<[^>]+>|\$\{?[A-Z_]+\}?|'$'\u4f8b\u5982''|example|EXAMPLE'
EXEMPT="$EXEMPT"'|grep -[rnIE]|secret_scan|\[\[:space:\]\]|RULES=\('

hits=0
for f in "${FILES[@]}"; do
  [[ -f "$f" ]] || continue
  file "$f" | grep -qi 'text\|json\|script' || continue      # Skip binary files
  for rule in "${RULES[@]}"; do
    name="${rule%%|*}"; re="${rule#*|}"
    while IFS=: read -r ln content; do
      [[ -z "${ln:-}" ]] && continue
      echo "$content" | grep -qE "$EXEMPT" && continue        # Exempt placeholders
      # Mask:retain only the first 4 characters of the matched segment
      masked=$(echo "$content" | sed -E "s/($re)/\[\1\]/g" \
               | sed -E 's/\[(.{4})[^]]*\]/\1…REDACTED/g' | cut -c1-110)
      printf '🔴 %-22s %s:%s\n     %s\n' "$name" "$f" "$ln" "$masked"
      hits=$((hits+1))
    done < <(grep -nIE "$re" "$f" 2>/dev/null)
  done
done

echo "────────────────────────────────"
if [[ $hits -eq 0 ]]; then
  echo "✓ Clean:$hits hits (scanned ${#FILES[@]} files)"; exit 0
else
  echo "🔴 $hits hits —— do not commit. Fix them first or add them to .gitignore."; exit 1
fi
