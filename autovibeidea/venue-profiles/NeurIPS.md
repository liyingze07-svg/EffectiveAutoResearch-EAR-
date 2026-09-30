# Venue Profile: NeurIPS

## Venue Metadata
- name: NeurIPS
- full_name: Conference on Neural Information Processing Systems
- type: ML
- acceptance_rate: ~25%
- verdict_options: Strong Reject, Reject, Weak Reject, Weak Accept, Accept, Strong Accept
- allows_revision: false

## Calibration Tiers

Dynamic attitude calibration: adjust the reviewing attitude to the actual quality of the idea. NeurIPS is more receptive than ICML to interdisciplinary work, creative new directions, and contributions with societal impact. Calibration should reflect this openness without lowering core quality standards.

### Tier 1: Top Work (High-Quality / Oral or Spotlight Potential)

- characteristics: Introduces a transformative paradigm or perspective; excels in both theory and experiments; resolves a longstanding challenge such as generalization, causality, or scalable inference; influences multiple fields, inspiring subsequent CV, NLP, and RL work; or uncovers important empirical findings through large-scale studies. NeurIPS particularly values seed papers that open a new research direction, even when current experiments are limited, if the idea has major potential impact.
- attitude: **Rigorous Endorsement.** Recognize pioneering contributions while examining generality: does the method depend excessively on particular assumptions? Does it hold under broader conditions? Does the Broader Impact statement honestly discuss potential risks?
- verdict_range: Accept / Strong Accept

### Tier 2: Above-Average Work (Solid but Incremental)

- characteristics: A somewhat novel method that naturally extends existing work; positive experiments without surprising findings; correct but shallow theory; or a useful engineering contribution without conceptual insight. This tier also includes interesting directions with incomplete execution. NeurIPS is more willing than ICML to give such work a chance when the idea itself is sufficiently interesting.
- attitude: **Curious Scrutiny.** Slightly more tolerant than ICML Tier 2: consider whether the idea opens an interesting direction despite imperfect execution. Still ask whether the contribution is significant enough, or merely repeats a known method on new data.
- verdict_range: Weak Accept / Weak Reject

### Tier 3: Mediocre or Flawed Work (Flawed / Trivial)

- characteristics: No clear core contribution; combines known techniques without new insight; has clear experimental flaws such as unfair comparisons, data leakage, or missing ablations; makes theoretical claims unsupported by experimental evidence; or omits or gives superficial treatment to Broader Impact.
- attitude: **Strict Threshold Review.** Identify the central problems directly. NeurIPS maintains strict quality thresholds despite its openness; openness does not imply accepting everything.
- verdict_range: Reject / Strong Reject

## Reviewer Profiles

### Reviewer 1: The Empiricist (Large-Scale Experiments and Reproducibility)

- focus: Large-scale empirical validation and reproducibility. This reviewer represents the community's emphasis on scale and reproducibility, expecting rigorous experiments on realistically sized benchmarks, repeated runs, and error bars. They take the NeurIPS reproducibility checklist particularly seriously.
- accept_when: Experiments cover scales and settings from synthetic data to real large datasets; provide complete reproducibility details, including code, hyperparameters, compute, and random seeds; use comprehensive ablations to establish each component's marginal contribution; compare fairly and comprehensively with current SOTA baselines; reveal interesting scaling behavior.
- reject_when: Evaluates only small or outdated datasets, such as claiming to solve vision problems using only CIFAR-10; lacks reproducibility information, a code-release commitment, or hyperparameter details; omits error bars or reports suspiciously small ones; uses outdated or unfairly tuned baselines; reports statistically insignificant gains.
- idea_screening_lens: Assess whether the idea can withstand rigorous large-scale validation. A good NeurIPS idea has a clear experimental account: at what scale should it work, how should it change with more data/models/compute, and what natural ablations exist? An idea verifiable only in a toy setting will struggle.

### Reviewer 2: The Innovator (Paradigm Shifts and Creativity)

- focus: Paradigm shifts and creative framing distinguish NeurIPS. Its best papers often open new directions instead of optimizing existing ones. This reviewer seeks work that changes how the problem itself is understood and considers interdisciplinary links between ML and neuroscience, cognitive science, statistical physics, and related fields.
- accept_when: Introduces a new perspective on an old problem, such as reformulating optimization as game theory to obtain new insight; offers clear, deep, illuminating intuition; opens a research direction despite imperfect experiments; successfully transfers valuable concepts from neuroscience, physics, economics, or other fields to ML; thoughtfully considers Broader Impact and ML's societal consequences.
- reject_when: Trivially extends an existing method, such as adding a loss term or changing normalization; claims novelty already covered by prior work due to an incomplete literature review; innovates only in implementation rather than concepts; uses superficial interdisciplinary framing that could be removed without affecting the paper.
- idea_screening_lens: Assess the novelty ceiling. Would the best possible execution excite the NeurIPS community and attract more than 100 citations? NeurIPS accepts high-risk, high-reward ideas: a potentially unsuccessful idea with major impact if it works should score above a sure success with limited impact.

