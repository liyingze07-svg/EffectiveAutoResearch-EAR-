"""Cross-family consensus gate for the AutoRebuttal harness (r7).

Two DIFFERENT model families judge the SAME rebuttal with the SAME frozen prompt
(prompt_template θ₀), and the harness stops only when BOTH agree the bar is met.
This is the anti-Goodhart stop condition: to game the loop you'd have to fool two
independent families at once.

  judge A = DeepSeek V4 Pro   (the 0.805-F1 backbone; runs here via the OpenAI-compatible API)
  judge B = Codex             (OpenAI/GPT family; SAME prompt, invoked by the harness agent
                               through the mcp__codex__codex tool — see codex_prompt())

SCORE-AWARE BAR (grounded in README §4/§5 findings):
  - At a borderline OA=3, raise/same OUTCOME is NOT predictable from the rebuttal text
    (permutation test, p>0.05). So the bar there is rebuttal STRENGTH, judged by the
    OA=3 diagnoser: veto == 'none' AND raise_potential == 'high'. Do NOT hard-require a
    predicted 'raise' at the border — that is chasing noise.
  - Everywhere else the raise signal exists, so the bar is reaction == 'raise'.

ZONE-AWARE PRIMARY JUDGE (grounded in README §7 cross-model finding):
  - The authoritative judge depends on the zone (mirrors verify_rebuttal's `--template route`):
      OA=3 border   -> Codex/GPT-5.5 is empirically BEST (quality-separation +0.28 vs
                       DeepSeek +0.13); run it at HIGH/xhigh reasoning. DeepSeek is weak
                       here (+0.13), so it is an advisory cross-check, not a hard blocker.
      non-border    -> DeepSeek V4 Pro is primary (ICLR macro-F1 0.805); Codex consensus.
  - Two consensus modes:
      'strict'        (default) stop iff BOTH families clear the bar — max anti-Goodhart.
      'authoritative' stop iff the PRIMARY judge clears AND the secondary does not veto
                       (reaction!='lower'); use at OA=3 where forcing weak-DeepSeek
                       consensus injects false negatives and stalls the loop.

Nothing here fabricates or optimizes against a judge's internals; the worker never sees
these prompts (physical DRIVE/ACQUIT split).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from verify_rebuttal import verify_one, _load_env, _parse  # noqa: E402
import prompt_template  # noqa: E402  (the frozen ICLR θ₀, shared by BOTH judges)


# ----- shared prompt (same for both families) --------------------------------

def judge_messages(case, template="iclr"):
    """The frozen prompt both judges see. `template`:
      'iclr' -> prompt_template (initial_rating /10; the 0.805 backbone)
      'auto' -> route EMNLP by OA=3 to the raise-potential diagnoser
    Returns OpenAI-style [{role,content}, ...]."""
    if template == "auto":
        from verify_rebuttal import build_messages_auto
        return build_messages_auto(case)
    import importlib
    return importlib.import_module(template if template != "iclr" else "prompt_template").build_messages(case)


def codex_prompt(case, template="iclr"):
    """Flatten judge_messages into a single string to feed mcp__codex__codex.
    The harness agent sends this to Codex, then calls parse_codex() on the reply."""
    msgs = judge_messages(case, template)
    return "\n\n".join(f"[{m['role'].upper()}]\n{m['content']}" for m in msgs)


def parse_codex(text):
    """Parse a Codex reply with the SAME robust parser DeepSeek uses, plus the
    diagnoser fields when present. Returns {reaction, reasoning, quality, veto?, raise_potential?, ...}."""
    import re, json
    from verify_rebuttal import QUALITY, _EXTRA_FIELDS
    reaction, reasoning = _parse(text)
    out = {"reaction": reaction, "reasoning": reasoning, "quality": QUALITY[reaction]}
    try:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            d = json.loads(m.group(0))
            for k in _EXTRA_FIELDS:
                if k in d:
                    out[k] = d[k]
    except Exception:
        pass
    return out


# ----- the score-aware bar ---------------------------------------------------

def bar_met(judgment, case):
    """Did this single judgment clear the bar for this case? Returns (met: bool, kind: str).
    Zone-aware per GOAL.md: OA<=2 -> raise; OA==3 (border) -> STRENGTH (veto none + rp high);
    OA>=4 -> maintain (reaction != 'lower')."""
    oa = case.get("initial_overall")
    reaction = str(judgment.get("reaction", "")).lower()
    if oa == 3:
        veto = str(judgment.get("veto", "none")).lower()
        rp = str(judgment.get("raise_potential", "low")).lower()
        return (veto == "none" and rp == "high", "strength")
    if oa is not None and oa >= 4:                      # high starter: maintain (not lowered)
        return (reaction != "lower", "maintain")
    return (reaction == "raise", "raise")               # low starter (OA<=2 / unknown)


def primary_judge(case):
    """Which family is authoritative for this case (README §7). At the OA=3 border
    Codex/GPT-5.5 wins; elsewhere DeepSeek. Returns 'codex' or 'deepseek'."""
    return "codex" if case.get("initial_overall") == 3 else "deepseek"


def consensus(ds_judgment, codex_judgment, case, mode=None):
    """Combine the two families into the stop decision + the route-back advice.
    mode: 'strict' (both clear; default off-border) or 'authoritative' (primary clears
    AND secondary does not veto; default on the OA=3 border, where DeepSeek is weak)."""
    ds_ok, kind = bar_met(ds_judgment, case)
    cx_ok, _ = bar_met(codex_judgment, case)
    primary = primary_judge(case)
    if mode is None:
        mode = "authoritative" if case.get("initial_overall") == 3 else "strict"

    if mode == "authoritative":
        prim_ok = cx_ok if primary == "codex" else ds_ok
        sec = ds_judgment if primary == "codex" else codex_judgment
        sec_veto = str(sec.get("reaction", "")).lower() == "lower"
        stop = bool(prim_ok and not sec_veto)
    else:  # strict
        stop = bool(ds_ok and cx_ok)

    # route-back signal: the PRIMARY judge's diagnoser advice if present, else reasoning
    prim_j = codex_judgment if primary == "codex" else ds_judgment
    advice = (prim_j.get("advice") or prim_j.get("reasoning")
              or ds_judgment.get("advice") or ds_judgment.get("reasoning") or "")
    return {
        "stop": stop, "kind": kind, "mode": mode, "primary": primary,
        "deepseek_ok": bool(ds_ok), "codex_ok": bool(cx_ok),
        "deepseek": ds_judgment, "codex": codex_judgment,
        "advice": advice,
    }


# ----- convenience: run the DeepSeek side here -------------------------------

def deepseek_judge(case, template="iclr"):
    """Run judge A (DeepSeek) in-process. Judge B (Codex) is run by the agent via
    mcp__codex__codex using codex_prompt(case, template) + parse_codex()."""
    bm = (lambda c: judge_messages(c, template))
    return verify_one(case, build_messages=bm)


def _selfcheck():
    """SPEC<->IMPL consistency guard. Every assertion below is the machine-checkable form of a
    line in ../harness/GOAL.md's zone table. If GOAL.md changes but bar_met/consensus don't (or
    vice-versa), this fails -- so orchestrate.py calls it at startup and REFUSES to run on drift.
    (This is what caught H4 conceptually: OA>=4 must be a maintain bar, not a raise bar.)
    Raises AssertionError with a GOAL.md-keyed message; returns True on success. No network."""
    def _ck(cond, spec):
        if not cond:
            raise AssertionError(f"GOAL.md drift: {spec} -- consensus_gate no longer implements it")

    border = {"initial_overall": 3}
    # GOAL.md OA=3 border: strength bar = veto=='none' AND raise_potential=='high'
    _ck(bar_met({"veto": "none", "raise_potential": "high"}, border) == (True, "strength"),
        "OA=3 -> strength (veto none + rp high)")
    _ck(bar_met({"veto": "novelty", "raise_potential": "high"}, border)[0] is False,
        "OA=3 -> a veto blocks the strength bar")
    # GOAL.md OA<=2 (low starter / unknown): raise bar
    _ck(bar_met({"reaction": "raise"}, {"initial_overall": 2}) == (True, "raise"), "OA<=2 -> raise")
    _ck(bar_met({"reaction": "same"}, {"initial_overall": 2})[0] is False, "OA<=2 -> 'same' fails raise")
    _ck(bar_met({"reaction": "raise"}, {}) == (True, "raise"), "unknown OA -> raise")
    # GOAL.md OA>=4 (high starter): maintain bar = reaction != 'lower'
    _ck(bar_met({"reaction": "same"}, {"initial_overall": 4}) == (True, "maintain"), "OA>=4 -> 'same' maintains")
    _ck(bar_met({"reaction": "raise"}, {"initial_overall": 5}) == (True, "maintain"), "OA>=4 -> 'raise' maintains")
    _ck(bar_met({"reaction": "lower"}, {"initial_overall": 4}) == (False, "maintain"), "OA>=4 -> 'lower' fails maintain")
    # GOAL.md: off-border uses STRICT consensus (both families clear); DeepSeek primary
    _ck(primary_judge({"initial_overall": 2}) == "deepseek", "off-border primary = DeepSeek")
    c = consensus({"reaction": "raise"}, {"reaction": "same"}, {"initial_overall": 2})
    _ck(c["stop"] is False and c["codex_ok"] is False and c["mode"] == "strict",
        "off-border strict: one family failing blocks stop")
    c2 = consensus({"reaction": "raise"}, {"reaction": "raise"}, {"initial_overall": 2})
    _ck(c2["stop"] is True and c2["primary"] == "deepseek", "off-border strict: both clear -> stop")
    c_hi = consensus({"reaction": "same"}, {"reaction": "same"}, {"initial_overall": 4})
    _ck(c_hi["stop"] is True and c_hi["kind"] == "maintain", "OA>=4 strict: 'same'/'same' maintains")
    c_hi2 = consensus({"reaction": "same"}, {"reaction": "lower"}, {"initial_overall": 4})
    _ck(c_hi2["stop"] is False, "OA>=4: a 'lower' from either family blocks maintain")
    # GOAL.md OA=3: AUTHORITATIVE consensus -- Codex primary; weak-DeepSeek 'same' must NOT block
    _ck(primary_judge(border) == "codex", "OA=3 primary = Codex")
    strong_cx = {"veto": "none", "raise_potential": "high", "reaction": "raise"}
    weak_ds = {"veto": "novelty", "raise_potential": "low", "reaction": "same"}
    c3 = consensus(weak_ds, strong_cx, border)
    _ck(c3["stop"] is True and c3["primary"] == "codex" and c3["mode"] == "authoritative",
        "OA=3 authoritative: Codex clears + DeepSeek not-veto -> stop")
    c4 = consensus({"reaction": "lower"}, strong_cx, border)
    _ck(c4["stop"] is False, "OA=3 authoritative: a real DeepSeek 'lower' still blocks (cross-family)")
    return True


if __name__ == "__main__":
    _selfcheck()
    print("consensus_gate structural self-check OK")
