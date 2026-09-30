#!/usr/bin/env python3
"""M1 cost meter — records one ledger line for every engine/judge call made by the harness.

Why this is a separate module:
  · `rebuttal_verifier/` is a **frozen package** (`consensus_gate.py` is pinned by the GATE_SHA
    content hash in orchestrate for provenance). Instrumentation **must never modify those files**,
    or it would break the frozen premise for anti-Goodhart. DeepSeek-side token counts are therefore
    intercepted at the **client factory** via `install_deepseek_probe()`; if interception fails, it
    silently degrades to "wall + call count only". A metering failure must never affect the production pipeline.
  · Accounting failures never raise exceptions. A broken meter means lost data; it must not become a production outage.

Ledger:campaigns/<slug>/ledger/cost.jsonl(one line per call,append-only)
Consumers:scripts/cost_report.py(aggregation)· M2 offline replay tool(counterfactual)

schema
------
ts          ISO8601 UTC
module      "rebuttal" | "math"
slug        campaign / target slug
unit        reviewer id / experiment expid / target slug — smallest unit of cost attribution
strategy    MoE strategy id(present for r6_write; None for other stage values)
stage       r6_write / r7_gate / cheap_eval / b3_ammo / ...
model       engine or judge model id
role        "DRIVE"(writer/planning) | "ACQUIT"(judge) — the two physically isolated sides are billed separately
in_tok/out_tok/cached_in_tok/reasoning_tok   token(None if unavailable)
wall_s      wall-clock seconds
prompt_chars number of characters sent(proxy when token counts are unavailable)
verdict     verdict from this call(PASS/FAIL/STRENGTH/CONCEDE/…)
cheap_reject whether the cheap gate rejected it(= one expensive judge call saved)
cache_hit   whether the stage-signature cache was hit(= the engine was not called at all)
err         engine failure/timeout marker
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
    """Append one cost record. **Swallow every exception** — the meter must not bring down the production pipeline."""
    if not _ENABLED:
        return
    try:
        row = {"v": SCHEMA_VERSION,
               "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "module": module, "slug": slug, "unit": unit, "stage": stage,
               # strategy is a first-class field: under MoE, the same reviewer runs N strategies;
               # recording only the reviewer prevents cost aggregation by strategy(the same flaw as the old gate ledger recording only picked)
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
    """Accumulate token counts from the stdout(JSONL event stream) of `codex exec --json`.

    Observed event:{"type":"turn.completed","usage":{"input_tokens":…,"cached_input_tokens":…,
              "cache_write_input_tokens":…,"output_tokens":…,"reasoning_output_tokens":…}}
    Accumulate across multiple turns. If unavailable, return None for every field(the caller degrades to wall + chars).
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


# ---- DeepSeek side: do not modify the frozen package; intercept at the client factory -------------------------------

_DS_USAGE = threading.local()


def last_deepseek_usage():
    """Retrieve and clear usage from the most recent DeepSeek call(thread-local). Probe not installed → None."""
    u = getattr(_DS_USAGE, "u", None)
    _DS_USAGE.u = None
    return u


def install_deepseek_probe():
    """Wrap the OpenAI client in verify_rebuttal so chat.completions.create also records usage.

    **Do not modify any file under rebuttal_verifier/**(frozen package + GATE_SHA provenance). If the internal
    structure changes, silently return False; the production pipeline keeps running, only without the token dimension.
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
    """with timed() as t: ...   afterward t.s = wall-clock seconds"""
    def __enter__(self):
        self._t0 = time.time()
        self.s = None
        return self

    def __exit__(self, *exc):
        self.s = time.time() - self._t0
        return False


if __name__ == "__main__":
    # Self-test: do not touch the network or the production pipeline
    ev = ('{"type":"turn.started"}\n'
          '{"type":"turn.completed","usage":{"input_tokens":12727,"cached_input_tokens":9984,'
          '"cache_write_input_tokens":0,"output_tokens":6,"reasoning_output_tokens":0}}\n')
    u = parse_codex_usage(ev)
    assert u == {"in_tok": 12727, "out_tok": 6, "cached_in_tok": 9984, "reasoning_tok": 0}, u
    assert parse_codex_usage("garbage") == {"in_tok": None, "out_tok": None,
                                           "cached_in_tok": None, "reasoning_tok": None}
    u2 = parse_codex_usage(ev + ev)          # Accumulate across multiple turns
    assert u2["in_tok"] == 25454, u2
    with timed() as t:
        pass
    assert t.s is not None and t.s >= 0
    print("✓ cost.py self-test passed(usage parsing / multiple-turn accumulation / degradation / timing)")
