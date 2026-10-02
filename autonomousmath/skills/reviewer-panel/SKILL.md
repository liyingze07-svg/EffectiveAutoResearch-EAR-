---
name: reviewer-panel
description: Review a complete AutonomousMath paper with independent SAC panels and return precise revision findings; final managed-run acceptance is decided by the frozen external referee.
---

# reviewer-panel — fixed terminal review

Read the complete paper with its definitions, claims, appendix proofs and references. Apply the unchanged SAC prompt from `autonomousmath/referee/SAC_PROMPT.md` supplied by the engine/runner. The bundled `SAC_PROMPT.md` preserves the earlier source skill's full SAC specification for provenance; the managed runner's frozen prompt is authoritative.

Run an independent Codex review and an independent Claude review when those backends are configured. Each receives the full paper text and full prompt, not a summary, and does not inherit the author's self-assessment. Alternate providers only when the configured setup supports them; never silently label one provider as another. Without the original tools, use independent review agents exposed by the host and record their actual backends. A model reviewing its own context cannot substitute for the independent final gate.

The source goal requires both reviews at least Weak Accept. The final Meta recommendation is `Reject`, `Accept (Poster)`, or `Accept (Oral)`; a campaign needs both independent Meta recommendations to be Accept. Individual reviewer ratings do not override a rejecting Meta verdict. Preserve the venue/scope gate and the exact fixed prompt rather than making criteria easier for the current paper.

Optional host adapter:

```text
Workflow(scriptPath="<skill-dir>/review.workflow.js",
         args={dir:"<campaign>", paperDir:"<campaign>/paper", round:1,
               instances:2, acceptThreshold:2, sacPrompt:"<frozen-referee-prompt>"})
```

The adapter returns `{accepted,accepts,verdicts,findings,reports}`. It requires Workflow/agent/parallel/log runtime support; otherwise delegate independent tool calls directly. Coordinator-owned reports go to `reviews/round-N/{verdicts.json,REPORT.md}`. Managed-run acceptance comes from the external referee, not this working-model report.

Findings use `{point,severity: blocker|major|minor,fix}`. Deduplicate points, put blockers first, and return exact actionable fixes. Overclaim, missing converse, invalid proofs or fundamental contribution gaps go back to Harden/Raid; writing/structure problems go back to writing Phase E. Initial review plus at most two revision cycles; at the cap, save the unsuccessful outcome for the outer loop.

Simulated SAC acceptance is a research evaluation signal, not an actual conference acceptance or a formal mathematical certificate. Lean checking is a separate, optional final step after successful paper review.
