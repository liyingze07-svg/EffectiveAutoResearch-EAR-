#!/bin/bash
# Run the verifier on the bundled example case. Requires rebuttal_verifier/.env
# (copy from .env.example and fill in DEEPSEEK_API_KEY).
cd "$(dirname "$0")/.."

echo "=== single case ==="
python3 verify_rebuttal.py --case examples/example_case.json

echo ""
echo "=== batch (same case x2) ==="
printf '%s\n%s\n' "$(cat examples/example_case.json | python3 -c 'import sys,json;print(json.dumps(json.load(sys.stdin)))')" \
                  "$(cat examples/example_case.json | python3 -c 'import sys,json;print(json.dumps(json.load(sys.stdin)))')" \
  > /tmp/_rv_batch.jsonl
python3 verify_rebuttal.py --batch /tmp/_rv_batch.jsonl --out /tmp/_rv_preds.jsonl
cat /tmp/_rv_preds.jsonl
