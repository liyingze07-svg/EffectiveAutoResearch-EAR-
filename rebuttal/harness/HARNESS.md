# AutoRebuttal Harness (index)

> A paper-agnostic operating system for rebuttals. Input a paper and its reviews; parallel strategies write the rebuttal; a frozen raise gate adjudicates; goal mode keeps looping until the zone bar is cleared. Version: see `HARNESS_VERSION`.

## First principles (the foundation)

1. **A loop can DRIVE; it cannot ACQUIT.** The worker writes, a frozen cross-family raise gate judges. They are physically separated and the worker never sees the judge's internals.
2. **Writing is argument compilation, not next-token generation.** Strategic goal → argument DAG → check logic, redundancy and first principles → render → decompile and verify.
3. **The raise gate is the only bar.** A draft passes only when DeepSeek and Codex **agree** (cross-family, to resist Goodharting). The bar is score-aware: OA≤2 wants a raise, OA=3 wants strength, OA≥4 wants the score held. **The authoritative Codex judge runs on a separate `JUDGE_MODEL` (default gpt-5.6-sol) and never reuses the writer's model** — otherwise a GPT writer acquits itself. Frozen SPEC, honesty bright lines, `ammo_hits == 0`.
4. **Paper-agnostic.** Switching cases means writing a new `REBUTTAL_CARD.json`, not editing the harness.

## Execution model (v0.8: materialized stages, Codex engine, enforced gates)

- Explicit goal and loop: `GOAL.md` (the zone-routed stopping predicate) and `LOOP.md` (the MoE select-refine protocol).
- Materialized stage prompts: `stages/*.md` (**18 of them**, r0a→ac), each with explicit I/O, numbered rules and a DO-NOT list.
- General MoE: `strategies/MANIFEST.json`, the shared `CRAFT.md`, and s1/s2/s3 (pluggable and composable).
- Thin driver: `runner/orchestrate.py` reads MANIFEST/GOAL/LOOP, dispatches each stage to a fresh `codex exec` process, verifies the receipt, and runs the loops.

## Lifecycle r0a → ac

r0a extract card → r1 evidence map → r2 diagnose concerns → **B1 concern gate** → r3 response-mode triage → **[experiment goal loop, `EXPERIMENT_LOOP.md`]** S-ante gate (is an experiment needed at all?) → (r4 run → code audit acceptance → **S-exp persuasion gate**, zone-routed, only STRENGTH halts → otherwise `r4_experiment_redesign` produces "why it failed and how to redesign" → rerun)* until STRENGTH or an honest concession → **r5 evidence merge** (only accepted evidence that cleared the persuasion gate) → r6 MoE argument compilation (following `framing_hint`) → r7 raise consensus gate + goal loop → **B2 faithfulness gate + B3 ammunition gate** → mt multi-turn exchange → ac package.

> There are **two** goal loops: the **experiment loop** (`EXPERIMENT_LOOP.md`, iterating an experiment until it is persuasive) and the **reviewer loop** (`LOOP.md`, iterating the rebuttal until it clears r7). Their stopping criteria are S-exp and r7 respectively, and both reuse the frozen `bar_met`.

## Layout

```
harness/
├── stages/*.md                     ★ 18 materialized stages, engine-agnostic
├── strategies/MANIFEST.json + CRAFT.md + s*.md   ★ general MoE (CRAFT is the shared brain)
├── runner/orchestrate.py           ★ thin driver (dispatches to the Codex engine)
├── runner/cost.py                  per-call cost ledger
├── instantiate.py                  REBUTTAL_CARD.json → contracts
├── templates/
│   ├── GOAL.tmpl.md                the methodological core (r0→r7, goal loop, per-round closeout)
│   ├── SPEC.tmpl.md                frozen acceptance (raise-gate consensus + honesty gate)
│   ├── VERIFY.tmpl.md              independent verifier (reruns the gate to decide ACQUIT)
│   ├── CLAUDE.tmpl.md              per-campaign briefing
│   ├── RESOURCE.tmpl.md            budget (gate calls, writing, experiments)
│   └── REBUTTAL_CARD.schema.json   card schema and example
├── runner/
│   ├── loop_runner.py              r7 gate scaffolding (ICLR + EMNLP OA=3)
│   ├── coach_loop.py               diagnoser coaching-loop orchestrator
│   └── moe_loop.py                 MoE select-refine orchestrator
└── shared-assets/
    ├── ammunition-checklist.md     the ammunition list (must have zero hits)
    ├── experiment-ladder.md        warrant fallback ladder + experiment request contract
    ├── rebuttal-tips.md            concern taxonomy and response playbook
    └── strategies.md               notes on the MoE pool
../rebuttal_verifier/consensus_gate.py   the frozen cross-family raise gate (DeepSeek θ₀ + Codex judge, zone bars)
campaigns/<case>/                        per-case contract workspace: ledger/, drafts/, experiments/
```

## Reused components

- DeepSeek side of the raise gate: `../rebuttal_verifier/verify_rebuttal.py` (benchmarked at 0.805 macro-F1 on ICLR) plus `consensus_gate.py` for the consensus itself.
- Second judge: Codex, invoked through `codex exec` from `orchestrate.py`, running a separate `JUDGE_MODEL`.

## Read these four and you have 80% of it

`GOAL.md` and `LOOP.md` (the explicit goal and loop), `EXPERIMENT_LOOP.md` (the experiment loop), and `runner/orchestrate.py` (how it is all wired).
