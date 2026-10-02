---
name: am-guerrilla
description: Scout winnable open problems and run bounded multi-agent informal proof raids with hostile verification, proved partial results, and honest retreat; used inside the complete AutonomousMath engine.
---

# am-guerrilla — bounded proof raids

Fight winnable problems, retain genuine partial results, and retreat quickly from a broken approach. This skill supplies Seek/Raid/Verify to `am-flow`; it does not replace writing and final review in a complete paper run.

## Modes and data

`seek` scouts and ranks problems. `raid <slug> [<slug>…]` attacks supplied targets in order. `auto` automatically selects eligible targets up to the outer batch limit. `status` reads the persistent target/campaign records. Interactive scouting can present a shortlist when requested; an authorized full engine run selects for itself.

Each target has `{slug,title,statement,knownPartials,field,sourceURLs,stillOpenEvidence,difficulty,winOdds,value,status}`. Score is winOdds × value; break ties by difficulty and evidence freshness. Store the original problem and the de-sensationalized brief separately. Keep `targets.json`, `TARGETS.md`, and an append-only `targets/<slug>/HISTORY.md` with provenance, status, rounds, failed routes, and re-arming evidence.

## Seek

Read all existing targets before scouting. Exclude registered slugs and titles, including stale and rejected entries. Independently search the ML-theory routes: learning theory; optimization for ML; bandits/RL; generalization/representation theory; statistical/information theory. Require exact statements and dated original-source evidence. Search subsequent solutions, not only the original open-problem paper. Spot-check the top candidates against the source, merge duplicates and statuses, and persist even rejected candidates with reasons.

Optional adapter: `seek.workflow.js` with `{cwd,exclude,perRoute,scout,routes}`. Pass explicit ML routes when using the adapter. Its output is data; the coordinator owns selection and persistence.

## Asymmetric evidence

The prover receives a RAID_BRIEF containing all precise mathematics and all usable known facts. Remove rhetorical labels such as `famous / unsolved / conjecture`, author names, years, and source links from the brief; call the proposed result a Theorem. Do not remove assumptions or invent facts. The confidence prompt asserts that a proof exists and asks for numbered, justified key steps. A fully proved restricted theorem is a valid fallback; fabrication is not.

The skeptical verifier receives fullContext: original statement, source, real open status, strongest known results, and known failure points. Its default is `refuted=true` until every claimed step survives. It independently checks proof errors, existence and hypotheses of cited facts, novelty, and counterexamples. **Never mix fullContext into the prover brief.** Configure the prover role without browsing tools or network egress. Online verification uses a read-only research mission.

## Raid and decision

1. Read HISTORY before repeating an attack. Feed previous first-broken steps into the prover feedback and the skeptic checklist. A retreated route needs new re-arming evidence before repetition.
2. Run the pre-Raid novelty/venue checks from `am-flow`. Persist STALE or VENUE-SKIP instead of attacking those targets.
3. Launch bounded independent proof angles: constructive/direct, extremal/contradiction, and structural/algebraic/probabilistic as useful. `raid.workflow.js` accepts `{slug,cwd,brief,fullContext,round,feedback,skeptics,angles}`. The original panel uses three skeptical audits per candidate.
4. Save each complete attempt under `campaigns/<slug>/probes/rN-pK.md`, including unsupported steps and declared proved scope. Save audit verdicts and blockers.
5. WON requires a full proof claim and all requested skeptics passing. PARTIAL requires a nontrivial, complete proved scope surviving verification. Otherwise RETREAT.
6. WON → fresh confirmation skeptic + coordinator reads the proof → bank clean proof and pass to Harden. PARTIAL in round 1 → round 2 with precise feedback; after round 2 bank only clean partials and move on. RETREAT → immediately record an honest negative and select another target. **At most two rounds per target.**

The confirmation gate adds a new online skeptical verifier after the panel, with the instruction that accepting a wrong open-problem proof costs more than rejecting a right one. The coordinator checks quantifier changes, circular references, and substantive steps hidden behind “clearly”. Either gate failing downgrades to PARTIAL. Proof files identify themselves as informal and not machine verified; required scientific limitations must remain accurate.

## Optional batching and board

`blitz.workflow.js` accepts a supplied target array and performs two independent prover roles followed by per-target hostile reduce verification. It is a triage adapter; results still need confirmation, hardening, writing, and fixed final review. No historical targets are embedded.

`harden.workflow.js` performs the generic converse audit. `harden-eq-paper.workflow.js` retains the compatibility filename and provides an argument-driven expanded hardening adapter without a private paper story.

When a board endpoint is explicitly configured and reporting is authorized, `board-submit` can claim a target and post results. Missing board service must not block the research loop. Local state remains the source of record.
