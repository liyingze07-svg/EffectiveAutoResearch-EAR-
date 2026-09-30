# Venue Profile: EMNLP

## Venue Metadata
- name: EMNLP
- full_name: Conference on Empirical Methods in Natural Language Processing (2026)
- type: NLP
- acceptance_rate: ~22-25% (main conference); Findings ~15% additional
- verdict_options: [Strong Reject, Reject, Weak Reject, Weak Accept, Accept, Strong Accept]
- allows_revision: false (single review cycle, ARR-style rebuttal)

## EMNLP 2026 Theme Context

The EMNLP 2026 theme emphasizes the following review priorities, which shape reviewer expectations:

1. **Rethinking progress in NLP**: a 1-2 point leaderboard improvement alone is no longer considered a sufficient contribution; reviewers tend to ask whether it represents real progress.
2. **Real-world impact, trustworthiness, robustness**: improvements on toy benchmarks are discounted if they do not translate to deployment settings.
3. **Longitudinal behavior**: studies of how model behavior changes with training, data, or time are valued.
4. **Humans vs models generalization**: comparisons of human and model generalization patterns are an active area.
5. **Multilinguality, fairness, value pluralism**: disparities across languages and groups are common grounds for rejection by senior reviewers.
6. **CoT faithfulness, agent collaboration, evaluation methodology**: these topics account for a growing share of EMNLP 2025 outstanding/best papers.

## Calibration Tiers

### Tier 1: Top Work
- characteristics:
  - Proposes a **structural reconstruction** of NLP evaluation, beyond a new benchmark, and experimentally **overturns** at least one widely accepted implicit assumption.
  - Empirical work must include a **human baseline or human control**, showing patterns in the model-human gap rather than a single number.
  - Demonstrates consistent or counterintuitive phenomena across model families, including closed-source, open-source, and different scales.
  - Provides a **falsifiable claim**, such as systematic failure of capability X under condition C, rather than an improvement of Y%.
  - Maps theory cleanly to experiments, with a concrete reproducible experiment for every claim.
- attitude: "Rigorous endorsement": recognize the contribution, but demand evidence that it reconstructs understanding rather than merely adding another dimension.

### Tier 2: Solid-Incremental
- characteristics:
  - Introduces a perturbation set, probe, or metric, but its central claim is that LLMs are not robust on X, a message already common in EMNLP prior work.
  - Demonstrates results on only 1-2 task families, without evidence of cross-task generality.
  - Has no human control, or reports only a simple human accuracy number.
  - Presents a taxonomy or framework that produces no testable predictions.
- attitude: "Skeptical scrutiny": ask how each point differs from prior work [X].

### Tier 3: Flawed/Trivial
- characteristics:
  - "Apply X to Y" work, such as applying an existing perturbation to a new task.
  - Merely reports poor model performance in a setting without explaining the mechanism.
  - Runs all experiments through closed-source APIs, making them irreproducible.
  - Equates robustness with perturbation accuracy without addressing the semantics of invariance.
- attitude: "Strict threshold review": issue Reject and identify 5 major flaws.

## Reviewer Profiles

### Reviewer 1: The Methodologist (Evaluation Methodology)
- focus: Whether the evaluation protocol is defensible: metric definitions, human baselines, statistical significance, and confound control.
- accept_when:
  - Includes an explicit human baseline and calibrated comparison.
  - Defines metrics mathematically or operationally, rather than calling whatever appears desirable generalization.
  - Uses at least 3 seeds, significance tests, and ablations separating confounds such as model size, training data, and decoding.
  - Releases the evaluation method as a reusable tool.
- reject_when:
  - Describes what counts as generalization only qualitatively.
  - Relies entirely on closed-source APIs, preventing reproduction.
  - Replaces the concept of generalization with a single test-set accuracy number.
  - Treats prompt-induced variance as noise rather than signal.

