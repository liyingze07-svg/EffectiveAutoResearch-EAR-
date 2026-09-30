#!/usr/bin/env python3
"""M1 cost summary —— read campaigns/*/ledger/cost.jsonl and produce an actionable cost profile.

  python3 scripts/cost_report.py                 all campaigns
  python3 scripts/cost_report.py --slug RIVET     one paper
  python3 scripts/cost_report.py --by unit        aggregate by reviewer/target

The focus is not "how much was spent," but **where the leverage is**:
  · DRIVE/ACQUIT mix   —— each writer's vs judge's share (if judges dominate, M4 cascade-threshold tuning offers large gains)
  · cheap_reject rate     —— how many expensive authoritative judge calls the cheap gate blocked (the actual effect of the current heuristic)
  · cache_hit rate        —— number of times the engine was not called at all
  · cached_in share      —— how much the prompt cache captured (codex has empirically reached 78%, yielding savings at no cost)
Modify PRICES as needed; if left empty, report only token usage and wall-clock time, without estimating cost.
"""
import os, sys, json, glob, argparse
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# USD / 1M token. Leave as None = do not estimate the cost of this model (report token usage only). Adjust according to the actual bill.
PRICES = {
    # "gpt-5.6-sol": {"in": 1.25, "cached_in": 0.125, "out": 10.0},
    # "deepseek-v4-pro": {"in": 0.27, "cached_in": 0.07, "out": 1.10},
}


def load(slug=None):
    pat = os.path.join(ROOT, "campaigns", slug or "*", "ledger", "cost.jsonl")
    rows = []
    for f in sorted(glob.glob(pat)):
        for ln in open(f):
            ln = ln.strip()
            if ln:
                try:
                    rows.append(json.loads(ln))
                except Exception:
                    pass
    return rows


def money(r):
    pr = PRICES.get(r.get("model") or "")
    if not pr:
        return None
    it, ot, ct = r.get("in_tok") or 0, r.get("out_tok") or 0, r.get("cached_in_tok") or 0
    fresh = max(it - ct, 0)
    return (fresh * pr["in"] + ct * pr.get("cached_in", pr["in"]) + ot * pr["out"]) / 1e6


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug")
    ap.add_argument("--by", default="stage", choices=["stage", "unit", "model", "role"])
    a = ap.parse_args()

    rows = load(a.slug)
    if not rows:
        print("The ledger is empty. The pipeline has not run since instrumentation —— this is the expected initial state for M1.")
        print(f"  Expected path: campaigns/{a.slug or '<slug>'}/ledger/cost.jsonl")
        return

    g = defaultdict(lambda: {"n": 0, "wall": 0.0, "in": 0, "out": 0, "cin": 0,
                             "cheap": 0, "cache": 0, "err": 0, "usd": 0.0, "usd_known": 0})
    tot = dict(n=0, wall=0.0, cheap=0, cache=0, err=0)
    for r in rows:
        k = r.get(a.by) or "(empty)"
        d = g[k]
        d["n"] += 1
        d["wall"] += r.get("wall_s") or 0
        d["in"] += r.get("in_tok") or 0
        d["out"] += r.get("out_tok") or 0
        d["cin"] += r.get("cached_in_tok") or 0
        d["cheap"] += 1 if r.get("cheap_reject") else 0
        d["cache"] += 1 if r.get("cache_hit") else 0
        d["err"] += 1 if r.get("err") else 0
        m = money(r)
        if m is not None:
            d["usd"] += m
            d["usd_known"] += 1
        tot["n"] += 1
        tot["wall"] += r.get("wall_s") or 0
        tot["cheap"] += 1 if r.get("cheap_reject") else 0
        tot["cache"] += 1 if r.get("cache_hit") else 0
        tot["err"] += 1 if r.get("err") else 0

    w = max(len(str(k)) for k in g) + 2
    print(f"\nCost profile  ({tot['n']} calls, aggregated by {a.by}"
          f"{', slug=' + a.slug if a.slug else ', all campaigns'})\n")
    hdr = f"{'':{w}}{'calls':>6}{'wall h':>8}{'in_tok':>11}{'out_tok':>10}{'cached in%':>9}{'cheap rejects':>7}{'cache skips':>7}{'failures':>6}"
    if PRICES:
        hdr += f"{'USD':>9}"
    print(hdr)
    print("-" * len(hdr))
    for k, d in sorted(g.items(), key=lambda kv: -kv[1]["n"]):
        cr = f"{100*d['cin']/d['in']:.0f}%" if d["in"] else "-"
        line = (f"{k:{w}}{d['n']:>6}{d['wall']/3600:>8.2f}{d['in']:>11,}{d['out']:>10,}"
                f"{cr:>9}{d['cheap']:>7}{d['cache']:>7}{d['err']:>6}")
        if PRICES:
            line += f"{d['usd']:>9.2f}" if d["usd_known"] else f"{'n/a':>9}"
        print(line)

    print("\nLeverage metrics")
    roles = defaultdict(int)
    for r in rows:
        roles[r.get("role") or "?"] += 1
    drive, acq = roles.get("DRIVE", 0), roles.get("ACQUIT", 0)
    # ★Use token count rather than call count —— call count is seriously misleading: empirically, writers use 447k in/call,
    # while judges use 16k in/call (a ~27-fold difference); judges account for most calls, but writers account for 94% of the cost.
    tok = defaultdict(int)
    for r in rows:
        tok[r.get("role") or "?"] += (r.get("in_tok") or 0) + (r.get("out_tok") or 0)
    dt, at = tok.get("DRIVE", 0), tok.get("ACQUIT", 0)
    if drive + acq:
        print(f"  DRIVE/ACQUIT calls   {drive} / {acq}  (judges account for {100*acq/(drive+acq):.0f}% of calls)")
    if dt + at:
        who = "writers" if dt > at else "judges"
        print(f"  DRIVE/ACQUIT token    {dt:,} / {at:,}"
              f"  ({who} account for {100*max(dt,at)/(dt+at):.0f}% of token usage ← this is the cost center)")
        if drive and acq:
            print(f"  token per call        writers {dt//max(drive,1):,} · judges {at//max(acq,1):,}"
                  f"  ({max(dt//max(drive,1),1)/max(at//max(acq,1),1):.0f}× difference)")
    print(f"  cheap_reject rate      {tot['cheap']}/{tot['n']} = {100*tot['cheap']/tot['n']:.1f}%"
          f"   (each one = one fewer authoritative Codex judge call)")
    print(f"  cache_hit rate         {tot['cache']}/{tot['n']} = {100*tot['cache']/tot['n']:.1f}%"
          f"   (each one = the entire engine call did not occur)")
    if tot["err"]:
        print(f"  ⚠ failures/timeouts          {tot['err']} occurrences —— pure waste; M4 must monitor this specifically")
    ci = sum(r.get("cached_in_tok") or 0 for r in rows)
    ti = sum(r.get("in_tok") or 0 for r in rows)
    if ti:
        print(f"  prompt cache coverage      {100*ci/ti:.0f}% of input token")
    if not PRICES:
        print("\n  (no price table configured → report token usage/wall-clock time only. To report monetary cost, fill in PRICES in scripts/cost_report.py)")


if __name__ == "__main__":
    main()
