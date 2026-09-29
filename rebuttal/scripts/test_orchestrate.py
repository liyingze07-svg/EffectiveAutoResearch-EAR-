#!/usr/bin/env python3
"""产线纯函数单测 —— 零 API 成本,改判官/改预算后随时可跑。

  python3 scripts/test_orchestrate.py

为什么要有这个:本项目反复栽在**静默失效**上(截断、降级、缺省值掩盖缺失)。
这类 bug 不报错,只表现为"效果不好"。纯函数部分能被断言钉住的,就该钉住。

已经抓到过的真 bug:
  · join_budget 的预算在 B3 改 union-of-3 后不够(命中 5-6 → 12 条 / 4305 字符),
    两个改动相互作用,只加大预算装不下 → 促成"拦截类优先"的设计。
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


# ---- join_budget:carry-forward 反馈通道 ------------------------------------
def t_join_budget():
    print("\n[join_budget] 判官反馈能不能完整传到下一轮")
    items = ["a" * 100, "b" * 100, "c" * 100]
    msgs = []
    got = o.join_budget(items, 1000, "T", logger=msgs.append)
    check("预算够时全部装下且不告警", got.count("a" * 100) == 1 and len(msgs) == 0)
    msgs.clear()
    got = o.join_budget(items, 150, "T", logger=msgs.append)
    check("预算不够时必须出声(不许静默丢)", len(msgs) == 1 and "丢弃" in msgs[0])
    check("超预算时仍装下能装的", got.count("a" * 100) == 1)
    msgs.clear()
    check("空条目被跳过", o.join_budget(["", "  ", "x"], 100, "T", logger=msgs.append) == "x")


# ---- B3 裁决:必须由代码按明文类别表算,不看判官自报 ------------------------
def t_b3_verdict():
    print("\n[B3 裁决] 按类别表在代码里算,不依赖判官自报 verdict")
    check("拦截类集合与 stage prompt §2/§6 一致",
          o.B3_BLOCKING == {"A", "B", "B2", "C", "C2", "D", "E"})
    check("建议类不拦", o.B3_ADVISORY == {"deletable", "not_direct"})
    check("建议类与拦截类无交集", not (o.B3_BLOCKING & o.B3_ADVISORY))
    k1 = o._b3_key({"category": "D", "quote": "Hello   World"})
    k2 = o._b3_key({"category": "D", "quote": "hello world"})
    check("命中去重键对空白/大小写归一", k1 == k2)
    k3 = o._b3_key({"category": "A", "quote": "Hello World"})
    check("不同类别不去重", k1 != k3)


# ---- 真实 B3 产物:拦截类必须全部进 seed --------------------------------------
def t_real_b3_feedback():
    print("\n[真实 B3 产物] 拦截类命中必须全部进 carry-forward seed")
    p = f"{ROOT}/campaigns/01-wdData/ledger/B3_37ch_ammunition.json"
    if not os.path.exists(p):
        print("  - 跳过(无样本)"); return
    hits = json.load(open(p)).get("hits") or []
    srt = sorted(hits, key=lambda h: 0 if str(h.get("category", "")).strip() in o.B3_BLOCKING else 1)
    items = [f'"{h.get("quote","")}" -> {h.get("rewrite","")}' for h in srt]
    nblock = sum(1 for h in hits if str(h.get("category", "")).strip() in o.B3_BLOCKING)
    got = o.join_budget(items, 6000, "B3", logger=lambda m: None)
    check(f"6000 预算装下全部 {len(items)} 条", got.count('" -> ') == len(items))
    # 即使预算被压小,拦截类也必须优先进去
    tight = o.join_budget(items, 1200, "B3", logger=lambda m: None)
    kept_block = sum(1 for i in items[:nblock] if i in tight)
    check("预算压小时拦截类优先(不会被建议类挤掉)", kept_block >= 1 and
          all(i in tight for i in items[:kept_block]))


# ---- 策略阶梯 ---------------------------------------------------------------
def t_ladder():
    print("\n[策略阶梯] route_strategies")
    strats = [{"id": "s3_multistage"}, {"id": "s1_evidence_locked"}, {"id": "s2_persuasion"}]
    lad = [s["id"] for s in o.route_strategies(strats, {"initial_overall": 3})]
    check("按 MANIFEST.route 排序,s1 打头", lad[0] == "s1_evidence_locked")
    check("阶梯覆盖全部策略(未列出的兜底补齐)", set(lad) == {s["id"] for s in strats})


# ---- cost:usage 解析 --------------------------------------------------------
def t_cost():
    print("\n[cost] codex usage 解析")
    ev = ('{"type":"turn.completed","usage":{"input_tokens":100,"cached_input_tokens":80,'
          '"output_tokens":5,"reasoning_output_tokens":1}}')
    u = cost.parse_codex_usage(ev)
    check("单 turn 解析", u["in_tok"] == 100 and u["cached_in_tok"] == 80)
    check("多 turn 累加", cost.parse_codex_usage(ev + "\n" + ev)["in_tok"] == 200)
    check("拿不到则全 None(调用方降级用 wall)",
          cost.parse_codex_usage("garbage")["in_tok"] is None)


for t in (t_join_budget, t_b3_verdict, t_real_b3_feedback, t_ladder, t_cost):
    t()
print(f"\n{'='*52}\n通过 {len(PASS)} · 失败 {len(FAIL)}")
if FAIL:
    print("失败项:", FAIL)
sys.exit(1 if FAIL else 0)
