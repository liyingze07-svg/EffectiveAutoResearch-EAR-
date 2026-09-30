# Search Demo

Demonstrates a complete `/idea-search` cycle: `init → expand → backup → mask → report`.

**Data provenance**: The 6 root candidates come from the real run in `examples/judge-run/`. Child candidates (`*-c*`) are **constructed for demonstration**, not outputs of a real LLM generation run. They reproduce the two behaviors below.

## Highlight 1: Verifiable Signals Outweigh LLM Scores

Two child candidates:

| Node | Composite (LLM Score) | feasibility_rule | Total Reward |
|---|---|---|---|
| `IDEA-04-c1` Interventional Identification of Disagreement Components | 7.8 | 1.0 | **0.801** |
| `IDEA-04-c2` Sample Complexity Lower Bound for Disagreement Decomposition | **8.1** (higher) | **0.0** | **0.700** (lower) |

Although `c2` has a higher LLM score, its theoretical claim—sample complexity `Ω(d log n / ε²)`—requires
a label-efficiency experiment with ≥5 labeled fractions according to the claim-type lookup.
Under the given constraints, this was `NOT_FEASIBLE` with no resolution adopted.
Thus `feasibility_rule = 0`, its total reward was lower, and the `not_feasible` mask pruned it.

**This is the purpose of incorporating non-LLM signals**: the model prefers an impressive-sounding theorem, while the rule lookup identifies that it cannot be validated within the constraints.

## Highlight 2: critique_saturated Prunes Only the Weakest Leaves Beyond the Limit

When `CRITIQUE-02` accumulates 4 candidate leaves (limit 3), only the lowest-reward leaf is flagged:

```
[critique_saturated] Critique CRITIQUE-02 has 4 candidate leaves (limit 3); this node ranks 4 by reward and exceeds the limit
```

Parent nodes and high-reward children remain. This boundary matters: an early implementation flagged **every** node under the anchor, pruning parents together with their best children.

## Reproduce

```bash
cd examples/search-demo
python3 ../../tools/mcts_search.py --path IDEA_NODES.jsonl --state SEARCH_STATE.json report --provenance
python3 ../../tools/mcts_search.py --path IDEA_NODES.jsonl --state SEARCH_STATE.json mask
python3 ../../tools/mcts_search.py --path IDEA_NODES.jsonl --state SEARCH_STATE.json select -k 3
```

`SEARCH_REPORT.txt` is an English translation of the original output snapshot, preserving its recorded numbers. Rerunning on translated descriptions may change lexical-overlap components and current rewards; stored visit counts and Q values remain historical. See `docs/SEARCH_DESIGN.md` for the design and mask/reward definitions.

## What This Demo Does Not Establish

- **It does not prove pruning decisions are correct.** False-positive rates for the 5 masks require human review.
- Child candidates are constructed, so the Q-value distribution does not represent a real run.
