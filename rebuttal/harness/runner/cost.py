#!/usr/bin/env python3
"""M1 成本仪表 —— 给 harness 的每次引擎/判官调用记一行账。

为什么单独一个模块:
  · `rebuttal_verifier/` 是**冻结包**(`consensus_gate.py` 被 orchestrate 的 GATE_SHA
    内容哈希钉住做溯源)。插桩**绝不改那些文件**,否则破坏反 Goodhart 的冻结前提。
    DeepSeek 侧的 token 因此靠 `install_deepseek_probe()` 在**客户端工厂**上拦截,
    拦不到就静默降级成"只有 wall + 调用数",绝不让计量失败影响产线。
  · 记账失败永不抛异常。仪表坏了是丢数据,不能变成产线中断。

账本:campaigns/<slug>/ledger/cost.jsonl(一行一次调用,append-only)
消费者:scripts/cost_report.py(汇总)· M2 离线回放器(反事实)

schema
------
ts          ISO8601 UTC
module      "rebuttal" | "math"
slug        campaign / 靶 slug
unit        reviewer id / 实验 expid / 靶 slug —— 成本归属的最小单位
strategy    MoE 策略 id(r6_write 有;其他 stage 为 None)
stage       r6_write / r7_gate / cheap_eval / b3_ammo / ...
model       引擎或判官模型 id
role        "DRIVE"(写手/规划) | "ACQUIT"(判官) —— 物理隔离两侧分别计费
in_tok/out_tok/cached_in_tok/reasoning_tok   token(拿不到则 None)
wall_s      墙钟秒
prompt_chars 送进去的字符数(token 拿不到时的代理量)
verdict     该次调用的结论(PASS/FAIL/STRENGTH/CONCEDE/…)
cheap_reject 便宜门是否拒掉(= 省下了一次贵判官调用)
cache_hit   stage-signature 缓存是否命中(= 完全没调引擎)
err         引擎失败/超时标记
"""
import os, json, time, threading

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
_LOCK = threading.Lock()
_ENABLED = os.environ.get("AUTOREBUTTAL_COST", "1") != "0"

SCHEMA_VERSION = 1


def ledger_path(slug, module="rebuttal"):
    if module == "math":
        return os.path.join(ROOT, "campaigns", slug, "ledger", "cost.jsonl")
    return os.path.join(ROOT, "campaigns", slug, "ledger", "cost.jsonl")


def record(slug=None, unit=None, stage=None, model=None, role=None, module="rebuttal",
           strategy=None, in_tok=None, out_tok=None, cached_in_tok=None, reasoning_tok=None,
           wall_s=None, prompt_chars=None, verdict=None,
           cheap_reject=None, cache_hit=None, err=None, **extra):
    """追加一条成本记录。**任何异常都吞掉** —— 仪表不能拖垮产线。"""
    if not _ENABLED:
        return
    try:
        row = {"v": SCHEMA_VERSION,
               "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "module": module, "slug": slug, "unit": unit, "stage": stage,
               # strategy 是一等字段:MoE 下同一 reviewer 会跑 N 个策略,只记到 reviewer
               # 就无法按策略归集成本(与旧 gate ledger 只记 picked 是同一类毛病)
               "strategy": strategy,
               "model": model, "role": role,
               "in_tok": in_tok, "out_tok": out_tok,
               "cached_in_tok": cached_in_tok, "reasoning_tok": reasoning_tok,
               "wall_s": round(wall_s, 2) if isinstance(wall_s, (int, float)) else None,
               "prompt_chars": prompt_chars, "verdict": verdict,
               "cheap_reject": cheap_reject, "cache_hit": cache_hit, "err": err}
        if extra:
            row["extra"] = extra
        p = ledger_path(slug or "_unscoped", module)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with _LOCK, open(p, "a") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def parse_codex_usage(stdout_text):
    """从 `codex exec --json` 的 stdout(JSONL 事件流)累加 token。

    实测事件:{"type":"turn.completed","usage":{"input_tokens":…,"cached_input_tokens":…,
              "cache_write_input_tokens":…,"output_tokens":…,"reasoning_output_tokens":…}}
    多 turn 则累加。拿不到返回全 None(调用方降级用 wall + chars)。
    """
    tot = {"in_tok": 0, "out_tok": 0, "cached_in_tok": 0, "reasoning_tok": 0}
    seen = False
    for ln in (stdout_text or "").splitlines():
        ln = ln.strip()
        if not ln or '"usage"' not in ln:
            continue
        try:
            d = json.loads(ln)
        except Exception:
            continue
        u = d.get("usage") or (d.get("msg", {}) or {}).get("usage")
        if not isinstance(u, dict):
            continue
        seen = True
        tot["in_tok"] += int(u.get("input_tokens") or 0)
        tot["out_tok"] += int(u.get("output_tokens") or 0)
        tot["cached_in_tok"] += int(u.get("cached_input_tokens") or 0)
        tot["reasoning_tok"] += int(u.get("reasoning_output_tokens") or 0)
    return tot if seen else {k: None for k in tot}


