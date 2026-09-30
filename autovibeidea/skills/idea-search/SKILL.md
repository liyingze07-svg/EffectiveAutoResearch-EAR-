---
name: idea-search
description: "UCT-guided budget allocation over existing candidate ideas: prior-mask pruning → select the next candidate to expand → generate mechanistically distinct children → score and back up rewards. Use when user says \"search ideas\", \"expand candidates\", \"idea search\", \"tree search\", \"allocate budget\", \"explore this direction further\", or wants to systematically expand and prune a pool of existing candidates instead of generating a fresh batch."
argument-hint: "[-- budget: N] [-- alpha: 0.5] [-- k: 3] [-- venue: ICML]"
allowed-tools: Bash(*), Read, Write, Grep, Glob, WebSearch, WebFetch, mcp__codex__codex, mcp__codex__codex-reply
---

# Idea Search — UCT-Guided Candidate Expansion and Pruning

Arguments: $ARGUMENTS

## Prerequisites

`outputs/IDEA_NODES.jsonl` must already exist and be nonempty (produced by `/idea-gen`). If missing, run `/idea-gen` first.

```bash
python3 tools/idea_nodes.py validate || echo "Fix the node file before continuing"
```

## Constants

- **BUDGET = 8** — Maximum expansions (override with `-- budget: N`). **One expansion = one or more LLM calls = real cost.**
- **ALPHA = 0.5** — Weight of the LLM score in the reward (override with `-- alpha:`). Increasing it makes search rely more on model preferences.
- **K = 3** — Child candidates per expansion (override with `-- k:`).
- **REVIEWER_MODEL = `gpt-5.4`** — (**Model availability depends on your account**: Codex signed in with a ChatGPT account can use only models available to that account; unsupported models return a 400 error. With `--codex-cli`, **do not pass `--model`**; let Codex use its default model. With `--gpt-only`, the model must be available to your OpenAI API key.)

See `docs/SEARCH_DESIGN.md` for the design and full mask/reward definitions. **This is not full MCTS with random rollouts** (value estimates replace rollouts). Do not describe it publicly as "MCTS discovering research problems".

> **External model routes (choose one, routed by `CODEX_MODE`)**
> - Unset → prefer `mcp__codex__codex` / `mcp__codex__codex-reply`. **Note: Codex CLI ≥0.158.0 removed the `mcp-server` subcommand**. In newer environments these two tools are unavailable; use one of the routes below instead of treating this as an error.
> - `CODEX_MODE=codex-cli` → `bash tools/codex_call.sh --thread <thread-file> --output <output-file> --phase <phase> --model REVIEWER_MODEL --config '{"model_reasoning_effort":"xhigh"}' --prompt "..."`. For a new thread, leave the thread file empty; the script writes the thread_id into it. Pass the same file on later calls to automatically `resume` that thread. **No API key required**.
> - `CODEX_MODE=gpt-api` → `bash tools/gpt_call.sh` (same argument format; requires `OPENAI_API_KEY`).
>
> Only when all three routes are unavailable, fall back to local-agent self-evaluation and set `scores.degraded=true` on the node.

## Workflow

### Phase 0: Initialization

```bash
python3 tools/mcts_search.py init --budget <BUDGET> --alpha <ALPHA>
```

### Phase 1: Prior Pruning (Required at the Start of Every Iteration)

```bash
python3 tools/mcts_search.py mask          # Inspect matches first
python3 tools/mcts_search.py mask --apply  # Write after confirmation
```

**Prune before expanding** to avoid spending budget on branches that will be discarded. Check each matching reason:

- `collision` / `not_feasible` / `fit_below_threshold`: Rule-based decisions; accept them.
- `critique_saturated`: Enough candidates already share this evidence anchor; accept pruning and consider another anchor.
- If you judge a match to be a false positive, **do not skip the mask**. Correct the node data (add `delta`, add `falsifier`, or add a `resolution` for a `NOT_FEASIBLE` claim), then rerun the mask.

Record this iteration's pruning count and mask distribution in `outputs/PIPELINE_LOG.md`.

### Phase 2: Selection

```bash
python3 tools/mcts_search.py select -k <K>
```

The output gives the selected node, its `visits`/`Q`/`UCT`, the reward-component breakdown, and expansion instructions.

