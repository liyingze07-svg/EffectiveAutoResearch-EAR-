---
name: exp-design
description: Experiment-design skill. Design paper experiments from first principles, treating reviewers as the audience and organizing evidence around two pillars—method validity and method utility—while strictly controlling cost. Load when planning new experiments or reviewing existing ones.

---

# Experiment Design from First Principles

> Every experiment exists to convince reviewers of a specific claim. An experiment without a supporting claim wastes resources.

---

## Core Principle: Will Reviewers Be Convinced?

Experiments are not a box to check; they must **persuade**. Before designing any experiment, answer:

1. **What do I want the reviewer to believe?** (A specific claim in one sentence)
2. **Why do they not believe it yet?** (Their prior belief or concern)
3. **What result would change their mind?** (The expected data pattern)

If these questions cannot be answered, do not run the experiment.

---

## Two Pillars

Organize all experiments around these two goals; stay within their scope:

### Pillar A: Method Validity ("Are Your Theoretical Predictions Accurate?")

Reviewer concern: Your theory assumes simplified conditions (a perfect oracle, fixed bandwidth), unlike the real world.

**Response strategy**: Show close agreement between theoretical predictions and experimental measurements.

Typical experiments:

- Measure a predictable quantity (e.g., per-gate accuracy or round ratio)
- Compare it directly with the theoretical prediction
- Plot "theory vs experiment"; closer curves indicate better agreement

### Pillar B: Method Utility ("What Can Your Theory Guide?")

Reviewer concern: Even if the theory holds on toy problems, how does it relate to real tasks?

**Response strategy**: Show that theoretical predictions agree with actual performance across multiple downstream tasks or real-world scenarios.

Typical experiments:

- Select tasks with different structures, covering different theoretical regimes
- Validate the theoretical prediction on each task
- Include at least one real-world case study; not all tasks may be synthetic

---

## Experiment-Design Workflow

### Step 1: List Every Paper Claim

Starting from the abstract and introduction, list each claim and record:

- Whether it needs experimental support (theoretical claims do not; modeling assumptions and utility claims do)
- The smallest experiment that supports it

### Step 2: Check Existing Data

**Do not rerun good existing data.** Reviewers will not be suspicious merely because results are strong. For each claim:

- Can existing data support it? → Reuse directly
- Are there problems with the data (wrong model, insufficient scale)? → Rerun
- No data available? → Design a new experiment

**Reuse principle**: Existing data may need only **reinterpretation** (relabeling/reframing), not recollection. For example, AND/OR tree data can be relabeled as "CSP experiments with treewidth=1".

### Step 3: Design New Experiments (Minimality Principle)

For each claim needing new data:

1. **Find the simplest design** that can test the claim
2. **Estimate cost** (prompt count, inference time, whether new prompts must be designed)
3. **Check per-step accuracy**: Run a pilot first (100 prompts) to confirm that the LLM can perform single-step evaluation. If it cannot, switch tasks instead of proceeding
4. **Check discriminative power**: Can the result distinguish correct from incorrect theory? If both predict the same outcome, the experiment is uninformative

### Step 4: Prioritize

| Priority | Criterion |
| --------------- | --------------------------------- |
| **P0 Required** | The core claim lacks support without this experiment |
| **P1 Strongly recommended** | Strengthens the argument and addresses likely reviewer concerns |
| **P2 Nice to have** | Helpful, but absence should not affect acceptance |

**Run only P0 and P1 initially.** Consider P2 only after all P0/P1 experiments are complete and resources remain.

---

## Cost Control

### Hard Constraints

| Constraint | Limit | Rationale |
| ------------------------- | -------- | ---------------------------- |
| Total prompts per batch | ≤ 100K | Shared GPU server; avoid occupying it too long |
| Inference time per run | ≤ 1 hour | Same reason |
| max_tokens per prompt | ≤ 16 | Experiment outputs are usually 1-2 tokens |
| Model selection | Smallest sufficient model | Do not use 27B if 9B suffices |
| Total experiment rounds | ≤ 3 | Includes pilot + main run + supplementary run |

### Cost Estimation Template

Calculate before submitting any experiment:

```
Experiment: B3 Treewidth Prediction
Prompt count: 4 (tw) × 3 (sizes) × 50 (inputs) × ~100 (gates/input) = ~60,000
Estimated inference time: 60K prompts × ~60 tokens/prompt ÷ 3800 tokens/sec ≈ 16 minutes
Within budget: ✅ < 100K prompts, < 1 hour
```

