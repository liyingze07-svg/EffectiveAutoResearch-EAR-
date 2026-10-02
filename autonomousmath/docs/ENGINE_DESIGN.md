# AutonomousMath engine design

AutonomousMath is the complete model-driven research engine: independent open-problem scouting → novelty and venue checks → informal proof raids and hostile verification → claim hardening → complete LaTeX paper → independent fixed review → targeted revision or another target. The authoritative combination is `prompts/goal.prompt` plus the six bundled skills. The launcher gives this goal to a tool-using model; the model decides which tools to call and how to respond to mathematical evidence.

## Preserved loop

The proving pass gets exact mathematics and usable facts without rhetorical open-problem labels. Independent online skeptics get the real provenance, prior results and proof attempts. Failed steps become feedback; complete proved partial results remain available. Each target has at most two raid rounds. Before writing, a separate prove/refute/adjudicate pass tests every strong converse or optimality claim.

Writing locks architecture, notation and theorem labels before drafting. Technical sections and full proofs come first, followed by front matter, six audits, revision and compilation. The final paper includes ≥7 pages of main text and complete justified proofs. Scientific claims must match established results; speculative extensions and draft remnants do not count as contributions.

Final reviewers receive the full paper and unchanged SAC standard. Both independent reviews must meet the goal's acceptance condition. Their findings drive another proof/hardening/writing pass. The default allows an initial review and at most two revision cycles, then the outer loop may change target. A simulated review decision is reported as such.

## Native hosts

For Claude Code, install the skills into a chosen workspace, enter that workspace, and supply the rendered goal prompt. `/goal` is a native convenience only when the particular host exposes it; the package does not assume every installation implements that command. `am-flow auto`, `run`, `resume` and `status` are skill-driven intents, not standalone operating-system commands.

For Codex, install the same skills into `.agents/skills`, then give the rendered goal to a session with shell, filesystem, search and independent delegation tools. Native tools can perform the original roles when the Codex MCP is unavailable. Always record actual providers and capabilities. A filesystem read-only setting alone does not guarantee a network-isolated prover.

The original MCP adapter uses `mcp__codex__codex`/`codex-reply`. Its eight JavaScript workflows are optional host adapters requiring injected `args`, `agent`, `parallel`, `pipeline`, `phase` or `log` helpers. They are not standalone Node programs and are not nested into a giant workflow. Without that runtime, the coordinating model directly performs the same phase intentions; writing and review remain mandatory.

## Managed execution and final review

The portable runner supplies workspace/campaign/engine/skill/referee paths and optional direction. It repeatedly invokes the chosen CLI host with the complete combination prompt and current checkpoint. This provides continuation when a single host invocation ends, while leaving research tool calls and internal stage decisions to the model.

A worker submits `proof.md`, complete `paper/` sources and `paper/main.pdf`, plus `CANDIDATE.json` with `draft_ready`, `retreat` or `checkpoint`. The parent runner submits ready papers to the external frozen referee and returns findings for same-episode revision. A worker-authored “ACCEPT” report is internal evidence, not final acceptance.

Batching and GA operate outside the episode loop. They can compare/change engine prompts, tool selection, workflow strategies and code, then execute candidate variants. The fixed final referee remains outside that changeable working context. The objective is fewer attempts and less rework per high-quality accepted paper, rather than a new accounting objective imposed on the research story.

## Persistent state

Keep each episode's target registry, proofs, attempted routes, negative findings, hardening decisions, LaTeX sources, audit reports and referee feedback. `PROGRESS.md` records timestamp, stage, completed artifacts, blocker and next action. `HISTORY.md` retains prior failed routes; a resumed run does not discard a verified result or retry the same dead end without new evidence.

Actual quota/connection failures produce a checkpoint. The managed runner or a supported native wakeup mechanism resumes after backoff. A native session without persistent scheduling can resume from files but should not claim it arranged unattended recovery.

## Final Lean interface

The engine first completes natural-language mathematics and paper review. After success, an optional final-check adapter can receive the claims and proofs for Lean formalization. Report which claims were translated, checked or unresolved separately from paper-review acceptance. No Lean service or weights are required by the basic engine.

## Package boundaries

The package contains six skills, eight optional workflow scripts, general writing/proof-audit guides, and LaTeX templates/style assets. It carries no runtime research history, account configuration or private parent-project dependency. The optional board client needs a separately configured compatible server and can be skipped.

`scripts/install_skills.py --workspace <path>` installs the six skills under that workspace's `.claude/skills` and `.agents/skills`. It checks collisions before writing; `--force` replaces only same-named installed skills. It does not modify global configuration or start any model calls. The caller owns backend setup and provides the runner's fixed referee path.
