---
name: fossil-hunt
description: Systematically find high-value "fossil components" in a research domain — long-standing, consensus-layer building blocks that have never been fundamentally questioned but carry hidden improvement potential. Produces a ranked target list with improvement hypotheses for use as input to /idea-gen. Use when user says "where should I look", "find fossil components", "find fossil components", "find blind spots", "which components to target", or wants a strategic map before brainstorming ideas.
argument-hint: [research-domain]
allowed-tools: Bash(*), Read, Write, Grep, Glob, WebSearch, WebFetch, Agent, mcp__codex__codex, mcp__codex__codex-reply
---

# Fossil Hunt

Systematically search for "fossil components" in this research domain: $ARGUMENTS

## Core Methodology

"Fossil components" are basic modules that have been widely used for years and treated as optimal by consensus without ever being fundamentally questioned. They are valuable targets because of an **epistemic arbitrage opportunity**: the community assumes they are already optimal, even though their environment (scale, hardware, algorithmic ecosystem) has changed by orders of magnitude and the components have never been reassessed.

Start discovery from **symptoms**, not a **list of components**.

---

## Constants

- **REVIEWER_MODEL = `gpt-5.4`** — External review model. (**Model availability depends on your account**: Codex signed in with a ChatGPT account can use only models available to that account; unsupported models return a 400 error. With `--codex-cli`, **do not pass `--model`**; let Codex use its default model. With `--gpt-only`, the model must be available to your OpenAI API key.)
- **MIN_TARGETS = 3** — Minimum number of final targets
- **MAX_TARGETS = 8** — Maximum number of final targets
- **CONFIDENCE_THRESHOLD = 2** — Minimum independent signal streams confirming a target before it enters the final list

---

## Workflow

### Phase 1: Domain Mapping — Competitive Layer vs Consensus Layer

**Goal**: Distinguish heavily contested directions (the competitive layer) from components everyone takes for granted (the consensus layer). Fossil components are found in the consensus layer.

1. Use 2-3 WebSearch queries to establish a basic understanding of the field：
   - `"[domain] survey 2024 2025 open problems future work"`
   - `"[domain] state-of-the-art benchmark 2025 2026"`
   - `"[domain] architecture components modules standard"`

2. Identify the following from search results：
   - **Competitive layer**: Directions pursued by many papers（e.g., scaling, RLHF, MoE routing, architecture search）
   - **Consensus layer**: Modules treated as glue code or standard defaults（e.g., normalization, activation, positional encoding, residual connections, loss function, tokenization, embedding lookup）
   - **"Joints" vs "muscles" in the computation graph**：
     - Muscles = modules doing the main computation (closely scrutinized)
     - Joints = connections and transformations between modules (dismissed as unimportant glue)

3. Produce a classification table to focus the Phase 2 search：
   ```
   Competitive layer (do not search): [list]
   Consensus-layer candidates (search focus): [list]
   Joint locations (high priority): [list]
   ```

**Quick test**: If telling a colleague "I am studying alternatives to X" prompts "Why change that?", X probably belongs to the consensus layer.

---

### Phase 2: Three-Stream Signal Collection

Collect signals along three independent routes in parallel. Each route can produce candidate targets. Cross-validate across routes: candidates identified by multiple routes deserve greater confidence.

#### Route A: Symptom Clustering (Trace Accumulated Workarounds to Root-Cause Components)

**Principle**: When workarounds accumulate around a component, the component itself is implicated. More patches indicate greater underlying design debt.

Procedure:
1. Use 2-3 WebSearch queries for training tricks, hacks, and workarounds in the field：
   - `"[domain] training tricks hacks instability workaround 2024 2025"`
   - `"[domain] loss spike gradient explosion clipping warmup 2024 2025"`
   - `"[domain] training recipe stabilization tips 2024 2025"`

2. Cluster the collected tricks and ask of each: **What root cause does this patch address?**
   - Example: `gradient clipping` + `learning rate warmup` + `Pre-Norm vs Post-Norm debate` → shared root cause: residual connections destabilize hidden-state magnitudes

3. Map each root cause to a candidate target labeled `Signal-A`

#### Route B: Reverse Scan of Strong Primitives (Cross-Dimension Transfer Blind Spots)

**Principle**: A strong primitive proven effective along one dimension often has not been systematically applied to others. Kimi's central insight was to extend attention, effective along the sequence dimension, to the depth dimension.

