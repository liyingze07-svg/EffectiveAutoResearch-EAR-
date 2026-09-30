#!/usr/bin/env python3
"""Diagnoser-as-coach loop orchestrator (EMNLP OA=3 r6->r7).

The EMNLP goal-mode loop: write -> diagnose -> apply advice -> rewrite, until the
rebuttal clears the strength bar under BOTH families (authoritative consensus) AND
is ammunition-free, or max_iter -> honest concede.

Two of the four steps are AGENT actions, not Python:
  · WRITING the draft (argument compiler) — the agent, using .instruction()
  · CODEX judgment (OA=3 authoritative judge, high reasoning) — the agent, via mcp__codex__codex

So this is an orchestrator the agent steps through, not a self-running script. Protocol
per round:
    inst = loop.instruction()                 # what to write/fix this round
    draft = <agent writes via argument compiler using inst>
    r = loop.step(draft)                       # cheap gate: ammunition + DeepSeek diagnoser
    if r["need_codex"]:
        codex_raw = <agent runs mcp__codex__codex with r["codex_prompt"], high reasoning>
        r = loop.step(draft, codex_raw=codex_raw)   # authoritative consensus
    if r["stop"]: break                        # cleared: veto none + rp high on both, ammo 0
    # else loop with the next instruction (r["instruction"])

Cheap-first: the expensive authoritative judge (Codex/GPT-5.5) is only invoked once a
draft is already ammunition-free AND passes the DeepSeek diagnoser — never wasted on a
draft the cheap checks already reject.
"""
import os
import re
import sys
import json
import hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
VERIFIER = os.path.join(ROOT, "rebuttal_verifier")
for p in (VERIFIER, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)
import consensus_gate as cg  # noqa: E402

# self-incriminating / ammunition patterns. Mirrors shared-assets/ammunition-checklist.md
# (A self-exposure, B/B over-concession, B2 performative honesty, C empty promises, D new
# attack surface). grep is a SIGNAL, not truth -- a hit is reviewed, then rewritten.
# Unicode escapes preserve the original multilingual matching rules in this English source.
AMMO_PATTERNS = [
    # A. self-exposure / leaking weaknesses
    r"in a future version",
    r"due to (time|space|the limited)", r"we did not (test|evaluate|run|verify)",
    r"we have not (yet )?(tested|evaluated|verified|run)", r"we are setting up",
    r"we remain somewhat puzzled", r"we do not claim", r"we make no claim",
    r"there is no guarantee", r"we cannot guarantee",
    r"it is unclear whether", r"might be flawed", r"this is indeed a limitation",
    "\u5c1a\u672a(\u9a8c\u8bc1|\u6d4b\u8bd5)", "\u8fd8\u6ca1\u6765\u5f97\u53ca", "\u7559\u4f5c\u540e\u7eed", "\u6211\u4eec\u8ba1\u5212", "\u6211\u4eec\u4e0d\u58f0\u79f0", "\u8fd9\u786e\u5b9e\u662f\u4e2a\u5c40\u9650",
    # B / B. over-concession, accepting the attacker's frame
    r"we agree this is (merely|just)", r"just a (simple )?combination",
    r"we agree that .{0,40}(is|are) (problematic|flawed|wrong)",
    r"the reviewer is right that .{0,40}(weak|flaw|limitation)",
    "\u6211\u4eec\u627f\u8ba4\u8fd9\u53ea\u662f", "\u786e\u5b9e\u53ea\u662f\u7ec4\u5408", "reviewer \u8bf4\u5f97\u5bf9",
    # B2. performative honesty (soft ammunition)
    r"we honestly (concede|admit|acknowledge)", r"we (disclose|state) .{0,30}honestly",
    r"we did not spin", r"honest (scope|caveat|framing|lower-bound)",
    r"we will not (manufacture|fabricate)", r"we prefer to concede",
    r"we are careful not to over-?claim", r"we are explicit that",
    "to be honest", "admittedly", "\u8bda\u5b9e\u5730\u8bf4", "\u5766\u767d(\u8bf4|\u5730)?\u8bb2?", "\u8868\u6f14\u5f0f\u8bda\u5b9e",
    # C. empty promises / future-tense hand-waving.
    # Say what the REVISED TEXT *IS* (present tense + quote it), not that you'll change it.
    # (Good, NOT matched: "the revised abstract reads: '...'", "we have revised X to '...'".)
    r"we kindly ask you to revise", r"in the (final|camera-?ready) version", r"camera-?ready",
    "if accepted,? we will", "if the paper is accepted", "\u5982\u679c\u88ab\u63a5\u6536", "\u7bc7\u5e45\u6240\u9650",
    r"we will (add|include|provide|run|conduct|report|revise|expand|sharpen|clarify|move|state|mark|"
    r"promote|highlight|incorporate|reorganize|streamline|relabel|redraw|decouple|foreground|introduce|"
    r"present|discuss|update|improve|note|adjust|refine|rework|rephrase|separate|spell out)",
    r"we plan to (add|include|run|report)", r"we (are|'re) (revising|updating|reworking|adding)",
    r"we will also", r"the revision will", r"in (a )?revision,? we",
    r"will be (added|moved|revised|clarified|included|updated|expanded|reorganized|promoted|relabeled)",
    "\u6211\u4eec\u4f1a(\u5728|\u628a|\u8865|\u52a0|\u6539|\u8bf4\u660e|\u91cd|\u79fb)", "\u4fee\u8ba2(\u7a3f|\u7248)?\u5c06", "\u6211\u4eec\u5c06(\u8865|\u52a0|\u6539|\u5728)",
    # D. opening new attack surface / apologetics
    r"we are (very )?sorry", r"another possible (issue|problem|concern)",
    r"it would be helpful if you could", r"please let us know", r"if you are aware of better",
    "\u53e6\u4e00\u4e2a\u53ef\u80fd\u7684\u95ee\u9898",
]

