#!/usr/bin/env python3
"""r7 gate runner for the AutoRebuttal minimal loop.

The r6 half (argument-compiler WRITING) and the Codex half of r7 are AGENT actions,
not pure Python — the campaign agent writes the rebuttal and calls
mcp__codex__codex. This module is the DETERMINISTIC scaffolding around them:

  · thread_to_case  — turn a data/threads.jsonl row into a verifier `case`
  · score_rebuttal  — run the DeepSeek judge + the score-aware bar on one rebuttal
  · RebuttalGate     — what the campaign agent calls each round (DeepSeek side);
                       the agent supplies Codex's judgment (via MCP) to .consensus()

Demo modes prove the gate works end-to-end on REAL data:
  --demo-discriminate --index N   score the REAL author rebuttal vs a trivial one on the
                                   same case; the gate should separate them.
  --agreement --split test --n K   score REAL rebuttals for K cases and compare the gate's
                                   raise-vs-not call to the gold `label` (re-checks the 0.805
                                   wiring end-to-end through our harness).
"""
import os
import sys
import json
import argparse

HARNESS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.abspath(os.path.join(HARNESS, ".."))
VERIFIER = os.path.join(ROOT, "rebuttal_verifier")
DATA = os.path.join(ROOT, "data", "threads.jsonl")
if VERIFIER not in sys.path:
    sys.path.insert(0, VERIFIER)
import consensus_gate as cg  # noqa: E402

TRIVIAL = ("We thank the reviewer for the helpful comments. We will carefully address "
           "all the raised points in the revised version of the paper.")


def assemble_review(thread):
    """Reconstruct the reviewer's original review text from the thread fields."""
    parts = []
    for label, key in (("Summary", "summary"), ("Strengths", "strengths"),
                       ("Weaknesses", "weaknesses"), ("Questions", "questions")):
        v = thread.get(key)
        if v:
            parts.append(f"## {label}\n{v}")
    return "\n\n".join(parts)


def thread_to_case(thread, rebuttal_text):
    return {
        "title": thread.get("title", ""),
        "review": assemble_review(thread),
        "rebuttal": rebuttal_text,
        "initial_rating": thread.get("initial_rating"),
        "confidence": thread.get("confidence"),
        "soundness": thread.get("soundness"),
        "presentation": thread.get("presentation"),
        "contribution": thread.get("contribution"),
        "note_id": thread.get("note_id"),
        # EMNLP would carry initial_overall -> bar routes to the OA=3 diagnoser.
    }


def score_rebuttal(thread, rebuttal_text, template="iclr"):
    """DeepSeek judge + score-aware bar on one rebuttal. Returns a compact verdict."""
    case = thread_to_case(thread, rebuttal_text)
    j = cg.deepseek_judge(case, template=template)
    met, kind = cg.bar_met(j, case)
    return {"note_id": thread.get("note_id"), "bar_kind": kind, "bar_met": met,
            "reaction": j.get("reaction"), "reasoning": (j.get("reasoning") or "")[:280],
            "advice": j.get("advice")}


# ----- EMNLP / OA=3 path (diagnoser-as-coach) --------------------------------

OA3_DATA = os.path.join(ROOT, "data", "oa3_all.jsonl")


def oa3_case(row, rebuttal_text):
    """EMNLP OA=3 verifier case. initial_overall=3 routes to the raise-potential
    diagnoser (blocker/veto/raise_potential/advice); reviewer_profile is the v2-style
    persona (room-to-move stated in words, per README §3 — do NOT add the raw score)."""
    return {"review": row.get("review", ""), "rebuttal": rebuttal_text,
            "reviewer_profile": row.get("reviewer_profile"),
            "initial_overall": 3, "note_id": row.get("note_id")}


