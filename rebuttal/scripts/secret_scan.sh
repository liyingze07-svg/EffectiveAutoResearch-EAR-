#!/usr/bin/env bash
# 密钥扫描器 —— 输出只显示掩码,绝不打印密钥原文。
#
#   scripts/secret_scan.sh            扫工作区(受 .gitignore 约束的已跟踪+未忽略文件)
#   scripts/secret_scan.sh --staged   只扫 `git add` 后将被提交的内容(用于 pre-commit)
#
# 退出码:0 = 干净;1 = 命中,不该提交。
# 清单与背景见 OPENSOURCE_SANITIZE_TODO.md。
set -uo pipefail
cd "$(dirname "$0")/.."

MODE="${1:-worktree}"
if [[ "$MODE" == "--staged" ]]; then
  mapfile -t FILES < <(git diff --cached --name-only --diff-filter=ACM)
else
  mapfile -t FILES < <(git ls-files --cached --others --exclude-standard 2>/dev/null || find . -type f -not -path './.git/*')
fi
[[ ${#FILES[@]} -eq 0 ]] && { echo "没有文件需要扫描。"; exit 0; }

# 规则:名称|正则。占位符(REDACTED / xxx / <> / $VAR)在下面统一豁免。
RULES=(
  "OpenRouter API key|sk-or-v1-[A-Za-z0-9]{20,}"
  "Anthropic/OpenAI key|sk-(ant|proj|live)-[A-Za-z0-9_-]{20,}"
  "通用 sk- 长密钥|sk-[A-Za-z0-9]{32,}"
  "sshpass 明文密码|sshpass +-p"
  "password 赋值|(password|passwd|PASSWORD)[[:space:]]*[:=][[:space:]]*[^[:space:]\$<]{6,}"
  "私钥文件|BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY"
  "Bearer token|Bearer [A-Za-z0-9._-]{24,}"
  "HuggingFace token|hf_[A-Za-z0-9]{30,}"
  "GitHub token|gh[pousr]_[A-Za-z0-9]{30,}"
)
# 豁免:占位符、变量引用,以及**扫描器自身的规则文本**(grep/正则文档不是凭据)
EXEMPT='REDACTED|xxxxx|XXXXX|placeholder|PLACEHOLDER|your[-_]?key|<[^>]+>|\$\{?[A-Z_]+\}?|例如|example|EXAMPLE'
EXEMPT="$EXEMPT"'|grep -[rnIE]|secret_scan|\[\[:space:\]\]|RULES=\('

hits=0
for f in "${FILES[@]}"; do
  [[ -f "$f" ]] || continue
  file "$f" | grep -qi 'text\|json\|script' || continue      # 跳过二进制
  for rule in "${RULES[@]}"; do
    name="${rule%%|*}"; re="${rule#*|}"
    while IFS=: read -r ln content; do
      [[ -z "${ln:-}" ]] && continue
      echo "$content" | grep -qE "$EXEMPT" && continue        # 占位符豁免
      # 掩码:命中片段只留前 4 字符
      masked=$(echo "$content" | sed -E "s/($re)/\[\1\]/g" \
               | sed -E 's/\[(.{4})[^]]*\]/\1…REDACTED/g' | cut -c1-110)
      printf '🔴 %-22s %s:%s\n     %s\n' "$name" "$f" "$ln" "$masked"
      hits=$((hits+1))
    done < <(grep -nIE "$re" "$f" 2>/dev/null)
  done
done

echo "────────────────────────────────"
if [[ $hits -eq 0 ]]; then
  echo "✓ 干净:$hits 处命中(扫了 ${#FILES[@]} 个文件)"; exit 0
else
  echo "🔴 命中 $hits 处 —— 不要提交。先修掉或加进 .gitignore。"; exit 1
fi
