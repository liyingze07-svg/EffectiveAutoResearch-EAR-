# Search Design: UCT-Guided Expansion with Prior Mask Pruning

## Is This MCTS?

This implementation covers three of the four standard MCTS stages:

| Stage | Status | Implementation |
|---|---|---|
| Selection | ✅ | UCT1: `Q(n) + c·sqrt(ln N_parent / N_n)`; unvisited nodes receive ∞ and must be visited once first |
| Expansion | ✅ | **Performed by an external model.** The tool outputs the next node and expansion instructions; `/idea-search` invokes the LLM to generate children |
| Simulation (rollout) | ❌ **Absent** | A research idea cannot be randomly simulated to a terminal outcome |
| Backup | ✅ | Back up evaluation values along the parent chain, updating `visits` and `value_sum` |

The precise description is **UCT-guided best-first expansion, with value estimates replacing rollout**: AlphaZero-style value substitution rather than full MCTS with random simulation. The README capability levels use this description.

## Why Search Allocates Expansion Budget

Each expansion requires one or more LLM calls and incurs real cost. Search therefore does not traverse a static space:
it **allocates a limited LLM-call budget among candidates**, deciding which candidate to expand first and when to abandon a branch.
`--budget` counts expansions; `report` prints this alongside measured token usage from `IDEA_NODES.jsonl`.

## Masks: Prior Pruning

Prune **before expansion** to avoid spending budget on branches already known to be unsuitable. All five masks use verifiable signals:

| Mask | Trigger | Signal type |
|---|---|---|
| `collision` | `closest_work.ref` exists but `delta` is empty (incomplete novelty verification), or `evidence_collision=true` (retrieval confirms published work with the same mechanism) | External retrieval fact |
| `not_feasible` | A theoretical claim has `feasibility=NOT_FEASIBLE` without a `resolution`, or `hypothesis` has no `falsifier` | Rule lookup / structural completeness |
| `fit_below_threshold` | `researcher_fit < 12` | Rule threshold |
| `duplicate` | Recorded after adjudication through `tools/dedup_ideas.py` | Computation + adjudication |
| `critique_saturated` | More than 3 **candidate leaves** share one evidence anchor; flag those with the lowest reward | Structural diversity constraint |

Two boundaries ensure that `critique_saturated` means stop investing in a branch, rather than discard existing work:

1. **Consider leaves only.** A parent with surviving children represents a branch, not a redundant sibling candidate. Pruning it would invalidate all its children.
2. **Keep the top 3 by reward** and flag only the excess. An early implementation flagged every node under the anchor, pruning parents and the best children together.

Pruned nodes **are not deleted**. `prune.all_hits` records every reason for later pruning-precision analysis (see group D in `ABLATIONS.md`).

## Reward: State the Signal Sources

```
reward = alpha × v_model + (1 - alpha) × v_verifiable        # alpha defaults to 0.5
```

`v_model = scores.composite / 10` is **produced by an LLM**.

`v_verifiable` averages the following available components, excluding missing ones:

| Component | Source | Type |
|---|---|---|
| `retrieval` | Whether retrieval found published work with the same mechanism / whether `delta` is provided | External fact |
| `feasibility_rule` | Fraction passing claim-type → validation-protocol lookup | Rule |
| `falsifiability` | Whether a falsifier is provided | Structure |
| `cost_efficiency` | Measured token usage relative to candidates in the same batch | Measurement |
| `distinctness` | Lexical/concept overlap with **candidates outside the lineage**, following the lineage rules in `dedup_ideas.py` | Computation |

`report --provenance` prints this source table for each node and explicitly warns when no verifiable components are available.

### Why Include Non-LLM Signals?

**If reward comes entirely from LLM scores, expanding search amplifies the scoring model's preferences**, making candidates collapse toward its preferred proposals. Empirical findings support this concern: work using execution rewards for RL has reported higher mean reward without an improved best result.

In the measured example under `examples/`, the child with the higher LLM composite score (8.1 vs 7.8) received a lower total reward (0.700 vs 0.801) because protocol lookup marked its theoretical claim `NOT_FEASIBLE`. **This is the intended effect of including verifiable signals.**
