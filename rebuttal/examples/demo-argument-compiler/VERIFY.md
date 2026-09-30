# VERIFY — demo-argument-compiler (Independent Verifier)

**After the writer self-reports done, run this file in a separate new window (physically isolated from the writer).** You are the independent verifier: independently re-verify this campaign against the frozen `SPEC.md`, and issue the binding verdict `ledger/ACQUITTAL.json` (ACQUIT or REJECT+reasons). **You do not write the rebuttal, revise the draft, soften the SPEC, or consider the writer's self-reported "verified" status—you only verify independently; you also do not change the raise gate configuration.**

**First action**: `ToolSearch select:mcp__codex__codex,mcp__codex__codex-reply,mcp__deepseek__chat`. Read `SPEC.md`, `REBUTTAL_CARD.json`, the final draft `drafts/final_rebuttal.md`, `inputs/reviews/`, and `ledger/` (evidence_map / concern_ledger / round*-gate.json).

## Item-by-item verification (against the SPEC, redo everything independently)
1. **A·raise gate (cross-family consensus gate)**: **Independently rerun the raise gate yourself**—using the frozen θ₀ in `$AUTOREBUTTAL_ROOT/harness/shared-assets/verifier/`, invoke DeepSeek V4 Pro and Codex once each on the final draft for every P0 reviewer (the persona includes initial_rating+subscores+confidence; **never feed it the final label**). Require **both DeepSeek and Codex to return `raise` for every P0 reviewer**. If either judge does not raise for any P0 → A fails (unless the honest concession exit is used). **Do not trust the writer's self-reported scores in round*-gate.json; score them again yourself.**
2. **B·coverage**: Check each P0/P1 concern against the final draft to verify that it is explicitly addressed. Any omission → REJECT.
3. **C·evidence honesty**: Spot-check every number/citation/claim in the final draft. Use `recompute_check` to recompute numbers included in the body, with <1% error (if any formula does not match raw → REJECT); independently verify the existence+relevance of every citation (fabricated citation → REJECT); ensure every "the paper has shown/we did" statement can be traced to evidence (presented as completed without support → REJECT). For quantities such as theoretical constants that have no raw formula, SKIP; do not count them as failures.
4. **D·no ammunition+no new attack surface**: Final-draft ammunition grep (`$AUTOREBUTTAL_ROOT/harness/shared-assets/ammunition-checklist.md`) = 0; independently read it once to check whether responding to A opens a new weakness B that was not raised; length ≤ per-reviewer 5000 chars; no `[TBD]` in the body.
5. **E·independence self-check**: You did not reuse the writer's gate-score conclusions; the persona in your gate calls was not filtered by the writer and did not leak the label. **iteration-cap=4** (the writer gets at most 4 rounds; you verify only the terminal state and do not iterate for the writer).

## Issue the verdict
Write `ledger/ACQUITTAL.json`:
```
{ "verdict": "ACQUIT|REJECT",
  "track": "raise|honest-concede",
  "A_consensus_raise": {"R1":{"deepseek":"raise|same|lower","codex":"raise|same|lower"}, ...},
  "A_all_p0_raise": <bool>,
  "B_coverage_ok": <bool>, "B_missed_concerns": ["..."],
  "C_recompute_max_relerr": <float>, "C_fake_citations": <int>, "C_unsupported_claims": <int>,
  "D_ammo_hits": <int>, "D_new_attack_surface": <bool>, "D_over_wordlimit": <bool>,
  "reasons": ["..."] }
```
**ACQUIT ⇔ A (cross-family consensus to raise for all P0 reviewers) ∧ B (complete coverage) ∧ C (evidence honesty) ∧ D (zero ammunition and no new attack surface) ∧ E (independence).**
**Block only substantive fabrication** (numbers do not match raw / citations do not exist / a claim is presented as completed without support / ammunition>0); minor differences in protocol wording are not fatal; simply flag them for correction.

**Honest concession exit**: If consensus to raise still cannot be reached after 4 rounds, but B/C/D/E all pass and this is the most honest concession-style rebuttal → `{"verdict":"ACQUIT","track":"honest-concede","A_all_p0_raise":false}`.

Your verdict is the final judgment for this campaign.
