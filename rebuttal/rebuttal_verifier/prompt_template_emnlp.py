"""EMNLP/ARR variant of the reviewer-reaction prompt (v2).

Empirical finding that drives this design (see the transfer analysis): on the
ARR "reviewers who explicitly commented" population, the post-rebuttal move is
dominated by the reviewer's STARTING overall assessment (room-to-move), NOT by
rebuttal-text quality. A 1-feature threshold on the initial OA reaches acc 0.69,
while text-only LLM reasoning sits at chance (~0.45). The rebuttal texts are all
substantive, so they do not discriminate; the starting position does.

So this prompt makes the STARTING assessment the primary anchor and encodes the
ARR room-to-move prior explicitly (the model's own prior about rating->movement is
miscalibrated for ARR and, when simply handed the number, it used it the wrong
way). Concern-type and resolution are secondary adjustments.

The ICLR template (prompt_template.py) is unchanged; this is a separate venue
version, per the two-version plan.
"""

SYSTEM_INSTRUCTION = (
    "You are role-playing a specific ACL/EMNLP peer reviewer under ACL Rolling "
    "Review (ARR). Decide how you would revise your OVERALL ASSESSMENT (1-5 scale) "
    "after reading the authors' rebuttal: raise, same, or lower.\n\n"
    "ANCHOR ON YOUR STARTING ASSESSMENT FIRST. Empirically, on ARR your move is "
    "driven mostly by how much room you had, not by how hard the authors worked:\n"
    "  - If you started LOW (overall assessment <= 3): you have room to move up. If "
    "the rebuttal addresses anything substantive, you TEND TO RAISE by a small step "
    "(~0.5). Default lean: RAISE unless the rebuttal fails to engage your main "
    "concern.\n"
    "  - If you started HIGHER (overall assessment >= 3.5): you are near your ceiling "
    "and usually HOLD. A good, responsive rebuttal reassures you but does not push "
    "you higher. Default lean: SAME.\n\n"
    "THEN ADJUST for the nature of your primary concern:\n"
    "  - FUNDAMENTAL / SUBJECTIVE concern (insufficient novelty, limited contribution "
    "or significance, an ill-defined core concept, 'not enough for ACL main'): sticky "
    "in ACL. Even from a low start, if this is your main concern and it still stands, "
    "you HOLD -> SAME.\n"
    "  - EMPIRICAL / RESOLVABLE concern (missing experiment, unclear detail, a needed "
    "baseline or ablation, a clarification): a rebuttal that genuinely provides it "
    "supports a RAISE from a low start.\n\n"
    "Reviewers rarely lower after a rebuttal; only lower if it exposes a new real flaw.\n\n"
    "Respond ONLY with a JSON object:\n"
    '{"reasoning": "<anchor on starting assessment, then adjust for concern type>", '
    '"reaction": "raise|same|lower"}'
)


def default_profile(case):
    if case.get("reviewer_profile"):
        return case["reviewer_profile"]
    bits = []
    if case.get("initial_overall") is not None:
        bits.append(f"Before the rebuttal your overall assessment was {case['initial_overall']}/5.")
    if case.get("confidence") is not None:
        bits.append(f"Your confidence is {case['confidence']}/5.")
    if case.get("soundness") is not None:
        bits.append(f"Your soundness assessment is {case['soundness']}/5.")
    return "You are an ACL/EMNLP (ARR) reviewer. " + (" ".join(bits) if bits
                                                      else "You are a rigorous reviewer.")


def build_messages(case):
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
