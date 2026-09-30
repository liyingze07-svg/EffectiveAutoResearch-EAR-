#!/usr/bin/env python3
"""M2a cascade replayer —— at zero API cost, computes "how much can be saved by switching cascade strategies" from existing judge predictions.

Corpus:the same batch of cases was judged by multiple models using **the same frozen prompt** (data/preds_*.jsonl),
with gold from data/threads.jsonl. This is **paired** data —— it supports computing inter-model agreement,
and agreement is exactly what matters for a cascade:when the cheap tier and expensive tier agree closely, most expensive-tier calls are wasted.

Criterion convention:the stopping criterion asks "is this rebuttal good enough?". Here, the zone bar for the low-start partition
(`reaction == 'raise'`) is modeled,where gold=raise means "should have cleared the gate".
  FP = false clearance(a weak draft clears the gate)—— the α that must be constrained
  FN = false rejection(a good draft is blocked)—— the cost is one extra round,spending money but not reputation

Cost unit:one cheap judge call = 1. The expensive/cheap price ratio r is unknown(no historical token records),
so **sweep a set of r values and report the results**,without pretending to know the exact price. The true value of r will come from the M1 ledger.

  python3 scripts/cascade_replay.py
  python3 scripts/cascade_replay.py --alpha 0.10
"""
import os, json, argparse, random
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
D = os.path.join(ROOT, "data")

MODELS = {           # file -> (display name, tier:cheap/mid/exp)
    "preds_deepseek-v4-flash.jsonl": ("deepseek-flash", "cheap"),
    "preds_deepseek-v4-pro.jsonl":   ("deepseek-pro",   "mid"),
    "preds_codex.jsonl":             ("codex",          "exp"),
    "preds_opus36.jsonl":            ("opus-3.6",       "exp"),
    "preds_sonnet36.jsonl":          ("sonnet-3.6",     "mid"),
}


def load():
    gold = {}
    for ln in open(os.path.join(D, "threads.jsonl")):
        d = json.loads(ln)
        gold[d["note_id"]] = d.get("label")
    preds = {}
    for fn, (name, tier) in MODELS.items():
        p = os.path.join(D, fn)
        if not os.path.exists(p):
            continue
        m = {}
        for ln in open(p):
            d = json.loads(ln)
            if d.get("note_id") in gold:
                m[d["note_id"]] = str(d.get("reaction", "")).strip().lower()
        preds[name] = (m, tier)
    return gold, preds