_AMMO_RX = [re.compile(p, re.I) for p in AMMO_PATTERNS]


def ammo_hits(text):
    return [m.group(0) for rx in _AMMO_RX for m in rx.finditer(text)]


class CoachLoop:
    """Drives one EMNLP OA=3 rebuttal to convergence. `case` is the verifier case
    WITHOUT the rebuttal field (review + reviewer_profile + initial_overall=3)."""

    def __init__(self, case, max_iter=4):
        assert case.get("initial_overall") == 3, "coach loop is the OA=3 (borderline) path"
        self.case = dict(case)
        self.max_iter = max_iter
        self.rounds = []          # [{round, ammo, ds, codex, consensus, stop}]
        self.best = None          # best-so-far {round, draft, score}
        self._pending = None      # draft awaiting codex this round

    # ---- what to write/fix this round -------------------------------------
    def instruction(self):
        """Assemble the rewrite guidance from the latest diagnosis + anti-oscillation log."""
        if not self.rounds:
            return {"round": 1, "guidance": "Write the rebuttal via the argument compiler; "
                    "lead with the strongest concrete evidence for the blocker.",
                    "blocker": None, "veto": None, "advice": None, "avoid": []}
        last = self.rounds[-1]
        ds = last["ds"] or {}
        con = last.get("consensus") or {}
        # #23: at OA=3 Codex is the PRIMARY judge -> prefer the consensus/Codex advice when it
        # exists; fall back to DeepSeek only when no authoritative judgment was recorded.
        advice = con.get("advice") or ds.get("advice")
        avoid = sorted(set(last.get("ammo_list", [])))
        return {
            "round": len(self.rounds) + 1,
            "blocker": ds.get("blocker"),
            "veto": ds.get("veto"),
            "advice": advice,
            "avoid": avoid,  # ammunition phrases the previous draft leaked — do not reuse
            "keep": (self.best or {}).get("why", ""),  # what already worked (anti-oscillation)
            "guidance": "Apply the advice to resolve the blocker; keep what already cleared; "
                        "do NOT reintroduce the 'avoid' phrases (they are ammunition).",
        }

    # ---- score a draft ----------------------------------------------------
    def _case_with(self, draft):
        return {**self.case, "rebuttal": draft}

    def codex_prompt(self, draft):
        return cg.codex_prompt(self._case_with(draft), template="auto")

    def _draft_key(self, draft):
        """#22: a hash binding a Codex judgment to the EXACT case+draft it was issued for."""
        blob = json.dumps(self.case, sort_keys=True, ensure_ascii=False) + "\x00" + draft
        return hashlib.sha256(blob.encode()).hexdigest()[:16]

    def step(self, draft, codex_raw=None):
        """Cheap gate first (ammunition + DeepSeek diagnoser); the authoritative Codex
        judge only when the draft is already clean and passes DeepSeek."""
        ammo = ammo_hits(draft)
        ds = cg.deepseek_judge(self._case_with(draft), template="auto")
        ds_ok, kind = cg.bar_met(ds, self.case)

        if ammo or not ds_ok:                       # cheap checks reject -> no Codex
            return self._finish_round(draft, ammo, ds, None, stop=False)

        if codex_raw is None:                       # clean + DeepSeek-ok -> need authoritative judge
            self._pending = self._draft_key(draft)  # #22: bind the pending judgment to THIS draft
            return {"stop": False, "need_codex": True, "pending_key": self._pending,
                    "codex_prompt": self.codex_prompt(draft),
                    "note": "draft is ammunition-free and passes DeepSeek; run Codex (high reasoning)"}

        # #22: the supplied codex_raw MUST resolve the same draft we issued the prompt for.
        if self._pending is None or self._pending != self._draft_key(draft):
            return {"stop": False, "need_codex": True, "pending_key": self._draft_key(draft),
                    "codex_prompt": self.codex_prompt(draft),
                    "error": "codex_raw does not match the pending draft (stale/out-of-order); "
                             "re-run Codex on THIS exact draft"}

        codex = cg.parse_codex(codex_raw)
        return self._finish_round(draft, ammo, ds, codex, stop=None)

    def _finish_round(self, draft, ammo, ds, codex, stop):
        con = cg.consensus(ds, codex, self.case) if codex is not None else None
        if stop is None:
            stop = bool(con and con["stop"] and not ammo)
        rec = {"round": len(self.rounds) + 1, "ammo": len(ammo), "ammo_list": ammo,
               "ds": ds, "codex": codex, "consensus": con, "stop": stop}
        self.rounds.append(rec)
        self._pending = None
        # best-so-far: prefer a stop; else a draft that at least cleared DeepSeek + ammo0
        ds_ok = cg.bar_met(ds, self.case)[0]
        score = (2 if stop else (1 if (ds_ok and not ammo) else 0))
        if self.best is None or score > self.best["score"]:
            self.best = {"round": rec["round"], "draft": draft, "score": score,
                         "why": (ds.get("advice") or "")}
        out = {"stop": stop, "need_codex": False, "round": rec["round"],
               "ammo": len(ammo), "ds_ok": ds_ok,
               "consensus": {k: con[k] for k in ("stop", "mode", "primary")} if con else None}
        if not stop:
            out["instruction"] = self.instruction()
            out["exhausted"] = (rec["round"] >= self.max_iter)
            if out["exhausted"]:
                out["honest_concede"] = {"best_round": self.best["round"],
                                         "reason": "max_iter reached without clearing the bar"}
        return out

    # ---- persistence ------------------------------------------------------
    def state(self):
        return {"max_iter": self.max_iter, "rounds": len(self.rounds),
                "best": (self.best or {}).get("round"),
                "log": [{"round": r["round"], "ammo": r["ammo"], "stop": r["stop"],
                         "veto": (r["ds"] or {}).get("veto"),
                         "rp": (r["ds"] or {}).get("raise_potential")} for r in self.rounds]}

    def save(self, path):
        json.dump(self.state(), open(path, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    # structural self-check (no network): drive the state machine with mocked judgments.
    class _Fake:  # monkeypatch cg calls
        pass
    import types
    case = {"review": "r", "reviewer_profile": "p", "initial_overall": 3}

    seq = {"n": 0}
    def fake_ds(c, template="auto"):
        seq["n"] += 1
        # round1 draft has a promise (ammo) so DeepSeek never gates; round2 clean+strong
        return {"veto": "none", "raise_potential": "high", "reaction": "raise",
                "blocker": "marginal gains", "advice": "add concrete numbers"}
    cg.deepseek_judge = fake_ds
    cg.parse_codex = lambda t: {"veto": "none", "raise_potential": "high", "reaction": "raise"}

    lp = CoachLoop(case, max_iter=4)
    # round 1: draft leaks a promise -> ammo>0 -> rejected cheaply, no codex
    r1 = lp.step("We will add GPT-4o experiments in a future version.")
    assert r1["stop"] is False and r1["ammo"] > 0 and r1["need_codex"] is False
    assert r1["instruction"]["avoid"], "ammunition phrases must be fed back as 'avoid'"
    # round 2: clean strong draft -> needs codex
    r2a = lp.step("SX-SAL improves +2.3% over SCross-PAL and +6.4% over Self-Consistent.")
    assert r2a["need_codex"] is True and "codex_prompt" in r2a
    # supply codex -> consensus stop
    r2b = lp.step("SX-SAL improves +2.3% over SCross-PAL and +6.4% over Self-Consistent.",
                  codex_raw='{"veto":"none","raise_potential":"high","reaction":"raise"}')
    assert r2b["stop"] is True, r2b
    assert lp.state()["rounds"] == 2
    print("coach_loop structural self-check OK:", json.dumps(lp.state(), ensure_ascii=False))
