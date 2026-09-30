"""Load data/threads.jsonl into DSPy examples.

Leakage guard: the model sees only the reviewer's INITIAL disposition
(initial_rating, confidence, sub-scores) + the review text + the rebuttal.
It never sees final_rating / delta / rating_trail (those define the label).
"""
import os
import json
import dspy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABELS = ["raise", "same", "lower"]
LABEL_ZH = {"raise": "raise", "same": "same", "lower": "lower"}


def _review_text(t):
    parts = []
    for k in ("summary", "strengths", "weaknesses", "questions"):
        v = t.get(k)
        if v:
            parts.append(f"## {k.capitalize()}\n{v}")
    return "\n\n".join(parts)


def _profile(t):
    return (
        f"You are an ICLR reviewer (id {t.get('reviewer_id')}). "
        f"Your self-reported confidence is {t.get('confidence')}/5. "
        f"Before the rebuttal you rated this paper {t.get('initial_rating')}/10. "
        f"Your sub-scores were soundness {t.get('soundness')}/4, "
        f"presentation {t.get('presentation')}/4, "
        f"contribution {t.get('contribution')}/4."
    )


def to_example(t):
    return dspy.Example(
        note_id=t["note_id"],                       # carried for joining, NOT an input
        paper_title=t.get("title") or "",
        reviewer_profile=_profile(t),
        review=_review_text(t),
        rebuttal=t.get("rebuttal") or "(no rebuttal was posted to this reviewer)",
        reaction=t["label"],
    ).with_inputs("paper_title", "reviewer_profile", "review", "rebuttal")


def load(path=None):
    path = path or os.path.join(ROOT, "data", "threads.jsonl")
    by_split = {"train": [], "val": [], "test": []}
    for line in open(path):
        t = json.loads(line)
        by_split[t["split"]].append(to_example(t))
    return by_split["train"], by_split["val"], by_split["test"]