def boot_ci(vals, n=2000, seed=7):
    if not vals:
        return (None, None)
    rnd = random.Random(seed)
    ms = []
    for _ in range(n):
        s = [vals[rnd.randrange(len(vals))] for _ in vals]
        ms.append(sum(s) / len(s))
    ms.sort()
    return (ms[int(0.025 * n)], ms[int(0.975 * n)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alpha", type=float, default=0.15, help="maximum acceptable false-clearance rate")
    a = ap.parse_args()
    gold, preds = load()

    # Shared case set(judged by all three tiers)——cascades must be compared on the same batch of cases
    core = ["deepseek-flash", "deepseek-pro", "codex"]
    ids = sorted(set.intersection(*[set(preds[m][0]) for m in core if m in preds]))
    print(f"\nCorpus:{len(ids)} cases were all judged by {', '.join(core)}"
          f"(gold: raise {sum(1 for i in ids if gold[i]=='raise')} / "
          f"non-raise {sum(1 for i in ids if gold[i]!='raise')})")
    if len(ids) < 100:
        print(f"⚠ n={len(ids)} is small —— all point estimates below include a 95% bootstrap CI,"
              f"and a wide CI means the conclusion cannot yet serve as a basis for decisions.")

    # ── Single-model performance ────────────────────────────────────────────────
    print("\n【Single-judge performance】(on the shared set;raise = clear the gate)\n")
    print(f"{'Judge':16}{'Tier':>5}{'Accuracy':>10}{'95% CI':>18}{'False clear FP':>10}{'False reject FN':>10}")
    print("-" * 70)
    for name, (m, tier) in preds.items():
        sub = [i for i in ids if i in m]
        if len(sub) < len(ids):
            continue
        corr, fp, fn = [], 0, 0
        for i in sub:
            say = m[i] == "raise"
            truth = gold[i] == "raise"
            corr.append(1 if say == truth else 0)
            fp += 1 if (say and not truth) else 0
            fn += 1 if (not say and truth) else 0
        acc = sum(corr) / len(corr)
        lo, hi = boot_ci(corr)
        print(f"{name:16}{tier:>5}{acc:>10.3f}{f'[{lo:.2f},{hi:.2f}]':>18}"
              f"{fp:>10}{fn:>10}")

    # ── Pairwise agreement(the physical basis of a cascade)────────────────────────────────
    print("\n【Pairwise agreement】—— the more the cheap tier agrees with the expensive tier,the more expensive-tier calls are wasted\n")
    names = [n for n in preds if all(i in preds[n][0] for i in ids)]
    for i1 in range(len(names)):
        for i2 in range(i1 + 1, len(names)):
            A, B = names[i1], names[i2]
            ag = [1 if (preds[A][0][i] == "raise") == (preds[B][0][i] == "raise") else 0
                  for i in ids]
            lo, hi = boot_ci(ag)
            print(f"  {A:16} vs {B:16} agree {sum(ag)}/{len(ag)} = "
                  f"{sum(ag)/len(ag):.1%}  CI[{lo:.1%},{hi:.1%}]")

    # ── Cascade strategy simulation ──────────────────────────────────────────────
    # Strategy = ordered tier chain + strict consensus(every tier in the chain must say raise to clear the gate;
    # if any tier says not raise,short-circuit immediately,and subsequent tiers are **not called** = save money)
    POLICIES = {
        "P0 current cheap-first (pro→codex)": ["deepseek-pro", "codex"],
        "P1 three tiers (flash→pro→codex)":       ["deepseek-flash", "deepseek-pro", "codex"],
        "P2 replace cheap tier with flash (flash→codex)":  ["deepseek-flash", "codex"],
        "P3 codex only":                    ["codex"],
        "P4 pro only":                      ["deepseek-pro"],
    }
    TIER_UNIT = {"cheap": 0.2, "mid": 1.0, "exp": None}   # parameterize exp with r

    print("\n【Cascade strategy simulation】strict consensus:every tier in the chain must say raise to clear the gate,"
          "and a no from any tier short-circuits the chain(subsequent tiers are not called)\n")
    for r in (2, 5, 10, 20):
        print(f"  ── Expensive/cheap price ratio r = {r}(each exp-tier call counts as {r},mid=1,cheap=0.2)──")
        print(f"  {'Strategy':36}{'E[Cost]':>10}{'Saved%':>8}{'False clear':>8}{'False reject':>8}{'Accuracy':>9}")
        base = None
        for label, chain in POLICIES.items():
            if not all(c in preds for c in chain):
                continue
            cost_t, fp, fn, corr = 0.0, 0, 0, []
            for i in ids:
                stop = True
                for c in chain:
                    tier = preds[c][1]
                    cost_t += r if tier == "exp" else TIER_UNIT[tier]
                    if preds[c][0][i] != "raise":
                        stop = False
                        break                     # Short-circuit:subsequent tiers are not called
                truth = gold[i] == "raise"
                corr.append(1 if stop == truth else 0)
                fp += 1 if (stop and not truth) else 0
                fn += 1 if (not stop and truth) else 0
            ec = cost_t / len(ids)
            if base is None:
                base = ec
            save = 100 * (base - ec) / base
            flag = "  ⚠exceeds α" if fp / len(ids) > a.alpha else ""
            print(f"  {label:36}{ec:>10.2f}{save:>7.0f}%{fp:>8}{fn:>8}"
                  f"{sum(corr)/len(corr):>9.3f}{flag}")
        print()

    print(f"How to read this:α={a.alpha:.0%} is the maximum acceptable false-clearance rate."
          f"A strategy that saves money but exceeds α is unusable —— false clearance means a weak draft clears the gate,which costs reputation,not money.")
    print("Substitute the true value of r after the M1 ledger has accumulated enough data(one codex call is known to be ≈12.7k in / 78% cached).")


if __name__ == "__main__":
    main()
