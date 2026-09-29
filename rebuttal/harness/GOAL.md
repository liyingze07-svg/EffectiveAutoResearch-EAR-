# GOAL.md — Explicit goal and stopping criterion (first-class)

> The engine reads this file every round to decide whether it is done. **This is a checkable predicate, not a narrative.**
>
> ⚠️ **Single source of truth + drift guard**: the authoritative implementation of the zone bar is `rebuttal_verifier/consensus_gate.bar_met` / `consensus`; the table below is its human-readable mirror. **Changing the criterion means changing three places**: ① this table ② `bar_met`/`consensus` ③ the matching assertions in `consensus_gate._selfcheck()`. `orchestrate.py` runs `_selfcheck()` at startup, so any drift between this table and the implementation (e.g. H4: OA≥4 must use the maintain bar, not the raise bar) makes it **refuse to start** rather than run all night with a broken criterion.
>
> 🔎 **Who uses this bar**: the r7 raise gate (halting for a whole draft) and the **S-exp experiment persuasion gate** (`stages/r4_experiment_persuasion.md`, between r4 and r5, which calls **the same** `bar_met` per concern against a **single experiment's real result**). S-exp is a **consumer** of this bar and adds no criterion of its own, so it is **not** part of the three-place rule above.

## Goal (one sentence)

For **each targeted reviewer**, make the rebuttal clear **the bar for that reviewer's zone** under the **cross-family consensus gate**. All clear means DONE; otherwise keep rolling per `LOOP.md`, and if `max_iter` is reached without clearing, emit the best-so-far with an **honest concession**.

## Zone bars (by the reviewer's overall assessment, decided by `consensus_gate.bar_met`)

| Zone | Bar (both families must satisfy it) |
|---|---|
| **OA = 3 (borderline)** | Diagnoser reports `veto == 'none'` **and** `raise_potential == 'high'` (i.e. sufficient strength — **not** a prediction of the score change, because the borderline outcome is not predictable from text) |
| **OA ≤ 2 (low start)** | `reaction == 'raise'` (a raise signal exists from a low starting score) |
| **OA ≥ 4 (high start)** | `reaction != 'lower'` (hold the score, do not drop) |

## Stopping criterion (DONE ⟺ all true)

Consensus is **zone-routed** (see `consensus_gate.consensus`); not every zone uses the same conjunction. For each targeted reviewer:

```
DONE ⟺  ∀ reviewer ∈ target.require_raise_on ∪ target.maintain:
            consensus(deepseek, codex, case).stop == True   # zone-routed, see below
        AND ammo_hits(final_rebuttal) == []                 # ammunition hard gate (all zones)
        AND no_fabrication(rebuttal, evidence)              # every claim traces to real evidence

where consensus(...).stop depends on the zone:
  · OA ≤ 2 / OA ≥ 4 (strict mode)        ⟺  bar_met(deepseek) AND bar_met(codex)
  · OA = 3 borderline (authoritative)    ⟺  bar_met(codex_primary) AND deepseek.reaction != 'lower'
```

- **Why OA=3 is not strict**: at the borderline DeepSeek separates quality weakly (README §7: +0.13 versus Codex's +0.28). Forcing DeepSeek to clear the bar as well would inject false negatives and deadlock the loop. So the authoritative judge is Codex/GPT-5.5 (high reasoning) and DeepSeek is demoted to a **soft veto** — it only has to refrain from judging `lower`. Every other zone treats the two families as equals and requires both.
- **Still cross-family**: even in authoritative mode a DeepSeek `lower` blocks halting, so fitting Codex alone cannot get a draft through. Invariant #4 holds.

## Exits

- **DONE** → package the per-reviewer rebuttals and the AC comment.
- **max_iter reached without DONE** → for each reviewer that did not clear, emit the best-so-far plus an honest concession and a list of the gaps, marked `HONEST_CONCEDE`. **Never fabricate an experiment or fit the judge to make something "look like it passed".**

## Inviolable (breaking any of these voids the round)

1. Never invent a number or a citation. If you cannot support it, write `[TBD]` — not an empty promise.
2. `ammo_hits == 0`, including soft ammunition such as performative honesty and over-concession (see `ammunition-checklist`).
3. The worker never sees the gate's internal prompt and must not fit the criterion.
4. Halting requires cross-family consensus; a single judge is never sufficient.