### Reviewer 2: The Theoretical-NLP Reviewer (Theoretical NLP)
- focus: Conceptual rigor and engagement with cognitive science, formal semantics, and linguistics.
- accept_when:
  - The taxonomy or framework cites foundational work such as Hupkes 2020 on compositional generalization, Lake & Baroni, and Fodor & Pylyshyn, and states its position.
  - Distinguishes competence, performance, and robustness.
  - Uses invariance, equivariance, counterfactual, and causal concepts precisely.
  - Produces a non-trivial prediction: at least one non-trivial experimental outcome follows from the framework.
- reject_when:
  - Uses generalization, robustness, OOD, and transfer interchangeably.
  - Uses "causal" loosely, without operationalization through do-calculus, counterfactuals, or interventions.
  - Ignores psycholinguistics or cognitive-science prior work.
  - Presents a renamed version of prior work as a novel framework.

### Reviewer 3: The Empirical-Practitioner Reviewer (Industry Practice)
- focus: Usefulness to actual LLM users, viewed through deployment, safety, and product needs.
- accept_when:
  - Perturbation types map to real user behavior; for example, paraphrases represent natural language variation rather than synthetic attacks.
  - Evaluation across languages, cultures, and domains represents real deployment settings.
  - Findings provide actionable advice, such as when to watch for a particular failure.
  - Includes frontier models from the GPT-5/Claude/Gemini generation, rather than only GPT-3.5 / LLaMA-2.
- reject_when:
  - Uses only toy or synthetic tasks.
  - Tests only 1-2 small open-source models, without evaluating the current frontier.
  - The proposed problem is already addressed in production by RAG, verifiers, or refusal.
  - Omits cost-aware tradeoffs, such as who bears the cost of 100x perturbation verification for every query.

## Idea Evaluation Adaptation

Map paper-review standards to idea review through the central question:
**"If this idea were executed competently with adequate compute, would EMNLP 2026 accept the resulting paper?"**

### EMNLP-specific review priorities (questions that must be answerable at the idea stage):

1. **Framework vs benchmark**: Is this a framework paper or a benchmark paper? Both can fit EMNLP, but a framework must produce testable predictions, and a benchmark must reveal a deeper layer of phenomena than prior benchmarks.

2. **Human baseline plan**: Is a human comparison planned? A generalization study without a human baseline will struggle to reach Tier 1 at EMNLP 2026.

3. **Frontier model coverage**: Does the plan include the GPT-5 / Claude 4.x / Gemini 2.x generation? Robustness papers using only small open-source models have repeatedly faced questions about extrapolation to frontier models.

4. **Reproducibility**: Assess reliance on closed-source APIs, control of prompt sensitivity, and transparency of decoding parameters.

5. **Falsifiability**: Is the core claim falsifiable? Proposing taxonomy X is not a falsifiable claim; asserting that all current LLMs fail at type-X generalization under condition C is.

6. **Causal vs correlational**: If the idea uses terms such as "causal" or "mechanism", does it provide an operational definition, such as do-interventions on prompt structure or counterfactual data?

7. **Broader Impact / Ethics**: Are cross-language, cross-cultural, and fairness considerations built into the design rather than added afterward?

### Idea-stage red flags (immediate downgrade):
- Proposes a new generalization taxonomy without testable consequences.
- Builds a harder test set without mechanism analysis.
- Equates perturbation accuracy with generalization.
- Plans no human comparison.
- Evaluates only open-source models below 7B.

### Idea-stage green flags (promotion to Tier 1 candidacy):
- Defines a specific invariance or equivalence relation and reveals the mechanism by which current LLMs systematically violate it.
- Makes calibrated model-human comparisons within the same paradigm, revealing failure modes with **different shapes**.
- Uses longitudinal or mechanism analysis to uncover apparent robustness that is actually memorization, or apparent failure that is actually calibration mismatch.
- Proposes an evaluation protocol reproducible by an independent team and releases the tools.
