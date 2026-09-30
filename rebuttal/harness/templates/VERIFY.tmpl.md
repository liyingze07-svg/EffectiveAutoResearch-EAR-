# VERIFY — {{SLUG}} (Independent Verifier)

**After the writer self-reports done, run this file in a separate new window (physically isolated from the writer).** You are the independent verifier: independently re-verify this campaign against the frozen `SPEC.md`, and issue the binding verdict `ledger/ACQUITTAL.json` (ACQUIT or REJECT+reasons). **You do not write the rebuttal, revise the draft, soften the SPEC, or consider the writer's self-report that it is "verified"—you only verify independently; you also do not modify the raise gate configuration.**

**First action**: `ToolSearch select:mcp__codex__codex,mcp__codex__codex-reply,mcp__deepseek__chat`. Read `SPEC.md`, `REBUTTAL_CARD.json`, the final draft `drafts/final_rebuttal.md`, `inputs/reviews/`, and `ledger/` (evidence_map / concern_ledger / round*-gate.json).

## Item-by-Item Verification (Against the SPEC, Independently Redo Everything)
1. **A·Raise (cross-family consensus gate)**: **Independently rerun the raise gate yourself**—using the frozen θ₀ in `{{HARNESS_DIR}}/shared-assets/verifier/`, call DeepSeek V4 Pro and Codex once each on the final draft for every P0 reviewer (the persona includes initial_rating+subscores+confidence; **never feed it the final label**). Require **both DeepSeek and Codex to return `raise` for every P0 reviewer**. If either judge does not raise on any P0 → A fails (unless the honest concession exit is used). **Do not trust the scores self-reported by the writer in round*-gate.json; score them again yourself.**
2. **B·Coverage**: Check each P0/P1 concern individually to confirm that the final draft addresses it explicitly. Any omission → REJECT.
3. **C·Evidence Honesty**: Spot-check every number/citation/claim in the final draft. `recompute_check` must recompute numbers included in the main text to <1% (if any calculation does not match the raw data → REJECT); independently verify every citation for existence+relevance (fabricated citation → REJECT); every "the paper has demonstrated/we did" statement must be traceable to evidence (claiming unsupported work as completed → REJECT). SKIP quantities such as theoretical constants that have no raw calculation; they do not count as failures.
4. **D·No Ammunition+No New Attack Surface**: The final-draft ammunition grep (`{{HARNESS_DIR}}/shared-assets/ammunition-checklist.md`) = 0; independently read it once to check whether responding to A has opened a new weakness not raised by B; word count ≤ {{WORD_LIMIT}}; no `[TBD]` in the main text.
5. **E·Independence Self-Check**: You did not reuse the writer's gate-score conclusions; the persona in your gate calls was not filtered by the writer and did not leak the label. **iteration-cap={{MAX_ITER}}** (the writer gets at most {{MAX_ITER}} rounds; you only verify the final state and do not iterate on its behalf).

## Issue the Verdict
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
**ACQUIT ⇔ A (cross-family consensus is raise for every P0) ∧ B (complete coverage) ∧ C (evidence honesty) ∧ D (zero ammunition and no new attack surface) ∧ E (independence).**
**Block only actual fabrication** (numbers do not match the raw data / citations do not exist / an unsupported claim is presented as completed / ammunition>0); minor discrepancies in protocol wording are not fatal—simply flag them for correction.

**Honest concession exit**: If cross-family consensus still cannot be reached on raise after {{MAX_ITER}} rounds, but B/C/D/E all pass and this is the most honest concession-style rebuttal → `{"verdict":"ACQUIT","track":"honest-concede","A_all_p0_raise":false}`.

Your verdict is the final judgment for this campaign.
