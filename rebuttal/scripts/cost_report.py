#!/usr/bin/env python3
"""M1 成本汇总 —— 读 campaigns/*/ledger/cost.jsonl,出可行动的成本画像。

  python3 scripts/cost_report.py                 全部 campaign
  python3 scripts/cost_report.py --slug RIVET     单篇
  python3 scripts/cost_report.py --by unit        按 reviewer/靶 归集

重点不是"花了多少钱",而是**杠杆在哪**:
  · DRIVE/ACQUIT 配比   —— 写手 vs 判官各占多少(判官占大头则 M4 级联阈值收益大)
  · cheap_reject 率     —— 便宜门拦掉了多少次贵判官调用(现行启发式的实际效果)
  · cache_hit 率        —— 完全没调引擎的次数
  · cached_in 占比      —— prompt 缓存吃到多少(codex 实测可达 78%,是白捡的省钱)
价格表按需改 PRICES;留空则只报 token 与墙钟,不猜钱。
"""
import os, sys, json, glob, argparse
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# USD / 1M token。留 None = 该模型不估价(只报 token)。自己按实际账单改。
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
        print("账本为空。产线还没在插桩后跑过 —— 这是 M1 的预期初始状态。")
        print(f"  期望路径: campaigns/{a.slug or '<slug>'}/ledger/cost.jsonl")
        return

    g = defaultdict(lambda: {"n": 0, "wall": 0.0, "in": 0, "out": 0, "cin": 0,
                             "cheap": 0, "cache": 0, "err": 0, "usd": 0.0, "usd_known": 0})
    tot = dict(n=0, wall=0.0, cheap=0, cache=0, err=0)
    for r in rows:
        k = r.get(a.by) or "(空)"
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
    print(f"\n成本画像  ({tot['n']} 次调用, 按 {a.by} 归集"
          f"{', slug=' + a.slug if a.slug else ', 全部 campaign'})\n")
    hdr = f"{'':{w}}{'调用':>6}{'墙钟h':>8}{'in_tok':>11}{'out_tok':>10}{'缓存in%':>9}{'便宜拒':>7}{'缓存跳':>7}{'失败':>6}"
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

    print("\n杠杆指标")
    roles = defaultdict(int)
    for r in rows:
        roles[r.get("role") or "?"] += 1
    drive, acq = roles.get("DRIVE", 0), roles.get("ACQUIT", 0)
    # ★按 token 而不是按调用数 —— 按调用数会严重误导:实测写手 447k in/次、
    # 判官 16k in/次(差 ~27 倍),调用数上判官占多数,成本上写手占 94%。
    tok = defaultdict(int)
    for r in rows:
        tok[r.get("role") or "?"] += (r.get("in_tok") or 0) + (r.get("out_tok") or 0)
    dt, at = tok.get("DRIVE", 0), tok.get("ACQUIT", 0)
    if drive + acq:
        print(f"  DRIVE/ACQUIT 调用数   {drive} / {acq}  (判官占 {100*acq/(drive+acq):.0f}% 的调用)")
    if dt + at:
        who = "写手" if dt > at else "判官"
        print(f"  DRIVE/ACQUIT token    {dt:,} / {at:,}"
              f"  ({who}占 {100*max(dt,at)/(dt+at):.0f}% 的 token ← 成本中心在这里)")
        if drive and acq:
            print(f"  每次调用 token        写手 {dt//max(drive,1):,} · 判官 {at//max(acq,1):,}"
                  f"  (相差 {max(dt//max(drive,1),1)/max(at//max(acq,1),1):.0f}×)")
    print(f"  cheap_reject 率      {tot['cheap']}/{tot['n']} = {100*tot['cheap']/tot['n']:.1f}%"
          f"   (每次 = 省下一次权威 Codex)")
    print(f"  cache_hit 率         {tot['cache']}/{tot['n']} = {100*tot['cache']/tot['n']:.1f}%"
          f"   (每次 = 整次引擎调用未发生)")
    if tot["err"]:
        print(f"  ⚠ 失败/超时          {tot['err']} 次 —— 纯浪费,M4 要专门盯")
    ci = sum(r.get("cached_in_tok") or 0 for r in rows)
    ti = sum(r.get("in_tok") or 0 for r in rows)
    if ti:
        print(f"  prompt 缓存吃到      {100*ci/ti:.0f}% 的输入 token")
    if not PRICES:
        print("\n  (未配价格表 → 只报 token/墙钟。要出金额请填 scripts/cost_report.py 的 PRICES)")


if __name__ == "__main__":
    main()