**If the output warns "no verifiable component; reward comes entirely from LLM scoring"**: First complete the node's `closest_work.delta`, `hypothesis.falsifier`, or `theory_claims`, then select again. Search based only on LLM scores amplifies scoring bias.

### Phase 3: Expansion (Call the External Model)

Generate child candidates with `mcp__codex__codex` (in GPT-only mode, use `bash tools/gpt_call.sh --phase idea-search/expand`):

```
Generate K **mechanistically distinct** child candidates for the research candidate below.

Parent candidate:
  Title: [title]
  Core hypothesis: [hypothesis.core]
  Falsifier: [hypothesis.falsifier]
  Anchored evidence: [generator.anchor]
  Closest work / delta: [closest_work]

Hard constraints (any violation invalidates the child candidate):
1. Differences from the parent must concern the **mechanism**: a different causal pathway, observable, or assumption,
   not merely different wording or a different dataset.
2. Every child must anchor to a specific evidence ID; the anchor cannot be empty. Identify any new critique it addresses.
3. State a falsifier: **what experimental result would disprove it**. Do not produce children without one.
4. Provide closest_work ref and delta. The delta must specify a mechanistic difference.
5. For theoretical claims, identify the type (convergence bound / generalization bound / sample complexity / approximation ratio /
   computational complexity / expressivity / information-theoretic bound / PAC / empirical hypothesis), plus the standard validation protocol and minimum experiment scale.

Return a JSON array; each object contains: id, title, generator{operator,anchor,phase},
hypothesis{core,falsifier}, closest_work{ref,delta}, theory_claims[{claim,type,protocol,feasibility}].
Use `<parent-id>-c<index>` for id.
```

Save the response as a JSON file, then register it:

```bash
python3 tools/mcts_search.py expand <parent-node-id> --children /tmp/children.json
```

**Validation failure rejects the entire batch** (missing anchors, falsifiers, `closest_work.delta`, etc.). Do not relax validation; return to Phase 3 and have the model fill in the missing fields.

### Phase 4: Scoring and Backup

Run `/idea-screen` on each new child (at least Module A novelty checking + Module C), write scores to the node, then run:

```bash
python3 tools/mcts_search.py backup <child-node-id>
```

By default, `backup` computes reward from `scores.composite` and verifiable components, then backs it up along the parent chain.

**Always write `scores.source` and `scores.degraded` with scores**: Fallback self-evaluation is not comparable to normal scoring; mixing them contaminates Q values throughout the tree.

### Phase 5: Loop and Termination

Return to Phase 1 until any condition holds:

- The expansion count reaches BUDGET.
- Every surviving leaf has been visited and Q values stop improving (best Q improves by < 0.02 for two consecutive rounds).
- No nodes survive (all pruned). Record "search space exhausted by pruning" in `PIPELINE_LOG.md`, then return to `/idea-gen` and regenerate with different anchors.

### Phase 6: Report

```bash
python3 tools/mcts_search.py report --provenance > outputs/SEARCH_REPORT.md
```

Append to `outputs/PIPELINE_LOG.md`:

```
## [Timestamp] Idea Search Complete
- Expansions: N / BUDGET
- New candidates: M (X surviving, Y pruned)
- Pruning mask distribution: collision=a, not_feasible=b, fit_below_threshold=c, duplicate=d, critique_saturated=e
- Best candidate: <id> (Q=..., composite=...)
- Median reward breakdown into v_model / v_verifiable: ...
- ⚠️ List any nodes whose reward comes entirely from LLM scores
```

## Key Rules

1. **Prune before expanding.** Phase 1 is mandatory in every iteration.
2. **Search does not improve idea quality; it allocates budget more efficiently.** If the reward signal is biased, search amplifies the bias. Inspect the `--provenance` component breakdown every round.
3. **Never delete pruned nodes.** Pruning records are outputs used to assess pruning precision later.
4. **Children must differ mechanistically.** `tools/dedup_ideas.py` flags reworded candidates; use `mark` to prune them and have the model rewrite them.
5. **This skill does not refine ideas.** After search, run `/idea-refine` on the best candidate.
6. Do not wait for user input. If the external model is unavailable, fall back to local-agent self-evaluation and set `scores.degraded=true` on the node.

## Composing

```
/idea-gen "direction"    → outputs/IDEA_NODES.jsonl (initial candidate pool)
/idea-search -- budget: 8 → expand + prune + rank
/idea-refine "best candidate" → FINAL_PROPOSAL.md
```
