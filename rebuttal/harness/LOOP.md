# LOOP.md — Explicit loop protocol (goal mode)

> The per-reviewer r6→r7 loop. The engine follows this **exact step sequence** and does not improvise. For the stopping criterion see `GOAL.md`.

## The loop, per reviewer

```
seed = None                                   # carry-forward seed (last round's best + advice)
best_ever = None
for round in 1..max_iter:                     # max_iter comes from the card, default 4
  # ① MoE generation: one draft per strategy (engine-agnostic, reads strategies/MANIFEST.json)
  drafts = [ engine(stages/r6_write.md, {reviewer, strategy: s, seed}) for s in MANIFEST ]
  # ② Cheap gate: ammunition grep + DeepSeek judge, take the highest
  for d in drafts: d.ammo = ammo_hits(d); d.ds = deepseek_judge(case(reviewer, d))
  best = argmax(drafts, key=rank)             # bar_met > rp=high > fewer ammo > reaction
  if best.ammo != []: seed = carry(best, "remove ammunition: "+best.ammo); continue  # cheap reject, no Codex
  if not bar_met(best.ds): seed = carry(best, best.ds.advice); continue              # DeepSeek did not clear
  # ③ Authoritative gate: Codex (high reasoning, zone-routed), called only after the cheap gate passes
  codex = codex_judge(case(reviewer, best))
  con = consensus(best.ds, codex, case)       # authoritative (OA=3) / strict (all other zones)
  if con.stop and best.ammo == []:
     record(reviewer, best, "PASS"); break     # cleared, leave this reviewer's loop
  best_ever = better(best_ever, best)
  seed = carry(best, con.advice)               # ④ carry-forward: best draft + judge advice + phrases to avoid
else:
  record(reviewer, best_ever, "HONEST_CONCEDE")   # rounds exhausted → honest concession
```

## Carry-forward seed (input to the next round's r6_write)

```json
{ "prior_best_rebuttal": "<last round's best text>",
  "blocker": "<blocker reported by the gate>",
  "apply_advice": "<advice reported by the gate>",
  "avoid_phrases": ["<ammunition phrasing that leaked last round>"] }
```

The next round **edits `prior_best`** — keep what worked, add what the advice asks for, delete what must be avoided. It does not rewrite from scratch.

## Four built-in protections (against laziness, criterion-fitting, waste and oscillation)

1. **Cheap gate first**: never spend the expensive Codex judge on a draft that failed the ammunition check or DeepSeek.
2. **Judge feedback drives the rewrite**: advice and avoid-phrases are fed back; the loop does not reroll wording and hope.
3. **Best-so-far** prevents oscillation (do not make a passing draft worse).
4. **max_iter → honest concession**, rather than fitting the criterion indefinitely.

## Routing (which stage the advice sends you back to when a gate fails)

| Type of advice from the gate | Go back to |
|---|---|
| Insufficient evidence / data needed | r4 (run a real experiment, cite literature, or move down the warrant ladder) |
| Weak logic / missed the point | r6 (rebuild the argument DAG) |
| Misread the concern | r2 (re-diagnose) |
