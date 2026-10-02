---
name: board-submit
description: Submit research target claims, findings, or conjectures to an explicitly configured compatible local board; use only when reporting is authorized and a board service is available.
---

# board-submit — optional research board adapter

This adapter preserves the source engine's claim/result/conjecture reporting capability. It is optional. `submit_client.py` is a Python standard-library client; no board server is bundled. Configure `--host` and `--port` for the compatible service (default loopback:9312). A missing service does not block research.

Before claiming a target, inspect the board's `/api/state` if supported and check the local target registry. Post only within authorized reporting scope:

```bash
python3 <skill-dir>/submit_client.py claim --slug <slug> --by <run-id>
python3 <skill-dir>/submit_client.py result --slug <slug> --by <run-id> --body <findings>
python3 <skill-dir>/submit_client.py conjecture --title <title> --statement <statement> --by <run-id>
```

Submissions enter the board queue; they do not overwrite canonical target/campaign state. Save state locally through `am-flow` regardless of board availability. Do not expose credentials, private machine paths or unpublished material in a public board unless the user has authorized publication.
