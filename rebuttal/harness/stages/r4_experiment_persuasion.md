# stage r4_experiment_persuasion — Experiment persuasion gate (POST; S gate shifted left · per concern)

> **This is not a free-form prompt—it reuses the frozen `consensus_gate` and is fully isomorphic to the r7 raise gate.** The orchestrator runs it in Python
> (`orchestrate.experiment_persuasion`), without improvisation. **This gate adds no new bar**: it moves the r7 `bar_met`
> earlier and asks again, per concern, about the **actual experimental results**.

## What it answers (and how responsibilities are divided with r4_accept)
- **r4_accept(X1-X6) = whether the experiment is honest** (actually run, with no fabrication). Passing it proves only that the numbers are credible.
- **This gate = whether the experiment is persuasive** (whether the actual results resolve the concern they serve, at the strength required by that reviewer's zone bar).
- An experiment can pass all of X1-X6 (real data and genuine rerun) yet be **null / double-edged / aimed away from the real concern**—honest but unpersuasive.
  Such a result **must never be presented as a strength** (= b3 ammunition C/C2/D); it must be reframed as a lower bound or honest concession **before** r6 writing.

## Inputs (read-only)
- `campaigns/{{SLUG}}/experiments/<expid>/ACCEPTANCE.json` — process only experiments with `verdict ∈ {ACCEPT, PARTIAL}`;
  use their `serves` (for example, the list `"vCzF-W4 (long free-form CoT generalization)"`) to identify the served (reviewer, concern).
- `results.json` in the same directory — use only `derived`'s **actual numbers** + `headline`/`interpretation` (the runner's honest interpretation, not optimized for persuasion).
- `campaigns/{{SLUG}}/REBUTTAL_CARD.json` — each reviewer's `initial_overall` (determines the zone bar).
- `campaigns/{{SLUG}}/ledger/concern_ledger.json` (if present)—use `real_concern` to enrich the concern text.
- Frozen machinery: `rebuttal_verifier/consensus_gate.py` (`deepseek_judge` / `codex_prompt` / `parse_codex` / `bar_met` / `consensus`).

## Mechanism (for each served (reviewer, concern), isomorphic to r7 **zone routing**)
1. **Construct an honest stub (use only actual numbers, with no polishing)**: concatenate the reviewer's original wording of the concern + the actual results from `results.json.derived` into a
   minimal stub ("Reviewer concern: … / We ran an experiment and observed: <actual derived> / Acceptance: X1-X6 …").
   **The orchestrator assembles the stub deterministically from a template; no LLM may write it freely** (to prevent inflating weak results into strong ones).
2. **Narrow the case by concern**: the `review` field = **the original wording of that concern** (not the entire review), so `bar_met` judges
   "whether this evidence resolves **this one** concern", not "whether the entire rebuttal is complete". `initial_overall` = that reviewer's OA.
3. **Judge via zone routing (a strict mirror of r7's `consensus`)**: `primary_judge` determines who is the primary judge—
   **OA=3 border → `authoritative`, Codex is the primary judge (**always call Codex**, while DeepSeek retains veto power only)**; OA≤2/≥4 → `strict`, both families must clear.
   ⚠️ **At OA=3, never allow weak DeepSeek cheap-reject to decide unilaterally** (that is the zone where README §7 says DeepSeek is weakest and r7 deliberately makes Codex the primary judge);
   only in the **strict zone** (non-OA=3) is DeepSeek an equal family, and only there is its failure to clear the bar a valid cheap-reject. The judge model **must ≠ the writer**.

## Criteria (three levels, determined by the **zone's primary judge**, no longer unilaterally by DeepSeek)
| verdict | condition (`consensus` ground-truth fields, `prim_ok` = whether the primary judge for that zone clears) | downstream |
|---|---|---|
| **STRENGTH** | `consensus.stop == True` (consensus clears under zone routing) | r5 records `met`; r6 writes it as a **direct answer** |
| **LOWER_BOUND** | no stop, but **the primary judge clears** (vetoed by the other family / only one clears under strict) | r5 records `partial` + `framing_hint`; r6 writes an **honest lower bound**, with no generalized overclaim |
| **CONCEDE** | **the authoritative judge serving as the primary judge for that zone does not clear it either** (OA=3 = Codex does not clear) | r5 records `unmet` (even if X1-X6 ACCEPT); r6 uses the warrant fallback ladder to concede, and **must not present it as a strength** |
- When the verdict is not STRENGTH, write the primary judge's `why_not_persuasive` (blocker/veto/reasoning) + `judge_advice` into PERSUASION.json, and feed them to the **redesign planner** to produce "why + how to redesign".
- Judge engine failure (`__CODEX_ERROR__`/`__TIMEOUT__`) → conservatively judge `LOWER_BOUND`; **never give away STRENGTH merely because the engine failed**.
- If the reviewer/OA in serves cannot be parsed → record a warning and skip that target (do not silently mark it met).

## Position in the loop
This gate is the **stopping criterion in `EXPERIMENT_LOOP.md`**: `STRENGTH → stop (WON)`; non-STRENGTH → drive `r4_experiment_redesign` to redesign and rerun, and upon max_iter/infeasibility → honest concession.

## `framing_hint` (v0.4 response argument compilation language, fed to r6)
- **STRENGTH** → "**Answer the concern literally and directly**: use completed-action wording ('we ran X and observed Y') + mirror its subject-verb-object structure, with no hedge."
- **LOWER_BOUND** → "The evidence supports only a **bounded** claim: state the lower bound honestly, and **do not** generalize it into 'stable/robust/in general' (= b3 ammunition, see 02-judgeswap);
  use past tense for what was run, and 'In the camera-ready we will …' for manuscript changes."
- **CONCEDE** → "This result **does not resolve** the concern and **must not be presented as a strength** (= b3 ammunition C/D). Use move-6 of the warrant fallback ladder:
  state the limitation **once** as a **positive technical scope condition**, then close; add 'In the camera-ready we will …' only for legitimate edits."

## Output (write this exact file)
`campaigns/{{SLUG}}/experiments/<expid>/PERSUASION.json`:
```json
{ "expid":"...", "acceptance":"ACCEPT|PARTIAL", "overall":"STRENGTH|PARTIAL|CONCEDE|NONE",
  "targets":[ { "reviewer":"vCzF", "concern":"W4", "serves":"vCzF-W4 (...)", "oa":3,
                "verdict":"STRENGTH|LOWER_BOUND|CONCEDE", "framing_hint":"…",
                "deepseek_ok":true, "codex_verdict":"raise|same|lower|null", "judge_error":null } ],
  "gate":"<GATE_SHA>" }
```

## DO-NOT (hard)
- Add no new bar: zone-strength criteria must use only `consensus_gate.bar_met` (the single source of truth; changing the criteria still requires the same three changes in those three places).
- Do not let an LLM freely write the stub; the stub contains only actual `derived` numbers + the concern's original wording.
- Judge ≠ writer; the stopping-criterion judgment still uses the cross-family consensus gate (fitting to Codex alone does not count as STRENGTH).
- For CONCEDE/LOWER_BOUND, experimental **results remain on disk and auditable**; they simply do not enter the evidence pool as "evidence that clears the concern".
