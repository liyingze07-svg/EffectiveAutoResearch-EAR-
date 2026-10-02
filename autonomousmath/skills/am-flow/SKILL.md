---
name: am-flow
description: Drive the complete AutonomousMath research engine from a fresh ML-theory problem through informal proof, hardening, LaTeX writing, independent review, and revision; use for an end-to-end paper run or resuming its checkpoint.
---

# am-flow — complete research loop

The engine is a model-driven loop, not a proof-only tool or a fixed stage scheduler. Read the rendered `prompts/goal.prompt` supplied by the launcher: it is the goal contract. Claude Code and Codex can both be the coordinating host. The host builds prompts, delegates work, writes files, inspects findings, and chooses the next action. In the original Claude + Codex setup, Claude coordinates and writes LaTeX while Codex performs scouting, proving, and auditing. On another host, preserve those independent roles using its available agent tools.

## Invocation and continuation

- `am-flow auto`: run the complete loop autonomously. Select a target without asking for stage-by-stage confirmation; continue through writing and review rather than stopping at a proof.
- `am-flow run <slug>`: run the complete loop on the supplied target.
- `am-flow resume <slug>`: read that campaign's artifacts and checkpoint, and continue at the next incomplete action.
- `am-flow status`: report target, campaign, and review state.

An explicit request for one stage authorizes that stage. A complete run includes all stages. The batch/GA runner can repeat episodes and compare engine variants; this skill owns the research decisions within an episode.

## Loop contract

1. **Seek.** Independently scout 3–5 ML-theory open problems using current COLT/ALT/NeurIPS open-problem tracks, arXiv, and original sources. Require a precise mathematical statement, source URL, dated openness evidence, difficulty, and estimated win odds. Prefer difficulty ≤3 and winOdds ≥0.20. Read `targets.json` to exclude duplicates; retain earlier evidence and failed approaches. A resumed selected target does not require repeating a completed scout.
2. **Novelty and venue.** Before Raid, independently search for solved/follow-up papers using title, author, and exact mathematical terms through the current date. SOLVED → STALE and select another target. Require a genuine ML-theory interface: learning, optimization, generalization, bandits/RL, statistical inference, information theory, or algorithms for ML. Out-of-scope → record VENUE-SKIP and select another target.
3. **Raid + Verify.** Read `am-guerrilla/SKILL.md`. Give the prover only the exact de-sensationalized mathematical brief and known facts; give skeptics the real provenance, openness, and prior failures. Use independent angles, hostile verification, and the confirmation gate. WON → Harden; PARTIAL → a second round with feedback; RETREAT → another target. Hard limit: two raid rounds per target. Preserve complete proved partial results rather than speculative extensions.
4. **Harden.** Before writing, test every `iff / tight / characterization / optimal` claim, especially its converse. Prove versus refute, then independently adjudicate. Unsupported directions are downgraded; save exact corrected claims and paper edits in `HARDENING.md`. A faithful transcription of an unsupported claim does not make it correct.
5. **Write.** Read `theory-to-paper/SKILL.md`: lock architecture, notation and theorem labels; draft technical sections and full appendix proofs; write front matter; run the six audits; apply findings and compile. Require ≥7 pages of main text, complete numbered reasoning, precise lemma hypotheses, claims matching established results, no draft remnants, and a clean build with no undefined references.
6. **Review.** Read `reviewer-panel/SKILL.md`. Send the complete assembled paper, including appendix proofs, to independent reviewers using the unchanged SAC prompt. A summary is insufficient. In managed execution, submit the paper to the runner's external frozen referee; a working-model self-report cannot establish final acceptance.
7. **Revision.** Proof errors → repair proofs; contribution too narrow → a bounded generalization Raid; overclaim/converse blockers → Harden; prose/structure issues → writing Phase E. Recompile and submit again. Maximum two revision cycles after the initial review. At the cap, record the unsuccessful result and move to another target when the outer run continues.

## Tools and optional workflows

Use the host's tools for reading, editing, shell checks, internet search and independent agents. Where configured, load `mcp__codex__codex` and `mcp__codex__codex-reply`; pass prompt, sandbox and cwd without hardcoded model/account overrides. Provers must have no internet tools or network egress; `read-only` is an original adapter setting, not a portable promise of network isolation. Seek/skeptics/review need online source verification with a read-only research mission.

The eight bundled JavaScript workflows are optional adapters for hosts that provide `Workflow`, `agent`, `parallel`, `pipeline` and `log`. Invoke each workflow from the coordinating host, not from a nested Workflow. If Workflow is absent, carry out the same phase intentions through direct agent/tool calls. Write and Review remain required. Bound each delegated prompt, use available concurrency conservatively, and save outputs between expensive actions.

## State and recovery

Keep state inside the run workspace, never in private/global configuration:

```text
targets.json / TARGETS.md / PROGRESS.md
targets/<slug>/HISTORY.md
campaigns/<slug>/
  PROBLEM.md / HISTORY.md / probes/ / proofs/
  VERDICT.md / HARDENING.md / STATUS.md / PROGRESS.md
  paper/main.tex / sections/ / appendix/ / main.pdf / NOTATION.md / refs.bib
  reviews/round-N/verdicts.json / REPORT.md
```

Update progress at every milestone and periodically during long actions. Include an ISO timestamp, stage, completed artifacts, blocker, and next action. Merge target updates without overwriting earlier statuses or histories. Persist negative findings as well as successful proofs.

On a real quota/connection failure, save `RESUME stage=... done=... next=...`, retain verified proof files, and use the runner's continuation/backoff or a supported wakeup tool. Do not spin-retry or rerun completed stages. A native interactive session can resume from files; unattended recovery requires a live host or the managed runner. Do not claim recovery was scheduled when the host lacks that capability.

## Completion and final checking

A campaign completes when the fixed referee accepts its complete paper. At caps or unrecoverable tool failures, save an honest status and the next available action. The outer loop may then change target or engine variant. Informal checks are not Lean verification, and simulated review is not a real conference decision.

After successful paper review, expose the completed claims/proofs to the optional final-check Lean adapter. Lean is not required during natural-language research. Report its actual coverage and status separately from paper acceptance.
