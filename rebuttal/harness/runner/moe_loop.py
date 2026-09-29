#!/usr/bin/env python3
"""MoE-select-refine loop (EMNLP r6->r7).

The r6->r7 body the user specified:
  1. a MoE of expert strategies generates N candidate rebuttals (parallel)
  2. select the one the verifier scores highest
  3. check it against the cross-family gate
  4. if it does NOT pass, carry that best rebuttal (+ the judge's advice) into the
     next round's expert input and re-roll

This layer sits on top of consensus_gate. It owns SELECTION + CARRY-FORWARD; the
gate/consensus is consensus_gate; the actual GENERATION is external (an agent, or a
pool of DeepSeek-prompt experts like data/agent_rebuttal_eval's 7 agents, or our
argument compiler as one more expert).

Grounding from the 7-agent eval (data/agent_rebuttal_eval/README):
  · raise-rate caps ~19-37.5% with the OUTCOME template -> for OA=3 we rank on the
    diagnoser STRENGTH bar (bar_met/raise_potential), not the unreachable raise outcome.
  · complex != better (SingleShot baseline ties 3rd) -> keep simple experts in the pool.
  · gen==judge self-eval bias -> the gate is cross-family (DeepSeek + Codex).

Protocol per round:
    cands = [{"expert": name, "rebuttal": text}, ...]   # <agent/experts generate, seeded by carry_forward>
    best, ranked = moe.select(cands)                     # DeepSeek verify score, ranked
    r = moe.decide(best)                                 # cheap gate: ammo + DeepSeek bar
    if r["need_codex"]:
        codex_raw = <agent runs mcp__codex__codex with r["codex_prompt"], high reasoning>
        r = moe.decide(best, codex_raw=codex_raw)        # authoritative consensus
    if r["stop"]: done
    else: seed = r["carry_forward"]  # feed into experts next round
"""
import os
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.abspath(os.path.join(HERE, "..", "..", "rebuttal_verifier"))):
    if p not in sys.path:
        sys.path.insert(0, p)
import consensus_gate as cg          # noqa: E402
from coach_loop import ammo_hits     # noqa: E402  (shared ammunition grep)

REACTION_RANK = {"raise": 2, "same": 1, "lower": 0}


def load_strategies(manifest_path=None):
    """Read the pluggable MoE strategy registry (harness/strategies/MANIFEST.json).
    Adding/merging a strategy = drop a strategies/<id>.md + register here. Engine-agnostic."""
    manifest_path = manifest_path or os.path.join(
        os.path.dirname(HERE), "strategies", "MANIFEST.json")
    m = json.load(open(manifest_path))
    return [s for s in m["strategies"] if s.get("enabled")]


def _rank_key(s):
    """Higher is better: clears the (score-aware) bar first, then raise_potential=high,
    then fewer ammunition hits, then the raw reaction. Mirrors the eval's composite
    (quality minus risk) but with our bar and a hard ammo tiebreak."""
    return (1 if s["bar_met"] else 0,
            1 if s.get("rp") == "high" else 0,
            -s["ammo"],
            REACTION_RANK.get(s["reaction"], 0))