# ---- DeepSeek 侧:不改冻结包,在客户端工厂上拦截 -------------------------------

_DS_USAGE = threading.local()


def last_deepseek_usage():
    """取并清空最近一次 DeepSeek 调用的 usage(线程局部)。探针未装 → None。"""
    u = getattr(_DS_USAGE, "u", None)
    _DS_USAGE.u = None
    return u


def install_deepseek_probe():
    """包住 verify_rebuttal 的 OpenAI 客户端,使 chat.completions.create 顺手记下 usage。

    **不改 rebuttal_verifier/ 任何文件**(冻结包 + GATE_SHA 溯源)。内部结构变了就
    静默返回 False,产线照跑,只是少了 token 维度。
    """
    try:
        import verify_rebuttal as vr
    except Exception:
        return False
    if getattr(vr, "_cost_probe_installed", False):
        return True
    try:
        orig = vr._client_and_model

        def wrapped(*a, **kw):
            client, model = orig(*a, **kw)
            try:
                comp = client.chat.completions
                if not getattr(comp, "_cost_wrapped", False):
                    _create = comp.create

                    def create(*aa, **kk):
                        resp = _create(*aa, **kk)
                        try:
                            u = getattr(resp, "usage", None)
                            if u is not None:
                                _DS_USAGE.u = {
                                    "in_tok": getattr(u, "prompt_tokens", None),
                                    "out_tok": getattr(u, "completion_tokens", None),
                                    "cached_in_tok": getattr(
                                        getattr(u, "prompt_tokens_details", None),
                                        "cached_tokens", None),
                                }
                        except Exception:
                            pass
                        return resp

                    comp.create = create
                    comp._cost_wrapped = True
            except Exception:
                pass
            return client, model

        vr._client_and_model = wrapped
        vr._cost_probe_installed = True
        return True
    except Exception:
        return False


class timed:
    """with timed() as t: ...   之后 t.s = 墙钟秒"""
    def __enter__(self):
        self._t0 = time.time()
        self.s = None
        return self

    def __exit__(self, *exc):
        self.s = time.time() - self._t0
        return False


if __name__ == "__main__":
    # 自检:不碰网络、不碰产线
    ev = ('{"type":"turn.started"}\n'
          '{"type":"turn.completed","usage":{"input_tokens":12727,"cached_input_tokens":9984,'
          '"cache_write_input_tokens":0,"output_tokens":6,"reasoning_output_tokens":0}}\n')
    u = parse_codex_usage(ev)
    assert u == {"in_tok": 12727, "out_tok": 6, "cached_in_tok": 9984, "reasoning_tok": 0}, u
    assert parse_codex_usage("garbage") == {"in_tok": None, "out_tok": None,
                                           "cached_in_tok": None, "reasoning_tok": None}
    u2 = parse_codex_usage(ev + ev)          # 多 turn 累加
    assert u2["in_tok"] == 25454, u2
    with timed() as t:
        pass
    assert t.s is not None and t.s >= 0
    print("✓ cost.py 自检通过(usage 解析 / 多 turn 累加 / 降级 / 计时)")