### Reviewer 3: The Rigorist (Theoretical Depth and Formal Analysis)

- focus: Theoretical depth and mathematical rigor, reflecting NeurIPS traditions in learning theory, optimization, and information theory. Not every paper needs a theorem, but every paper needs rigorous thinking through formal theory or principled methodology.
- accept_when: Provides convergence, generalization, or sample-complexity guarantees; uses reasonable assumptions with explicit scope; connects theoretical predictions to empirical observations; derives the method from clear principles even without a theorem, rather than assembling ad-hoc tricks. **Formula density (rigorous informality)**: accept explicit conjectures with corresponding empirical validation. For example, conjecturing generalization error ≤ O(1/√n) by analogy with PAC-Bayes and testing it in Section 4 is more persuasive than natural-language claims alone, even without a formal proof.
- reject_when: Uses irrelevant formulas to create an illusion of depth; mathematics whose removal leaves the paper unchanged is decoration. Assumptions disconnect from practice, such as assuming convex optimization to analyze deep learning. Proofs contain errors or logical gaps. Theory analyzes a simplified model unrelated to the experimental method. **Derivation without principles**: explains decisions only by saying an attempted change worked, or claims theoretical contributions without mathematical symbols; this signals insufficiently serious method design.
- idea_screening_lens: Assess the principled foundation. A complete theory is unnecessary, but there must be a clear argument for why the method should work. Intuition is acceptable if it withstands logical scrutiny; merely having tried something successfully invites criticism. **Theorem Scaffold assessment**: check for a draft core mathematical claim, even an informal one. Conjecturing sample complexity O(d/ε²) by analogy with ridge regression is much stronger than asserting good theoretical properties. The Rigorist scores conjectures with empirical support well above narrative-only ideas.

## Broader Impact Consideration

NeurIPS requires a Broader Impact statement in all papers. At the idea-screening stage:

- **Positive:** explicitly considers beneficial and harmful societal effects; builds fairness/privacy/robustness into the method; has an application with clear societal value.
- **Negative:** leaves obvious dual-use risks undiscussed; may amplify existing bias without acknowledging it; assumes idealized applications that ignore real ethical constraints.
- **Neutral:** a pure-theory Broader Impact statement may be brief, but must not be absent.

## Idea Evaluation Adaptation

When adapting NeurIPS paper-review standards to idea screening, make the following changes:

**Core question: "If a competent team executed this idea, could the resulting paper be accepted at NeurIPS?"**

NeurIPS idea screening reflects its breadth as a leading ML conference:

1. **Broader scope than ICML.** NeurIPS accepts pure theory, pure experiments, methodology, applications, benchmarks/datasets, and even position papers through workshops. Do not reject an idea solely because it departs from the standard new-method-plus-experiments format.

2. **High-risk, high-reward principle.** The community is receptive to creative, bold ideas. An idea that might fail but would be highly influential if successful should score higher here than at ICML. Distinguish risky-but-exciting from flawed-and-uninteresting.

3. **Interdisciplinary advantage.** The Neural and Information Processing traditions connect neuroscience, cognitive science, statistical physics, and computer science. Ideas importing perspectives from outside ML have better opportunities here than at ICML.

4. **Broader Impact is substantive.** The community takes AI's societal effects seriously. Considering fairness, privacy, and environmental cost at the idea stage gives work an advantage over ignoring them.

5. **Empirical contributions have value.** Unlike ICML's theoretical preference, NeurIPS accepts purely empirical contributions when experiments are large enough, findings sufficiently surprising, and results useful to the community, such as scaling laws or large-scale benchmarks. Do not automatically downgrade ideas lacking theory.

6. **Adapt the Litmus Test:**
   - "Breakthrough" idea = opens a new direction or explains a known phenomenon in a new way, meriting publication even with limited execution.
   - "Solid" idea = makes a clear contribution in a defined direction and can be accepted with good execution.
   - "Incremental" idea = a natural extension without surprise, requiring very strong experiments to clear the threshold.
   - "Trivial" idea = offers no value to the NeurIPS community regardless of execution.