def score_emnlp_oa3(row, rebuttal_text):
    """Run the OA=3 diagnoser (DeepSeek) + the strength bar. Returns the coach signal
    (blocker/veto/advice) the loop routes on."""
    case = oa3_case(row, rebuttal_text)
    j = cg.deepseek_judge(case, template="auto")   # auto -> OA=3 diagnoser
    met, kind = cg.bar_met(j, case)                # strength bar: veto none + rp high
    return {"note_id": row.get("note_id"), "bar_kind": kind, "bar_met": met,
            "reaction": j.get("reaction"), "veto": j.get("veto"),
            "raise_potential": j.get("raise_potential"),
            "blocker": j.get("blocker"), "advice": j.get("advice"),
            "reasoning": (j.get("reasoning") or "")[:220]}


def load_oa3(note_id=None, split=None):
    rows = [json.loads(l) for l in open(OA3_DATA) if l.strip()]
    if note_id:
        return [r for r in rows if r.get("note_id") == note_id]
    if split:
        rows = [r for r in rows if r.get("split") == split]
    return rows


class RebuttalGate:
    """What the campaign agent instantiates per case. Each round it scores a candidate
    rebuttal on the DeepSeek side; the agent runs Codex (same prompt, via MCP) and passes
    the parsed judgment into consensus() for the cross-family stop decision."""

    def __init__(self, thread, template="iclr"):
        self.thread = thread
        self.template = template

    def deepseek(self, rebuttal_text):
        case = thread_to_case(self.thread, rebuttal_text)
        return case, cg.deepseek_judge(case, template=self.template)

    def codex_prompt(self, rebuttal_text):
        """The exact string the agent feeds to mcp__codex__codex (same frozen prompt)."""
        return cg.codex_prompt(thread_to_case(self.thread, rebuttal_text), self.template)

    def consensus(self, case, ds_judgment, codex_judgment):
        return cg.consensus(ds_judgment, codex_judgment, case)


def _load(split=None):
    rows = [json.loads(l) for l in open(DATA) if l.strip()]
    if split:
        rows = [r for r in rows if r.get("split") == split]
    return rows


def demo_discriminate(index, template):
    rows = _load()
    t = rows[index]
    print(f"# case {index}  note={t.get('note_id')}  rating={t.get('initial_rating')}/10 "
          f"conf={t.get('confidence')}  gold_label={t.get('label')} (delta={t.get('delta')})\n")
    real = score_rebuttal(t, t.get("rebuttal") or "", template)
    triv = score_rebuttal(t, TRIVIAL, template)
    print("REAL author rebuttal :", json.dumps(real, ensure_ascii=False))
    print("TRIVIAL rebuttal     :", json.dumps(triv, ensure_ascii=False))
    print(f"\n=> gate separates real vs trivial: "
          f"{real['reaction']!r} vs {triv['reaction']!r} "
          f"({'DISCRIMINATES' if real['reaction'] != triv['reaction'] else 'same call'})")


def agreement(split, n, template):
    rows = [r for r in _load(split) if r.get("has_rebuttal")][:n]
    ok = 0
    for t in rows:
        v = score_rebuttal(t, t.get("rebuttal") or "", template)
        gold_raise = (t.get("label") == "raise")
        pred_raise = (v["reaction"] == "raise")
        hit = (gold_raise == pred_raise)
        ok += hit
        print(f"note={t.get('note_id')} rating={t.get('initial_rating')} "
              f"gold={t.get('label'):5} pred={v['reaction']:5} {'OK' if hit else 'x'}")
    print(f"\nraise-vs-not agreement on {len(rows)} {split} cases: {ok}/{len(rows)} = {ok/max(1,len(rows)):.2f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo-discriminate", action="store_true")
    ap.add_argument("--agreement", action="store_true")
    ap.add_argument("--index", type=int, default=0)
    ap.add_argument("--split", default="test")
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--template", default="iclr")
    a = ap.parse_args()
    if a.demo_discriminate:
        demo_discriminate(a.index, a.template)
    elif a.agreement:
        agreement(a.split, a.n, a.template)
    else:
        ap.error("pick --demo-discriminate or --agreement")


if __name__ == "__main__":
    main()