### Pilot Principle

**Run a pilot before every new experiment.** Use 1/10 of the main experiment's scale (e.g., 10 inputs instead of 100).

Pilot checks:

1. Prompt format is correct and LLM outputs are parseable
2. Per-step accuracy > 80% (otherwise change tasks or prompts)
3. Results discriminate between conditions

**Run the full experiment only after the pilot passes.** This avoids wasting an hour only to discover a prompt error.

---

## Experiment Architecture: Three Separate Phases

Use the same architecture for all experiments (validated as the most stable setup):

```
Phase 1: Local generation (generate_prompts.py)
  - Construct all prompts using ground-truth values
  - Output: all_prompts.json

Phase 2: GPU-server inference (run_inference.py)
  - Load model once → batch_chat → release
  - Output: all_results.json

Phase 3: Local analysis (analyze_results.py)
  - Parse outputs → compute metrics → generate figures
```

**Do not make sequential calls through an API server.** This has proved unstable (broken tunnels, timeouts, repeated model loading).

### Why Ground-Truth Inputs Are Appropriate

> "Why use ground-truth child-node values instead of the LLM's own outputs?"

Because the target is **the reliability of each oracle call**, not **end-to-end protocol accuracy**. This is the paper's core claim: whether the LLM is a reliable oracle.

End-to-end accuracy can be derived from the per-gate error rate:

- Tree: P_correct ≈ (1-ε)^depth
- Chain: P_correct ≈ (1-ε)^(n-1)

There is no need to run the end-to-end protocol itself.

---

## Presenting Experimental Results

### One Clear Claim per Experiment

| Experiment | Claim (One Sentence) | Presentation |
| ---- | ---------------------------- | ----------------------------------------------- |
| A1 | The LLM is a reliable oracle | Table: per-gate accuracy by gate type and depth |
| A2 | Round ratio matches theory | Table + Figure: empirical vs n/log₂n |
| A3 | Locality is the causal factor | Table: accuracy vs prompt locality |
| B1 | The framework generalizes | Table: accuracy on non-AND/OR tasks |
| B3 | Separation varies with treewidth | Figure: separation ratio vs treewidth |
| B4 | The framework is useful in practice | Case study narrative + data |

### Do Not Present Data Unconnected to a Claim

If a result supports no claim (e.g., 5% accuracy on an iterated function), either:

1. Identify the claim it supports ("the oracle assumption fails for arithmetic" → a scope limitation of the framework)
2. Leave it out of the paper

### Handling Negative Results

Negative results (e.g., "trees offer no advantage on sequential tasks") are **valuable** because they validate the theory's precision: not "trees solve everything", but "tree advantages depend on task structure".

Place negative results in the Discussion, framed as "the theory correctly predicts regimes where trees have no advantage".

---

## Pitfalls to Avoid

### Pitfall 1: Wrong Experiment Scale

Too small → insufficient statistical evidence. Too large → wasted resources.

Rules of thumb:

- Per-gate accuracy: ≥ 500 evaluations per condition (confidence interval ±2%)
- Comparing two conditions: ≥ 1000 evaluations per condition
- Scaling experiments: at least 3 scale points to reveal a trend

### Pitfall 2: Measuring Model Ability Rather Than Topological Differences

If the LLM cannot perform even one step (e.g., only 5% accuracy on (3x+7)%256), the experiment measures model ability, not topological differences.

**Check**: Per-step accuracy must exceed 80% to be meaningful. Below 80%, change the task.

### Pitfall 3: Excessive Experiments

Three thorough experiments are better than 10 shallow ones. Reviewers care about persuasiveness, not count.

Each experiment should occupy 0.5-1 paper pages. With a 9-page NeurIPS main text and at most 3-4 pages for experiments, plan **at most 5-6 experiments**.

### Pitfall 4: Forgetting Ablations

Every core claim needs an ablation: if A causes B, remove A and test whether B disappears. Without ablation, there is no causal evidence, only correlation.

---

## Checklist

After designing experiments, check each item:

- [ ] Every experiment maps to an explicit claim
- [ ] All reusable existing data have been reused
- [ ] New experiment costs are estimated and within budget
- [ ] Every new experiment has a pilot plan
- [ ] Per-step accuracy is confirmed > 80%
- [ ] Both positive and negative results are included (not "everything works")
- [ ] Total experiment count ≤ 6 (more is not necessarily better)
- [ ] Every claim has an ablation supporting causality
- [ ] Presentation is planned (table / figure / narrative)
