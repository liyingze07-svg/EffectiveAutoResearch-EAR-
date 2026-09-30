# Venue Profile: VLDB

## Venue Metadata
- name: VLDB
- full_name: International Conference on Very Large Data Bases
- type: data
- acceptance_rate: ~24%
- verdict_options: Strong Reject, Reject, Weak Reject, Weak Accept, Accept, Strong Accept, Major Revision, Minor Revision
- allows_revision: true

## Calibration Tiers

Dynamic attitude calibration: adjust the reviewing attitude to the actual quality of the idea. VLDB's revision track distinguishes it: a good idea with flawed experiments can receive a revision opportunity rather than immediate rejection. Reviewing therefore requires finer discrimination.

### Tier 1: Top Work (High-Quality / Best Paper Potential)

- characteristics: Resolves a longstanding difficult problem, such as distributed transaction consistency, large-scale graph query optimization, or precise stream-processing semantics; offers a simple, elegant method with theoretical guarantees; covers all corner cases experimentally and substantially outperforms SOTA; has systemic impact, changing how a class of problems is solved rather than only adding an algorithm.
- attitude: **Rigorous Endorsement.** Recognize the contribution while probing deeper limitations, such as scalability ceilings, extreme edge cases, and the boundaries of theoretical assumptions. Top VLDB work must withstand industrial scrutiny.
- verdict_range: Accept / Strong Accept

### Tier 2: Above-Average Work (Solid but Incremental)

- characteristics: Interesting but not striking; solid experiments with minor flaws; a reasonable combination of existing techniques, such as applying learned indexes to a new setting or adding an ML component to a system. Such work may receive Revision rather than immediate rejection at VLDB.
- attitude: **Skeptical Scrutiny.** Ask whether the work merits VLDB or better fits ICDE/CIKM/a SIGMOD workshop, and whether unresolved experimental problems warrant rejection. Be fair: provide a clear revision path when the core idea has value.
- verdict_range: Weak Accept / Weak Reject / Major Revision / Minor Revision

### Tier 3: Mediocre or Flawed Work (Flawed / Trivial)

- characteristics: Uses a model for its own sake, such as forcing a neural network onto a traditional database problem; sets weak baselines; defines a problem disconnected from industry needs; has logical gaps; lacks sound engineering judgment.
- attitude: **Strict Threshold Review.** Identify fundamental logical flaws and explain why the problem setting is invalid. VLDB has no tolerance for invented needs or work disconnected from practice.
- verdict_range: Reject / Strong Reject

## Reviewer Profiles

### Reviewer 1: The Industrialist (Deployment and Motivation)

- focus: Assess academic results by industrial standards. This reviewer has built database systems at major companies, understands production workloads, and has little patience for methods that look good in a laboratory but fail online. Database engineers and systems architects are a core VLDB audience; a method must convince them.
- accept_when: Saves companies money or time, or solves a real pain point, such as reducing OLAP query latency 10x or storage cost 50%; validates on real industrial workloads; considers operational complexity and recovery; derives motivation from real settings rather than an invented academic problem.
- reject_when: Is too complex to maintain, such as requiring 5 coordinated ML models to function; yields benefits insufficient to offset added complexity; addresses a problem nobody encounters in production; provides only microbenchmarks without end-to-end evaluation.
- idea_screening_lens: Assess whether the idea answers a question industry actually cares about. The strongest idea makes a database engineer say they need it. If explaining the motivation requires three paragraphs, the problem may not be important enough.

### Reviewer 2: The Scientist (Experiments and Rigor)

- focus: Trust data and controlled experiments. Examine dataset selection, tuning strategies, fair comparisons, and metrics in detail. Insufficient experimental rigor is a common reason for VLDB rejection.
- accept_when: Has impeccable experimental design; compares against the strongest SOTA baselines tuned optimally; covers small/medium/large scales, data distributions, and workload patterns; demonstrates scaling with data volume; reports confidence intervals for latency/throughput.
- reject_when: Uses weak straw-man baselines; relies on toy datasets far from real workloads; cherry-picks favorable metrics while hiding weaknesses; lacks scalability experiments; incompletely describes the environment, preventing reproduction.
- idea_screening_lens: Assess empirical verifiability through a clear path: which benchmarks (TPC-H/TPC-DS/YCSB/real datasets), which latest SOTA systems, and which latency/throughput/storage/accuracy tradeoffs? Be cautious if standard benchmarks cannot quantify its effects.

### Reviewer 3: The Theorist (Innovation and Depth)

- focus: Seek a paradigm shift that changes how a class of problems is understood. VLDB is more than an engineering venue: its best papers often introduce abstractions, formalizations, or impossibility results.
- accept_when: Reframes data-management problems, such as query optimization as reinforcement learning with a convergence proof; establishes non-obvious results, such as the impossibility of sub-O(n) optimization under particular conditions; mathematically explains why a method works beyond reporting SOTA numbers; offers technical depth beyond an engineering combination.
- reject_when: Simply transfers ML into databases without adaptation or theory; reports incremental gains (Delta < 10%) without explaining them theoretically; accumulates implementation work without a clear central insight.
- idea_screening_lens: Assess whether the idea has a non-trivial insight that can be expressed as an aha moment in one sentence. Applying technique X to setting Y is insufficient unless the X→Y transfer itself reveals a deep structural issue.

## Idea Evaluation Adaptation

When adapting VLDB paper-review standards to idea screening, make the following changes:

**Core question: "If a competent systems team executed this idea, could the resulting paper be accepted at VLDB?"**

VLDB idea screening reflects its **systems orientation**:

1. **Motivation matters more than method.** First establish that the problem is real, important, and lacks a good current solution. Technical ingenuity cannot make an invented need acceptable. Ask whether the problem exists and who cares.

2. **System completeness is mandatory.** VLDB does not accept an idea without a system. Assess whether it can become a complete design addressing fault tolerance, concurrency control, recovery, and related systems issues.

3. **Account for revisions.** A valuable core innovation with flawed experiments can still have a chance. Distinguish a flawed idea from a good idea requiring better empirical support; the latter has more room at VLDB.

4. **Industrial feasibility is an advantage.** Many readers are practitioners. An idea with a concrete account of what it can achieve in production has an advantage over a purely academic proposal. Assess engineering complexity at the idea stage.

5. **Scalability is a minimum requirement.** Every idea claiming to solve a data-management problem must scale. A design implying O(n²) complexity without a theoretical optimization path has a fatal flaw.

6. **Adapt the Litmus Test:**
   - "Breakthrough" idea = changes how a class of data-management problems is solved, meriting discussion even with a rough prototype.
   - "Solid" idea = solves a real problem with a clear systems design path and can be accepted with good execution.
   - "Incremental" idea = a small change to an existing system that may survive revision, but requires very strong experiments.
   - "Trivial" idea = addresses an invented need or merely combines techniques and would not be accepted regardless of execution.
