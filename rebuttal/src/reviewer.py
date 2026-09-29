"""The reviewer-simulator DSPy module (CoT role-play -> raise/same/lower).

The Signature docstring is the θ₀ instruction; MIPROv2 will later rewrite this
instruction and attach few-shot demos while keeping the backbone LM frozen.
"""
from typing import Literal
import dspy


class ReviewerReaction(dspy.Signature):
    """You are role-playing a specific ICLR peer reviewer. Given your reviewer
    profile, your original review, and the authors' rebuttal addressed to you,
    decide how you would revise your overall rating after reading the rebuttal.

    Think as this reviewer: weigh whether the rebuttal actually resolves the
    weaknesses and questions you raised, or merely restates the paper. Reviewers
    rarely change their score; only move it when the rebuttal materially changes
    your assessment. Output `raise`, `same`, or `lower`."""

    paper_title: str = dspy.InputField()
    reviewer_profile: str = dspy.InputField(desc="who you are as a reviewer")
    review: str = dspy.InputField(desc="your original review")
    rebuttal: str = dspy.InputField(desc="the authors' response to you")
    reaction: Literal["raise", "same", "lower"] = dspy.OutputField(
        desc="how you revise your score after the rebuttal"
    )


class ReviewerSimulator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.predict = dspy.ChainOfThought(ReviewerReaction)

    def forward(self, paper_title, reviewer_profile, review, rebuttal):
        return self.predict(
            paper_title=paper_title,
            reviewer_profile=reviewer_profile,
            review=review,
            rebuttal=rebuttal,
        )
