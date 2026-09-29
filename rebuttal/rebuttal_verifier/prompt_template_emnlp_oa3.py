"""EMNLP/ARR OA=3 raise-potential DIAGNOSER (final: the v7 logic).

Use when the reviewer is at a borderline overall assessment of 3 (the zone that
decides acceptance and the one the deployment cares about). It scores whether the
rebuttal is STRONG ENOUGH to deserve a raise, and — more usefully — returns an
actionable diagnosis (the blocker, which veto if any, and one concrete fix).

Why this design (grounded, not guessed):
  - At a borderline 3, whether THIS reviewer moves is dominated by reviewer inertia,
    not rebuttal quality; a permutation test found no significant text signal for the
    raise/same OUTCOME. So we score the rebuttal's STRENGTH, not the outcome.
  - v2 already tracks quality (its raise-calls carry significantly more concrete
    evidence, p=0.025), and good rebuttals a lazy reviewer held ("same, high delivery")
    score like true raises — so high recall on genuinely-good rebuttals is right.
  - The one thing v2 lacked was rejecting clearly-weak rebuttals (it called 'raise' on
    67% of non-response / promise-only ones). A NARROW veto fixes that while a permissive
    positive lean keeps recall high. On the quality-separation metric (raise-rate on
    good rebuttals minus on clearly-weak), this beats v2 (+0.16 vs +0.13) and a strict
    veto variant (+0.03). The margin is within noise at n=54, but the veto makes the
    output interpretable and actionable, which is the real product.

reaction: 'raise' = strong enough to deserve a raise; 'same' = not.
"""

SYSTEM_INSTRUCTION = (
    "You are judging whether an author rebuttal is STRONG ENOUGH to deserve a score "
    "increase from a borderline ACL/EMNLP (ARR) reviewer at overall assessment 3/5. "
    "Judge the REBUTTAL'S STRENGTH, not whether this reviewer bothered to move - a "
    "borderline reviewer often holds a good rebuttal out of inertia.\n\n"
    "STEP 1 - Blocker. Identify the single weakness most responsible for the 3.\n\n"
    "STEP 2 - Veto. YOUR DEFAULT IS veto='none'. Set a veto ONLY when the response to "
    "the blocker is a BLATANT, unambiguous failure - when in any doubt, choose 'none'. "
    "The three failures:\n"
    "  no-delivery: it gives NOTHING new - only promises future changes, or asks you to "
    "clarify, or merely restates the paper with no new evidence at all.\n"
    "  off-target: it never engages the blocker, answering only secondary points.\n"
    "  novelty: the blocker is insufficient NOVELTY or SIGNIFICANCE, and the rebuttal "
    "only adds experiments or clarifications. New experiments cannot create novelty.\n\n"
    "STEP 3 - Default to RAISE when veto='none'. At a borderline 3 you have room to "
    "move, so any substantive engagement with the blocker (a clarification you accept, "
    "or new evidence - it need NOT be dramatic or complete) is strong enough -> 'raise'. "
    "Choose 'same' with veto='none' only in the rare case where the response is on-topic "
    "yet plainly trivial. Do NOT demand a perfect resolution; a small credible step "
    "earns a raise.\n\n"
    "Reaction 'lower' only if the rebuttal introduces a new real flaw.\n\n"
    "Respond ONLY with a JSON object:\n"
    "{\n"
    '  "blocker": "<the single weakness holding the score at 3>",\n'
    '  "veto": "none|no-delivery|off-target|novelty",\n'
    '  "reasoning": "<blocker, then veto check, then substantive-engagement check>",\n'
    '  "raise_potential": "high|low",\n'
    '  "advice": "<one concrete change that would make this rebuttal strong enough>",\n'
    '  "reaction": "raise|same|lower"\n'
    "}"
)


def default_profile(case):
    if case.get("reviewer_profile"):
        return case["reviewer_profile"]
    bits = []
    if case.get("confidence") is not None:
        bits.append(f"Your confidence is {case['confidence']}/5.")
    if case.get("soundness") is not None:
        bits.append(f"Your soundness assessment is {case['soundness']}/5.")
    return ("You are an ACL/EMNLP (ARR) reviewer at overall assessment 3/5. "
            + " ".join(bits))


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
