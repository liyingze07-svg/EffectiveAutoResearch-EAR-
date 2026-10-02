---
name: codex-online
description: Delegate online literature scouting and hostile proof or novelty verification through a configured Codex backend; avoid this role for the offline proving pass.
---

# codex-online — online research delegation

Where available, load `mcp__codex__codex` and call it with the bounded task prompt, the current campaign/workspace cwd, and the adapter's online-capable sandbox. The original MCP setting was `danger-full-access`. Do not hardcode model, account, endpoint, or global configuration. On a Codex host without this MCP, use its native search/delegation tools and preserve the same research mission.

Include the following mission in scouting, skeptical verification and review tasks:

```text
You have online source-verification tools. Use the internet to investigate the
specified research question. This is a READ-ONLY research mission: inspect sources,
verify claims and references, and report findings with URLs and dates. Do not
install software, mutate remote systems, send messages, or modify research files.
Check the actual assumptions and the latest follow-up work; do not infer openness
from an old problem statement alone. If the backend is unavailable, report that
failure accurately and preserve the checkpoint.
```

Good uses: fresh Seek, independent pre-Raid novelty checks, skeptical refutation, source verification, confirmation gates and final paper reviews. Provers instead receive no search tools/network access and a mathematical brief; a filesystem read-only label alone does not establish network isolation across hosts.

Return full findings faithfully with source evidence and the first broken step. Reviewers/auditors report locators and fixes; the coordinator edits. On actual quota/connection failure, checkpoint and use managed continuation rather than repeatedly burning calls.