class MoELoop:
    def __init__(self, case, max_iter=4):
        assert "rebuttal" not in case, "case is review+profile+initial_overall, no rebuttal"
        self.case = dict(case)
        self.max_iter = max_iter
        self.rounds = []          # [{round, best_expert, ranked, stop, carry}]
        self.best_ever = None

    # ---- selection --------------------------------------------------------
    def select(self, candidates):
        """candidates: [{"expert","rebuttal"}]. Score each via DeepSeek verify, rank."""
        scored = []
        for c in candidates:
            case = {**self.case, "rebuttal": c["rebuttal"]}
            j = cg.deepseek_judge(case, template="auto")
            met, kind = cg.bar_met(j, self.case)
            scored.append({"expert": c["expert"], "rebuttal": c["rebuttal"], "ds": j,
                           "bar_met": met, "bar_kind": kind, "rp": j.get("raise_potential"),
                           "reaction": j.get("reaction"), "ammo": len(ammo_hits(c["rebuttal"]))})
        scored.sort(key=_rank_key, reverse=True)
        return scored[0], scored

    # ---- gate the selected best ------------------------------------------
    def codex_prompt(self, best):
        return cg.codex_prompt({**self.case, "rebuttal": best["rebuttal"]}, template="auto")

    def decide(self, best, codex_raw=None):
        """Cheap gate (ammo + DeepSeek bar, already in `best`) then authoritative Codex."""
        rnd = len(self.rounds) + 1
        if best["ammo"] or not best["bar_met"]:            # cheap reject -> no Codex
            return self._record(rnd, best, None, stop=False)
        if codex_raw is None:                              # clean + passes DeepSeek -> need authoritative judge
            return {"stop": False, "need_codex": True, "codex_prompt": self.codex_prompt(best)}
        con = cg.consensus(best["ds"], cg.parse_codex(codex_raw), self.case)
        return self._record(rnd, best, con, stop=bool(con["stop"] and not best["ammo"]))

    def _record(self, rnd, best, con, stop):
        # best-ever pointer (score: stop > cleared-cheap > else)
        score = 2 if stop else (1 if (best["bar_met"] and not best["ammo"]) else 0)
        if self.best_ever is None or score > self.best_ever["score"]:
            self.best_ever = {"round": rnd, "expert": best["expert"],
                              "rebuttal": best["rebuttal"], "score": score}
        carry = None if stop else self._carry_forward(best, con)
        self.rounds.append({"round": rnd, "best_expert": best["expert"], "stop": stop,
                            "reaction": best["reaction"], "rp": best["rp"], "ammo": best["ammo"],
                            "consensus": (con or {}).get("stop")})
        out = {"stop": stop, "need_codex": False, "round": rnd,
               "best_expert": best["expert"], "ammo": best["ammo"], "bar_met": best["bar_met"]}
        if not stop:
            out["carry_forward"] = carry
            out["exhausted"] = rnd >= self.max_iter
            if out["exhausted"]:
                out["honest_concede"] = {"best_round": self.best_ever["round"]}
        return out

    def _carry_forward(self, best, con):
        """The seed the experts get next round: the prior best + the judge's advice +
        the ammunition phrases to avoid. This is 'carry the rebuttal into the next roll'."""
        advice = (con or {}).get("advice") or best["ds"].get("advice") or ""
        blocker = best["ds"].get("blocker") or ""
        avoid = sorted(set(ammo_hits(best["rebuttal"])))
        return {
            "prior_best_rebuttal": best["rebuttal"],
            "prior_best_expert": best["expert"],
            "blocker": blocker,
            "apply_advice": advice,
            "avoid_phrases": avoid,
            "instruction": ("Improve on the prior best rebuttal: keep what works, resolve the "
                            "blocker using the advice, and do NOT reuse the avoid_phrases (ammunition)."),
        }

    def state(self):
        return {"max_iter": self.max_iter, "rounds": len(self.rounds),
                "best_ever": (self.best_ever or {}).get("round"),
                "log": self.rounds}


if __name__ == "__main__":
    # structural self-check (no network): mock DeepSeek so selection + carry-forward run offline.
    case = {"review": "r", "reviewer_profile": "p", "initial_overall": 3}

    def fake_ds(c, template="auto"):
        t = c["rebuttal"]
        if "STRONG" in t:
            return {"veto": "none", "raise_potential": "high", "reaction": "raise",
                    "blocker": "marginal gains", "advice": "add concrete numbers"}
        return {"veto": "no-delivery", "raise_potential": "low", "reaction": "same",
                "blocker": "marginal gains", "advice": "add concrete numbers"}
    cg.deepseek_judge = fake_ds
    cg.parse_codex = lambda t: {"veto": "none", "raise_potential": "high", "reaction": "raise"}

    moe = MoELoop(case, max_iter=4)
    # round 1: pool of weak candidates (one leaks a promise) -> best still fails cheap gate
    r1cands = [{"expert": "A", "rebuttal": "we will add experiments in a future version"},
               {"expert": "B", "rebuttal": "a plain weak reply"}]
    best1, ranked1 = moe.select(r1cands)
    d1 = moe.decide(best1)
    assert d1["stop"] is False and "carry_forward" in d1
    assert d1["carry_forward"]["apply_advice"], "carry-forward must include the advice"
    # round 2: a STRONG candidate appears -> selected -> needs codex -> consensus stop
    best2, ranked2 = moe.select([{"expert": "C", "rebuttal": "STRONG: +2.3% and +6.4%, no promises"},
                                 {"expert": "B", "rebuttal": "still weak"}])
    assert best2["expert"] == "C"
    d2a = moe.decide(best2)
    assert d2a["need_codex"] is True
    d2b = moe.decide(best2, codex_raw='{"veto":"none","raise_potential":"high","reaction":"raise"}')
    assert d2b["stop"] is True, d2b
    print("moe_loop structural self-check OK:", json.dumps(moe.state(), ensure_ascii=False))
