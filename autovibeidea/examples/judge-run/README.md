# Example Run: LLM-as-a-Judge

**Sanitized, abridged version.** Retains workflow evidence—stage timestamps, critique-manifest format, screening scores, fallback records, and a complete record of an overturned novelty judgment—while omitting idea mechanisms and full proposals.

- **Direction**: LLM-as-a-Judge bias, calibration, and social choice theory
- **Target venue**: EMNLP 2026
- **External model**: gpt-5.5 via Codex MCP, `model_reasoning_effort=xhigh`
- **Actual duration**: First pass 16:31 → 17:25 (54 minutes across 4 stages); full rescreening and refinement followed the next day

## Three Things to Notice

### 1. Novelty scores can be overturned substantially

The first screening assigned IDEA-06 a novelty score of **8/10**. A deeper second-round search found three close prior works **missed** by the initial `lit-survey`. Its novelty fell to **4/10**, and its recommendation changed from CAUTION to **ABANDON**. Another idea fell from 8 to 5.

See `SCREENING_RANKED.excerpt.md` for the full record. This illustrates the project's `README.md` limitation: **"No similar work found" means only that no collision was found within the current search coverage**. Inspecting `closest_work.delta` is more useful than reading the novelty score alone.

### 2. Ideas anchor to critiques, not gaps

`CRITICAL_ANALYSIS.excerpt.md` is a Phase 2a artifact (16 critiques in full; 3 retained here). Each critique names **which assumption in which published work it challenges**. Every Phase 2b idea must identify the critique it addresses.

### 3. Pruning records are themselves outputs

`IDEA_NODES.jsonl` reconstructs this run's 6 candidates using the current node schema (see `docs/IDEA_NODE_SCHEMA.md`), **including both pruned candidates** and their `prune.mask`. Run:

```bash
python3 ../../tools/idea_nodes.py --path IDEA_NODES.jsonl validate
python3 ../../tools/idea_nodes.py --path IDEA_NODES.jsonl stats
python3 ../../tools/dedup_ideas.py --path IDEA_NODES.jsonl pairs --top 3
```

## An Essential Caveat

Scores were assigned by gpt-5.5 through Codex MCP. They are **not peer reviews and do not predict acceptance**. Before reading any score, inspect `scores.degraded`: self-evaluation when the external model is unavailable is not comparable to normal scoring.
