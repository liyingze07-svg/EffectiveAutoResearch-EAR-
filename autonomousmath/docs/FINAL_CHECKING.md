# Final checking contract

The research loop uses informal proofs. Formalization runs only after a real
terminal-review pass. Without a configured checker, the result is `deferred`,
with empty coverage.

Configure an argv list in the engine JSON configuration:

```json
{
  "final_check_command": ["python3", "path/to/your_autoformalizer.py", "--request", "{request}"],
  "final_check_timeout_sec": 600
}
```

No shell expansion is performed. The request JSON contains `campaign_dir`,
`paper_content_hash` and `output_file`. The checker reads the accepted paper,
formalizes selected claims, runs Lean, and writes the requested result file:

```json
{
  "status": "partial",
  "paper_content_hash": "the hash from the request",
  "coverage": [
    {"claim_id": "theorem-1", "lean_file": "Theorem1.lean", "status": "verified"}
  ]
}
```

Allowed statuses are `verified`, `partial`, `failed`, and `blocked`. The result
must bind to the supplied paper version and declare claim coverage. A verified
Lean file is not automatically a guarantee that every informal manuscript claim
has been translated faithfully.

An optional adapter for an existing Lean/Mathlib project is available:

```bash
python3 -m autonomousmath.checking --code path/to/Theorem1.lean --project path/to/lean-project
```

Install [LeanSearch-v2](https://github.com/frenzymath/LeanSearch-v2) with its
`[lean]` extra in your own environment to use this adapter. It lazily imports
the upstream `LeanInteractVerifier`, verifies supplied Lean code, and reports
unfinished proofs. No Lean models, indexes, toolchains or upstream repository
are bundled or installed automatically. The upstream project retains its own
license.
