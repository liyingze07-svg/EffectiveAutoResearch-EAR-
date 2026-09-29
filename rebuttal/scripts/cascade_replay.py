#!/usr/bin/env python3
"""M2a 级联回放器 —— 零 API 成本,在已有判官预测上算"换级联策略能省多少"。

语料:同一批 case 被多个模型用**同一冻结 prompt** 判过(data/preds_*.jsonl),
gold 来自 data/threads.jsonl。这是**配对**数据 —— 能算模型间一致性,
而一致性正是级联的关键:便宜档和贵档高度一致时,贵档大部分调用是浪费。

判据口径:停机门问的是"这份 rebuttal 够不够"。此处建模低起点分区的 bar
(`reaction == 'raise'`),gold=raise 即"本该放行"。
  FP = 误放行(弱稿过门)—— 要约束的 α
  FN = 误拦截(好稿被卡)—— 代价是多跑一轮,烧钱不烧信誉

成本单位:以一次便宜判官 = 1。贵/便宜价格比 r 未知(历史无 token 记录),
故**扫一组 r 报结果**,不假装知道确切价格。r 的真值将由 M1 账本给出。

  python3 scripts/cascade_replay.py
  python3 scripts/cascade_replay.py --alpha 0.10
"""
import os, json, argparse, random
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
D = os.path.join(ROOT, "data")

MODELS = {           # 文件 -> (展示名, 档位:cheap/mid/exp)
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
    ap.add_argument("--alpha", type=float, default=0.15, help="可接受的误放行率上限")
    a = ap.parse_args()
    gold, preds = load()

    # 公共 case 集(所有三档都判过的)——级联必须在同一批 case 上比
    core = ["deepseek-flash", "deepseek-pro", "codex"]
    ids = sorted(set.intersection(*[set(preds[m][0]) for m in core if m in preds]))
    print(f"\n语料:{len(ids)} 个 case 被 {', '.join(core)} 全判过"
          f"(gold: raise {sum(1 for i in ids if gold[i]=='raise')} / "
          f"非 raise {sum(1 for i in ids if gold[i]!='raise')})")
    if len(ids) < 100:
        print(f"⚠ n={len(ids)} 偏小 —— 下面所有点估计都带 95% bootstrap CI,"
              f"宽 CI 说明该结论还不能当决策依据。")

    # ── 单模型表现 ────────────────────────────────────────────────
    print("\n【单判官表现】(在公共集上;raise = 放行)\n")
    print(f"{'判官':16}{'档':>5}{'准确率':>10}{'95% CI':>18}{'误放行FP':>10}{'误拦截FN':>10}")
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

    # ── 两两一致性(级联的物理基础)────────────────────────────────
    print("\n【两两一致性】—— 便宜档与贵档越一致,贵档的调用越多是浪费\n")
    names = [n for n in preds if all(i in preds[n][0] for i in ids)]
    for i1 in range(len(names)):
        for i2 in range(i1 + 1, len(names)):
            A, B = names[i1], names[i2]
            ag = [1 if (preds[A][0][i] == "raise") == (preds[B][0][i] == "raise") else 0
                  for i in ids]
            lo, hi = boot_ci(ag)
            print(f"  {A:16} vs {B:16} 一致 {sum(ag)}/{len(ag)} = "
                  f"{sum(ag)/len(ag):.1%}  CI[{lo:.1%},{hi:.1%}]")

    # ── 级联策略模拟 ──────────────────────────────────────────────
    # 策略 = 有序档位链 + strict 合议(链上每一档都要说 raise 才放行;
    # 任一档说不 raise 即短路,后面的档**不调用** = 省钱)
    POLICIES = {
        "P0 现行 cheap-first (pro→codex)": ["deepseek-pro", "codex"],
        "P1 三档 (flash→pro→codex)":       ["deepseek-flash", "deepseek-pro", "codex"],
        "P2 便宜档换 flash (flash→codex)":  ["deepseek-flash", "codex"],
        "P3 只用 codex":                    ["codex"],
        "P4 只用 pro":                      ["deepseek-pro"],
    }
    TIER_UNIT = {"cheap": 0.2, "mid": 1.0, "exp": None}   # exp 用 r 参数化

    print("\n【级联策略模拟】strict 合议:链上每档都说 raise 才放行,"
          "任一档否即短路(后续档不调用)\n")
    for r in (2, 5, 10, 20):
        print(f"  ── 贵/便宜价格比 r = {r}(exp 档每次记 {r},mid=1,cheap=0.2)──")
        print(f"  {'策略':36}{'E[成本]':>10}{'省%':>8}{'误放行':>8}{'误拦截':>8}{'准确率':>9}")
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
                        break                     # 短路:后面的档不调用
                truth = gold[i] == "raise"
                corr.append(1 if stop == truth else 0)
                fp += 1 if (stop and not truth) else 0
                fn += 1 if (not stop and truth) else 0
            ec = cost_t / len(ids)
            if base is None:
                base = ec
            save = 100 * (base - ec) / base
            flag = "  ⚠超α" if fp / len(ids) > a.alpha else ""
            print(f"  {label:36}{ec:>10.2f}{save:>7.0f}%{fp:>8}{fn:>8}"
                  f"{sum(corr)/len(corr):>9.3f}{flag}")
        print()

    print(f"读法:α={a.alpha:.0%} 是可接受的误放行率上限。"
          f"省钱但超 α 的策略不可用 —— 误放行意味着弱稿过门,那是信誉成本,不是钱。")
    print("r 的真值待 M1 账本积累后代入(已知一次 codex 调用 ≈12.7k in / 78% 缓存)。")


if __name__ == "__main__":
    main()