Procedure:
1. Identify validated **strong primitives** in the field (mature and with manageable overhead)：
   - Common strong primitives: attention, gating, routing (MoE routing), normalization flow, sparse selection, learned interpolation

2. For each strong primitive, list the dimensions where it is currently applied：
   ```
   Primitive: Attention
   Applied dimension: sequence (between tokens) ✓
   Unexplored dimensions: depth (between layers)? Between features/channels? Between attention heads? Vocabulary dimension?
   ```

3. Each "?" identifies a candidate target; label it `Signal-B`

   Run additional searches to verify that these "?" dimensions are genuinely unexplored：
   - `"[primitive] across [dimension] transformer 2024 2025 depth-wise channel-wise"`

#### Route C: Ablation Mining (Unexpected Sensitivity Signals)

**Principle**: Ablation studies in top-venue papers unintentionally probe the consensus layer. Unexpectedly poor results after removing a "standard" component indicate a hidden bottleneck; unexpectedly good results suggest replaceability. Both are direct signals.

Procedure:
1. Use 2-3 searches to find papers reporting surprising ablation findings：
   - `"[domain] ablation study surprising sensitivity normalization activation 2024 2025"`
   - `"[domain] ablation removing [component] unexpected significant impact 2024 2025"`
   - `"[domain] component analysis removing layernorm softmax residual 2024 2025"`

2. Classify each "surprising" finding：
   - **Unexpectedly important** (large performance drop after removal) → the component is a bottleneck; improving it may yield large gains
   - **Unexpectedly unimportant** (little performance change after removal) → the component may be a legacy artifact replaceable with something better

3. Map each surprising finding to a candidate target labeled `Signal-C`

---

### Phase 3: Candidate Target Validation

Apply three checks to every candidate from routes A/B/C to determine whether it is a high-value target worth pursuing.

#### 3a. Scale-Mismatch Check

**Key question**: Does the problem worsen with model or data scale?

- Search for differences in the component's behavior in large versus small models
- If scale amplifies the problem → high value (industry trends will expose it)
- If the problem exists at small scale and is scale-independent → moderate value
- If the problem appears only at small scale and disappears in large models → low value; exclude

#### 3b. Cross-Domain Analogy Check

**Key question**: Does this "fixed" operation already have a mature "adaptive" version in another field (signal processing, control theory, neuroscience, operations research)?

- A "fixed" ML component often already has an "adaptive" counterpart elsewhere
- If a mature solution exists elsewhere → the improvement direction has theoretical support and high feasibility
- If other fields also lack a good solution → this may be a more fundamental hard problem

Example search：`"adaptive [component-concept] control theory signal processing 2020 2021 2022"`

#### 3c. Timing Readiness Check

**Key question**: Is the pain point acute enough, and are the tools to fix it mature?

Timing is right only when both conditions hold：
1. **Acute pain point**: The community widely recognizes the problem but has not correctly attributed it (active attribution = intense competition; attributed but unresolved = good timing)
2. **Mature repair primitives**: Replacement primitives (such as attention or gating) are validated elsewhere and have manageable overhead

The best timing is when **the pain point is becoming widely recognized but has not yet been correctly attributed**.

---

### Phase 4: External LLM Cross-Review

Have an external LLM independently review the candidate list, check for important omissions, and evaluate the quality of each improvement hypothesis.

**Call `mcp__codex__codex`** with：

- **model**: REVIEWER_MODEL (i.e., `gpt-5.4`)
- **config**: `{"model_reasoning_effort": "xhigh"}`
- **prompt**:

