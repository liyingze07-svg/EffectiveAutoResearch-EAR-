# IDEA_NODES.jsonl — Ideas as Auditable Objects

## Why This Is Needed

Previously, the pipeline produced linear Markdown, which caused three problems:

1. **No unified answer to why an idea was retained or pruned.** Rejection reasons were scattered across stage reports.
2. **No precise cost accounting.** There was no unit for measuring expenditure per candidate.
3. **No basis for tree search.** Nodes, parent-child relations, and pruning reasons were missing.

`outputs/IDEA_NODES.jsonl` stores one structured idea record per line as a JSON object. It provides a shared foundation for MCTS pruning and cost accounting in the Roadmap.

## Fields

| Field | Type | Description |
|---|---|---|
| `id` | str | `IDEA-01`, unique within the run |
| `parent_id` | str \| null | Derivation source: a refined revision or a variant split from another idea. Roots use `null` |
| `run_id` | str | Timestamp identifying a pipeline run |
| `status` | enum | `pending` / `supported` / `refuted` / `impl_failed` / `shelved` / `pruned`. **Distinguish scientific refutation (`refuted`) from code failing to run (`impl_failed`): the former is a valuable result; the latter is not** |
| `generator.operator` | enum | Generating operator: `critique_anchored` / `fossil_hunt` / `entropy_region` / `failure_mode` / `manual` |
| `generator.anchor` | list[str] | Evidence IDs such as `CRITIQUE-03`, `G2`, or `FM-05` |
| `generator.phase` | str | Generation stage, such as `idea-gen/2b` |
| `title` / `thesis` | str | Title / one-sentence claim ("We show that X by Y") |
| `evidence` | list | Evidence that the problem exists: `{kind: paper\|code\|experiment_observation, ref, note}` |
| `closest_work` | obj | `{ref, delta}`: closest prior work and substantive difference. **An empty delta means novelty verification is incomplete** |
| `hypothesis.core` | str | Core hypothesis |
| `hypothesis.falsifier` | str | **The result that would refute the hypothesis**. If none can be specified, it is not falsifiable |
| `min_experiment` | obj | `{design, budget:{gpu_hours, wall_clock_h}}` |
| `theory_claims` | list | `{claim, type, protocol, feasibility}`, from the Theory-Experiment Alignment Matrix |
| `scores` | obj | Per-dimension scores + `composite` + `researcher_fit` + `source` (**who scored it**) + `degraded` (**whether external evaluation fell back to self-evaluation**) |
| `prune` | obj | `{pruned, reason, mask}`. `mask` ∈ `collision` / `not_feasible` / `fit_below_threshold` / `duplicate` / `critique_saturated` |
| `review_log` | list | `{round, overall, verdict, top2}` |
| `cost` | obj | `{tokens_in, tokens_out, wall_clock_s, external_calls}` |

## Design Conventions

- **`scores.source` and `scores.degraded` are required.** Scores without provenance are meaningless: fallback self-evaluation is not comparable to standard external evaluation.
- **`prune.mask` records the pruning mechanism, not a natural-language explanation.** This supports per-mask counts and precision estimates: how many pruned candidates actually warranted pruning.
- **Do not delete pruned nodes.** Keep them in the file with `status=pruned`. Knowing what was excluded is a major part of search's value.

## Usage

```bash
python3 tools/idea_nodes.py init                       # Create an empty file
python3 tools/idea_nodes.py add --file node.json       # Append a node with validation
python3 tools/idea_nodes.py update IDEA-03 --set status=pruned --set prune.mask=collision
python3 tools/idea_nodes.py validate                   # Validate all nodes
python3 tools/idea_nodes.py stats                      # Summarize status/operators/masks/cost
python3 tools/idea_nodes.py tree                       # Print derivation lineage
```
