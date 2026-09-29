#!/usr/bin/env bash
# 提交前自检：语法、skill frontmatter、命令链接、文档引用。
set -uo pipefail
cd "$(dirname "$0")/.."
FAIL=0
bad() { echo "  ✗ $1"; FAIL=1; }

echo "=== shell / python 语法 ==="
for f in *.sh tools/*.sh; do bash -n "$f" 2>/dev/null || bad "语法错误: $f"; done
for f in tools/*.py; do python3 -m py_compile "$f" 2>/dev/null || bad "语法错误: $f"; done

echo "=== skill frontmatter ==="
for s in skills/*/SKILL.md; do
  sed -n '1p' "$s" | grep -q '^---$' || bad "缺少 frontmatter 起始: $s"
  grep -q '^name:' "$s"        || bad "缺少 name: $s"
  grep -q '^description:' "$s" || bad "缺少 description: $s"
done

echo "=== 运行产出不应入库 ==="
for d in outputs refine-logs; do
  c=$(find "$d" -type f ! -name '.gitkeep' 2>/dev/null | wc -l)
  [ "$c" -gt 0 ] && bad "$d/ 有 $c 个文件，提交前请 ./clean.sh 归档"
done

echo
if [ "$FAIL" -eq 0 ]; then echo "✅ 自检通过"; else echo "❌ 自检未通过"; fi
exit $FAIL