```
You are a senior ML researcher with deep expertise in [domain from $ARGUMENTS].

I have identified the following "fossil component" candidates — long-standing, consensus-layer building blocks that may have hidden improvement potential due to environmental drift (scale changes, new hardware, new algorithmic primitives becoming available):

[paste the candidate list from Phases 2-3, with their signal sources and validation results]

Research domain: [domain]

Your tasks:
1. **Coverage check**: Are there high-value fossil components I missed? List up to 3 additional candidates with the signal that makes you think they're worth targeting. Be specific: cite the concrete symptom, scale failure mode, or cross-domain analogue.

2. **Quality review** of each candidate I found: For each candidate, provide:
   - Confidence (HIGH / MEDIUM / LOW) that this is a genuinely underexplored target
   - The single strongest argument FOR pursuing this
   - The single strongest argument AGAINST (most common failure mode or reason it may have already been tried)
   - Whether the "improvement hypothesis" is mechanistically sound

3. **Ranking**: Rank all candidates (including any you added) by expected impact × feasibility. Justify the top 3 placements briefly.

Evaluation criteria:
- HIGH value: Scale-sensitive problem + cross-domain analogue exists + timing is right + social consensus treats it as "solved"
- LOW value: Already crowded space / requires compute we can't access / improvement requires something that doesn't exist yet

Be critical. Many "fossil" hunts fail because the component WAS updated (just not widely cited) or because the update IS hard for a fundamental reason.
```

**Failure handling**: If Codex MCP is unavailable, skip this phase, state "⚠️ Phase 4 skipped: Codex MCP unavailable. External cross-check not performed." in the output, and continue.

---

### Phase 5: Map Improvement Operators

Systematically apply improvement operators to each validated target to generate concrete hypotheses. These operators are recurring patterns in successful prior work:

