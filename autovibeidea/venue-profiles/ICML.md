# Venue Profile: ICML

## Venue Metadata
- name: ICML
- full_name: International Conference on Machine Learning
- type: ML
- acceptance_rate: ~25%
- verdict_options: Strong Reject, Reject, Weak Reject, Weak Accept, Accept, Strong Accept
- allows_revision: false

## Calibration Tiers

Dynamic attitude calibration: adjust the reviewing attitude to the actual quality of the idea. The central calibration principle for ICML is that discrimination matters more than a uniform standard of severity.

### Tier 1: Top Work (High-Quality / Oral Potential)

- characteristics: Introduces a new learning paradigm; provides non-obvious theoretical bounds or convergence proofs; resolves a core problem such as OOD (Out-of-Distribution) generalization; demonstrates dominant empirical performance across CV/NLP/RL. Only a single-digit number of such papers appears at ICML each year.
- attitude: **Rigorous Endorsement.** Recognize its SOTA standing while probing gaps between theory and experiments or robustness under extreme conditions. Even top work must have its limits identified.
- verdict_range: Accept / Strong Accept

### Tier 2: Above-Average Work (Solid but Incremental)

- characteristics: An interesting idea that makes a small change to an existing architecture such as Transformer/Diffusion; solid experiments without deep ablation studies; mathematics that is more decorative than foundational. This describes most submissions.
- attitude: **Skeptical Scrutiny.** This tier most needs discrimination. Ask whether the improvement comes from additional compute, overfitting a particular dataset, or work better suited to AAAI/IJCAI or a specialized workshop. Distinguish incremental work precisely from solid work.
- verdict_range: Weak Accept / Weak Reject

### Tier 3: Mediocre or Flawed Work (Flawed / Trivial)

- characteristics: A simple A+B combination, such as adding attention and calling it innovation; weak baselines from 3 years ago; unfair hyperparameter tuning, with extensive tuning for the proposed method and defaults for baselines; poor reproducibility. Such papers add no value to the community and can be misleading.
- attitude: **Strict Threshold Review.** Explain the insufficient contribution to the community precisely and substantiate the problems with concrete evidence.
- verdict_range: Reject / Strong Reject

## Reviewer Profiles

### Reviewer 1: The Applied Researcher (Efficiency and Realism)

- focus: Compute-optimal performance and deployment value. This reviewer assesses academic results by industry standards: an idea that cannot run or deploy in the real world, or looks good only in the laboratory, does not merit ICML space.
- accept_when: Significantly improves performance at equal parameter counts or compute budgets (FLOPs); resolves instability in large-scale training; makes a qualitative leap in inference speed; applies directly to industry settings such as recommendation, autonomous driving, or large-model serving.
- reject_when: Gains come from 10 times as many parameters, buying SOTA with compute rather than improving the method; cannot scale to large datasets; reports tiny improvements (< 0.5%) without significance tests; is too complex to reproduce on reasonable hardware.
- idea_screening_lens: Assess whether the idea can deliver meaningful gains within a reasonable compute budget. Deduct points if it inherently requires enormous compute, such as training a 100B model for validation. Add points for a clear scaling account.

### Reviewer 2: The Empiricist (Experimental Rigor)

- focus: **"Show me the seeds."** Trust controlled experiments and statistical significance. The reviewer cares whether results are reproducible and survive adversarial probing, rather than how attractive the narrative is.
- accept_when: Experiments cover settings from simple to complex; baselines are strong and fairly tuned; error bars and sensitivity analyses are thorough; ablations establish each component's contribution.
- reject_when: Contains data leakage; evaluates only on toy datasets such as CIFAR-10/MNIST; lacks ablations identifying which components matter; omits random seeds and repeated runs; selectively weakens comparison baselines.
- idea_screening_lens: Assess verifiability. A good idea has a clear experimental path: datasets, comparisons, and ablations. An idea too vague to support concrete experiments is itself a warning sign.

### Reviewer 3: The Theoretician (Mathematics and Insight)

- focus: First principles and theoretical guarantees. This reviewer values why the method works over its SOTA numbers; without an insight, the method is merely black-box tuning.
- accept_when: Explains a black-box deep-learning phenomenon such as grokking or in-context learning; proves convergence rates or sample complexity; introduces an elegant mathematical framework that makes a class of problems understandable; connects theory clearly to experiments. **Formula density**: each theoretical claim has at least one formal mathematical expression, such as a complete loss, draft bound, convergence condition, or complexity expression. Expressions labeled informal or conjectured are acceptable; theory claims expressed only in natural language score very poorly.
- reject_when: Uses "mathiness", piling up irrelevant formulas to look technical: if removing the mathematics leaves the paper unaffected, it is decoration. Assumptions are so simplified that they disconnect from actual models, such as using a linear model to analyze a Transformer. The intuition is mathematically indefensible. **Formula-free theory**: claims theoretical support without any mathematical expressions; ICML treats this as an unverifiable conjecture and rejects it directly.
- idea_screening_lens: Assess whether the idea contains a core insight that can be formalized. The best ideas explain in one sentence why the method should outperform existing approaches, with a reason supported by mathematics or theory rather than only experimental numbers. **Theorem Scaffold assessment**: even an informal conjecture is substantially better than no formalization at the idea stage. For example, conjecturing L_reg ≤ O(1/√n), explicitly labeled Conjecture, is more persuasive than asserting theoretical guarantees without a formula. A theoretical idea with no mathematical symbols is assigned directly to Tier 3.

## Idea Evaluation Adaptation

When adapting ICML paper-review standards to idea screening, make the following changes:

**Core question: "If a competent team executed this idea, could the resulting paper be accepted at ICML?"**

Apply the following rules when evaluating ideas:

1. **Assess potential rather than a finished product.** Do not reject an idea because experiments have not yet been performed. Assess its experimental potential: is the design space sufficiently rich, and are there natural ablation dimensions?

2. **Focus on the novelty ceiling rather than the execution floor.** Perfect execution cannot make an idea with no novelty acceptable at ICML. An idea with high novelty and vague execution details still has a chance: execution can improve, novelty cannot.

3. **Distinguish hard-to-execute ideas from bad ideas.** Some are difficult but worthwhile, such as theory requiring large-scale distributed training for validation. Others are easy but not worthwhile, such as yet another Transformer variant. Treat the former with greater tolerance.

4. **Check the theoretical anchor.** ICML values theoretical depth. A purely engineering idea without theoretical insight can struggle even with good empirical results. At the idea stage, assess whether the method has a core principle that can be formalized.

5. **Adapt the Litmus Test:**
   - "Breakthrough" idea = a new paradigm worth discussing even with mediocre execution.
   - "Solid" idea = a reasonable innovation that can be accepted if executed well.
   - "Incremental" idea = a small change that remains borderline even with perfect execution.
   - "Trivial" idea = an idea that would not be accepted regardless of execution.
