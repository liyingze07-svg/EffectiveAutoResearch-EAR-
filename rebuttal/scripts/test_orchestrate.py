#!/usr/bin/env python3
"""Production pure-function unit tests — zero API cost; runnable at any time after changing judges or budgets.

  python3 scripts/test_orchestrate.py

Why this exists: this project has repeatedly stumbled over **silent failures** (truncation, fallback, and defaults masking missing values).
These bugs raise no errors and manifest only as "poor results." Any pure-function behavior that can be pinned down with assertions must be pinned down.

Real bugs already caught:
  · The join_budget budget became insufficient after B3 changed to union-of-3 (5-6 hits → 12 items / 4305 characters),
    because two changes interacted, and merely increasing the budget still could not fit everything → leading to the "blocking categories first" design.
"""
import sys, os, json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(ROOT, "harness", "runner"))
sys.argv = ["test"]
import orchestrate as o          # noqa: E402
import cost                       # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"  {'✓' if cond else '🔴'} {name}{('  ' + detail) if detail and not cond else ''}")


# ---- join_budget:carry-forward feedback channel ------------------------------------
def t_join_budget():
    print("\n[join_budget] Whether judge feedback can be passed intact to the next round")
    items = ["a" * 100, "b" * 100, "c" * 100]
    msgs = []
    got = o.join_budget(items, 1000, "T", logger=msgs.append)
    check("When the budget is sufficient, include everything without warning", got.count("a" * 100) == 1 and len(msgs) == 0)
    msgs.clear()
    got = o.join_budget(items, 150, "T", logger=msgs.append)
    check("When the budget is insufficient, a warning must be emitted (never discard silently)",
          len(msgs) == 1 and "feedback exceeds budget" in msgs[0]
          and "2/3" in msgs[0] and "budget=150" in msgs[0])
    check("When over budget, still include what fits", got.count("a" * 100) == 1)
    msgs.clear()
    check("Empty items are skipped", o.join_budget(["", "  ", "x"], 100, "T", logger=msgs.append) == "x")


# ---- B3 verdict:must be computed in code from the explicit category table,ignoring the judge's self-reported verdict ------------------------
def t_b3_verdict():
    print("\n[B3 verdict] Compute from the category table in code, without relying on the judge's self-reported verdict")
    check("The blocking-category set matches stage prompt §2/§6",
          o.B3_BLOCKING == {"A", "B", "B2", "C", "C2", "D", "E"})
    check("Advisory categories do not block", o.B3_ADVISORY == {"deletable", "not_direct"})
    check("Advisory and blocking categories do not overlap", not (o.B3_BLOCKING & o.B3_ADVISORY))
    k1 = o._b3_key({"category": "D", "quote": "Hello   World"})
    k2 = o._b3_key({"category": "D", "quote": "hello world"})
    check("The hit deduplication key normalizes whitespace/case", k1 == k2)
    k3 = o._b3_key({"category": "A", "quote": "Hello World"})
    check("Different categories are not deduplicated", k1 != k3)


# ---- Real B3 artifact:all blocking categories must enter the seed --------------------------------------
def t_real_b3_feedback():
    print("\n[Real B3 artifact] All blocking-category hits must enter the carry-forward seed")
    p = f"{ROOT}/campaigns/01-wdData/ledger/B3_37ch_ammunition.json"
    if not os.path.exists(p):
        print("  - Skip (no sample)"); return
    hits = json.load(open(p)).get("hits") or []
    srt = sorted(hits, key=lambda h: 0 if str(h.get("category", "")).strip() in o.B3_BLOCKING else 1)
    items = [f'"{h.get("quote","")}" -> {h.get("rewrite","")}' for h in srt]
    nblock = sum(1 for h in hits if str(h.get("category", "")).strip() in o.B3_BLOCKING)
    got = o.join_budget(items, 6000, "B3", logger=lambda m: None)
    check(f"The 6000 budget includes all {len(items)} items", got.count('" -> ') == len(items))
    # Even when the budget is reduced, blocking categories must still enter first
    tight = o.join_budget(items, 1200, "B3", logger=lambda m: None)
    kept_block = sum(1 for i in items[:nblock] if i in tight)
    check("When the budget is reduced, blocking categories take priority (they cannot be displaced by advisory categories)", kept_block >= 1 and
          all(i in tight for i in items[:kept_block]))


# ---- Strategy ladder ---------------------------------------------------------------
def t_ladder():
    print("\n[Strategy ladder] route_strategies")
    strats = [{"id": "s3_multistage"}, {"id": "s1_evidence_locked"}, {"id": "s2_persuasion"}]
    lad = [s["id"] for s in o.route_strategies(strats, {"initial_overall": 3})]
    check("Sort by MANIFEST.route, with s1 first", lad[0] == "s1_evidence_locked")
    check("The ladder covers all strategies (unlisted ones are appended as fallback)", set(lad) == {s["id"] for s in strats})


# ---- cost:usage parsing --------------------------------------------------------
def t_cost():
    print("\n[cost] codex usage parsing")
    ev = ('{"type":"turn.completed","usage":{"input_tokens":100,"cached_input_tokens":80,'
          '"output_tokens":5,"reasoning_output_tokens":1}}')
    u = cost.parse_codex_usage(ev)
    check("Parse a single turn", u["in_tok"] == 100 and u["cached_in_tok"] == 80)
    check("Accumulate multiple turns", cost.parse_codex_usage(ev + "\n" + ev)["in_tok"] == 200)
    check("If unavailable, all values are None (the caller falls back to wall)",
          cost.parse_codex_usage("garbage")["in_tok"] is None)


for t in (t_join_budget, t_b3_verdict, t_real_b3_feedback, t_ladder, t_cost):
    t()
print(f"\n{'='*52}\nPassed {len(PASS)} · Failed {len(FAIL)}")
if FAIL:
    print("Failed items:", FAIL)
sys.exit(1 if FAIL else 0)