| Operator | Meaning | Applicable Signal |
|------|------|---------|
| **Static → Adaptive** | Make a fixed operation input-dependent (the most common pattern; Kimi's AttnRes is an example) | Operation ignores input content |
| **Global → Local** | Make a global operation local or sparse | Global operation is too costly for long sequences or large scales |
| **Local → Global** | Introduce global information into a local operation | Local operation cannot capture long-range dependencies |
| **Independent → Coupled** | Introduce interactions among independent units | Independent units process correlated information |
| **Single-scale → Multi-scale** | Replace one granularity with multiple granularities | Phenomena behave differently across scales |
| **Uniform → Selective** | Replace uniform processing with selective processing | Importance varies substantially across positions/features |

For each target, choose the 1-2 best theoretically grounded operators and formulate a concrete hypothesis: "Replace [fixed operation] in [component] with [adaptive mechanism], changing [static property] into [dynamic property]."

---

### Phase 6: Design Validation Metrics

Specify the **right validation metrics** for every final target.

Historical experience: Kimi's central argument was not "a few more benchmark points", but "the same loss with 20% less compute"—a **scaling argument**. Small-scale experiments should emphasize:

- **Changes in the loss-vs-compute curve's slope** (core metric)
- Rather than absolute benchmark scores, which are easily diluted by other factors

For each target, specify:
- A minimum viable experiment (skeleton experiment, feasible in < 1 week)
- The validation metric (prefer scaling exponent to top-1 accuracy)
- The validation scale (small enough for fast iteration, large enough to reveal scale effects)

---

### Phase 7: Output

Ensure `outputs/` exists and write the following file.

#### File 1: `outputs/FOSSIL_TARGETS.md`

```markdown
# Fossil Hunt Report: [domain]

**Date**: [today]
**Domain**: [domain from $ARGUMENTS]
**Signal sources**: Symptom clustering (A) + Primitive scan (B) + Ablation mining (C) + External LLM review (D)
**Candidates identified**: [N total]
**Final targets**: [M after validation]

---

## Methodology Overview

This report uses the "fossil component" methodology to identify basic deep-learning components long assumed optimal but never fundamentally questioned—where epistemic arbitrage opportunities are greatest.

Search path: consensus-layer components + joint locations → three-stream signals (symptom clustering / reverse primitive scan / ablation mining) → triple validation of scale mismatch × cross-domain analogies × timing readiness → improvement-operator mapping

---

## Domain Map: Competitive Layer vs Consensus Layer

### Competitive Layer (Heavily Contested; Not Our Target)
- [list]

### Consensus Layer (Assumed Optimal; Our Search Space)
- [list]

### Joint Locations (Connections/Transformations in the Computation Graph; Highest Priority)
- [list]

---

## Top [M] Fossil Targets (Ranked by Overall Confidence)

---

### Target #1: [component name]

**Signal sources**: [Signal-A/B/C] × [validation results]
**Overall confidence**: HIGH / MEDIUM
**External LLM rating**: HIGH / MEDIUM / LOW

#### Core Problem Diagnosis
- **Fossil symptoms**: [Specific workaround accumulation / scale mismatch / fixed behavior]
- **Implicit assumption**: [What was assumed at design time, and why was it reasonable then?]
- **When the assumption broke**: [Environmental changes that invalidated the original assumption]
- **Scale sensitivity**: [Does the problem worsen with scale? Specific evidence]
- **Cross-domain analogy**: [What corresponding "adaptive" solution exists elsewhere?]
- **Timing assessment**: [Pain-point severity + maturity of repair tools]

#### Improvement Hypothesis
- **Operator**: [Static→Adaptive / Global↔Local / ...]
- **Improvement hypothesis**: Replace [fixed operation] in [component] with [adaptive mechanism], changing [static property] into [dynamic property]
- **Drop-in feasibility**: [Can it be substituted directly without changing interfaces?]

#### Minimum Validation Experiment
- **Skeleton experiment**: [Design feasible in < 1 week]
- **Validation metric**: [Loss-vs-compute curve slope / scaling exponent / ...]
- **Recommended validation scale**: [Model size × token count]

#### Counterargument
- [Why might this direction fail? What is the strongest counterargument?]

---

### Target #2: [component name]
[Same structure as above]

---

[Repeat for all M targets]

---

## Eliminated Candidates

| Candidate | Signal Source | Reason for Exclusion |
|------|---------|---------|
| [component] | Signal-A | [e.g., Not scale-sensitive: the problem disappears in large models] |
| [component] | Signal-B | [e.g., Solved by a 2025 paper that was not widely circulated] |

---

## Recommended Next Steps

1. Use the top-1 target as the direction and run `/lit-survey "[target] rethinking improvement adaptive 2024 2025"` for an in-depth survey
2. Then run `/idea-gen "[target] — [improvement hypothesis]"` to generate concrete ideas
3. To generate ideas directly from this report, run `/idea-gen` with the report's top-1 improvement hypothesis in the direction

---

## Methodological Notes

- **Why start from symptoms rather than component lists**: Brute-force enumeration is inefficient; symptoms provide direct evidence of a component problem
- **Why use scaling exponents instead of benchmark scores**: Absolute scores depend on too many factors; changes in scaling exponents indicate genuine improvement to basic components
- **The basis of epistemic arbitrage**: Environmental change is much faster than component reassessment. Design choices from 2015-2017 were made under entirely different hardware and scale constraints.
```

#### Writing procedure:
1. Ensure `outputs/` exists: `mkdir -p outputs/`
2. Write `outputs/FOSSIL_TARGETS.md` with the Write tool
3. If Write fails because the file is too large, use a Bash heredoc without asking the user

---

## Key Rules

1. **Write all output in English.** Use English for report content, component names, technical terms, and paper titles.

2. **Start from symptoms, not component lists.** Do not enumerate every possible component and ask "Can this be improved?" one by one; that is brute force, not a methodology.

3. **Three-stream cross-validation is essential.** A candidate found by only one route has low confidence unless strongly endorsed by the external LLM. Prioritize targets independently identified by at least two routes.

4. **Timing is key to differentiation.** A problematic component is not enough: repair tools must be mature, and nobody should already be fixing it. Rediscovering a "fossil component" improvement published in 2025 has no value.

5. **Take counterarguments seriously.** Every target needs its strongest counterargument. Positive evidence alone is incomplete. Exclude targets facing compelling objections, such as "the problem resolves itself in large models".

6. **Drop-in feasibility determines impact.** Improvements closer to a drop-in replacement (unchanged interfaces, direct substitution) are easier to adopt and yield greater paper impact. Prefer drop-in hypotheses.

7. **Use scaling exponents, not absolute benchmark scores, for validation.** Improvements to basic components should change the loss-vs-compute slope, not merely a benchmark point.

8. **Do not report the obvious.** If a candidate appears in many recent paper titles, it already belongs to the competitive layer; do not label it a fossil component.

---

## Position in the Pipeline

```
/fossil-hunt "domain"      <- You are here (identify high-value target areas)
/lit-survey "target"      -> In-depth survey focused on a target
/idea-gen "target"        -> Generate concrete ideas
/idea-screen              -> Multidimensional screening
/idea-refine              -> Iterative refinement
/idea-pipeline            -> One-command end-to-end workflow
```

The output of `/fossil-hunt` (improvement hypotheses in `FOSSIL_TARGETS.md`) can directly supply research directions to `/lit-survey` and `/idea-gen`, focusing both skills' searches.
