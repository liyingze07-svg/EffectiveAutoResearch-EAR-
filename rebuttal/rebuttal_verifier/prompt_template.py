"""Prompt template for the rebuttal-quality verifier.

The task is framed as REVIEWER ROLE-PLAY: given a reviewer's identity, their
original review, and the authors' rebuttal to them, predict how that reviewer
would revise their overall score. The predicted reaction IS the rebuttal-quality
verdict:

    raise  -> the rebuttal is strong enough to move this reviewer UP  (high quality)
    same   -> the rebuttal does not change this reviewer's assessment  (neutral)
    lower  -> the rebuttal hurts (rare; e.g. exposes a flaw / annoys the reviewer)

This is the exact θ₀ instruction that scored best (DeepSeek V4 Pro, macro-F1
0.805 on a balanced ICLR-2025 test subset). See results.md.
"""

SYSTEM_INSTRUCTION = (
    "You are role-playing a specific ICLR peer reviewer. Given your reviewer "
    "profile, your original review, and the authors' rebuttal addressed to you, "
    "decide how you would revise your OVERALL rating after reading the rebuttal.\n\n"
    "Think as this reviewer: weigh whether the rebuttal actually resolves the "
    "weaknesses and questions you raised, or merely restates the paper. Reviewers "
    "rarely change their score; only move it when the rebuttal materially changes "
    "your assessment.\n\n"
    "First reason step by step as the reviewer, then output your decision as one "
    "of: raise, same, lower.\n\n"
    "Respond ONLY with a JSON object of the form:\n"
    '{"reasoning": "<your brief reviewer-style reasoning>", '
    '"reaction": "raise|same|lower"}'
)


def default_profile(case):
    """Build a reviewer-profile string from structured fields, or a generic one."""
    if case.get("reviewer_profile"):
        return case["reviewer_profile"]
    bits = []
    if case.get("initial_rating") is not None:
        bits.append(f"Before the rebuttal you rated this paper {case['initial_rating']}/10.")
    if case.get("confidence") is not None:
        bits.append(f"Your confidence is {case['confidence']}/5.")
    for k in ("soundness", "presentation", "contribution"):
        if case.get(k) is not None:
            bits.append(f"{k} {case[k]}/4.")
    return "You are an ICLR reviewer. " + (" ".join(bits) if bits else
                                           "You are a rigorous, fair reviewer.")


def build_messages(case):
    """case: dict with keys review, rebuttal, and either reviewer_profile OR
    initial_rating/confidence/soundness/presentation/contribution. Optional: title.
    Returns OpenAI-style [{"role","content"}, ...]."""
    profile = default_profile(case)
    review = case.get("review", "")
    rebuttal = case.get("rebuttal") or "(no rebuttal was posted to this reviewer)"
    title = case.get("title") or ""

    user = (
        f"# Paper title\n{title}\n\n"
        f"# Your reviewer profile\n{profile}\n\n"
        f"# Your original review\n{review}\n\n"
        f"# The authors' rebuttal to you\n{rebuttal}\n"
    )
    return [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": user},
    ]
