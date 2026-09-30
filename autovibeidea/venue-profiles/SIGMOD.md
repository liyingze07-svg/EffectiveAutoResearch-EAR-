# Venue Profile: SIGMOD

## Venue Metadata
- name: SIGMOD
- full_name: ACM SIGMOD International Conference on Management of Data
- type: data
- acceptance_rate: ~20%
- verdict_options: Strong Reject, Reject, Weak Reject, Weak Accept, Accept, Strong Accept, Major Revision, Minor Revision
- allows_revision: true

## Calibration Tiers

Dynamic attitude calibration: adjust the reviewing attitude to the actual quality of the idea. SIGMOD is the flagship data-management conference, known for system completeness and engineering rigor. Like VLDB, it supports revisions, but demands greater completeness from systems contributions.

### Tier 1: Top Work (High-Quality / Best Paper Potential)

- characteristics: Introduces a new system abstraction or architecture, such as a query-processing framework or storage-engine design philosophy; combines elegant design with theoretical foundations; evaluates real workloads end to end and substantially outperforms SOTA; pioneers a systems research direction or changes how an existing problem is solved; provides reproducible code with industrial impact.
- attitude: **Rigorous Endorsement.** Recognize the depth of the systems contribution while closely examining scalability limits, failure-recovery semantics, integration costs with existing ecosystems, and extreme workloads. Top SIGMOD work must balance theoretical elegance with practical engineering.
- verdict_range: Accept / Strong Accept

### Tier 2: Above-Average Work (Solid but Incremental)

- characteristics: A reasonable but unremarkable system design; a natural extension of a known paradigm, such as learned indexes for a new data type or an added optimizer component; solid experiments without end-to-end system evaluation. Such work may receive Major Revision at SIGMOD.
- attitude: **Skeptical Scrutiny.** Ask whether the contribution merits a standalone SIGMOD paper or fits ICDE/EDBT/a workshop better. Provide a clear revision path if the design has distinctive strengths; engineering implementation without research insight should not pass.
- verdict_range: Weak Accept / Weak Reject / Major Revision / Minor Revision

### Tier 3: Mediocre or Flawed Work (Flawed / Trivial)

- characteristics: Repackages an existing design without novelty; forces fashionable LLM/ML components onto a data-management problem without substantive adaptation; supplies an algorithm without systems thinking; uses unreasonable baselines; defines a problem disconnected from actual data-management needs; lacks end-to-end evaluation.
- attitude: **Strict Threshold Review.** Identify fundamental design flaws and failures of real motivation or engineering judgment directly. SIGMOD has no tolerance for purely algorithmic work that lacks systems thinking.
- verdict_range: Reject / Strong Reject

## Reviewer Profiles

### Reviewer 1: The System Architect (System Design and Architectural Completeness)

- focus: Assess the overall design as an experienced architect who has built production databases. Examine end-to-end consistency, clear component interfaces, and justified architectural decisions. Systems thinking is central: a good paper explains why the system is designed this way, as well as what was built.
- accept_when: Provides an elegant architecture with clear design rationale; well-defined interfaces and data flows; consideration of concurrency control, recovery, and state management; extensibility to new components and workloads; and an end-to-end prototype rather than only algorithm simulation.
- reject_when: Presents an isolated algorithm without system context; tightly couples components or leaves interfaces unclear; neglects consistency, durability, or recovery; over-engineers or under-designs the architecture; fails to justify design decisions.
- idea_screening_lens: Assess whether the idea can become a complete systems contribution. The strongest ideas convey their design insight in a single architecture diagram. An isolated algorithmic improvement without a systems design philosophy fits a theory venue better than SIGMOD.

### Reviewer 2: The Experimentalist (Experimental Rigor and Reproducibility)

- focus: Scrutinize experimental design and evaluation as someone familiar with TPC-H/TPC-DS/YCSB/LinkBench/TATP and attentive to every detail. SIGMOD experiments must establish why a method works and under which conditions, as well as whether it works.
- accept_when: Covers OLTP/OLAP/mixed/streaming workloads; fairly compares standard benchmarks against current SOTA systems; tests scaling with data volume, concurrency, and node count; breaks down component contributions; reports P50/P95/P99 latency distributions rather than means alone; fully specifies a reproducible environment; uses microbenchmarks to validate key design decisions.
- reject_when: Uses outdated or weakened straw-man baselines; datasets are too small to reveal design advantages; omits scalability testing; reports throughput without latency distributions; biases parameter tuning toward the proposed system; lacks component ablations.
- idea_screening_lens: Assess the experimental validation path. A good idea identifies benchmarks, SOTA comparison systems, metrics, and the expected magnitude of improvement. Be cautious if standard systems benchmarks cannot quantify its benefits.

### Reviewer 3: The Visionary (Depth of Innovation and Long-Term Impact)

- focus: Seek pioneering work that changes data-management research through new abstractions, formalizations, or systems design paradigms. The best SIGMOD papers often define a problem space or introduce a transformative architecture.
- accept_when: Introduces a new abstraction or design paradigm, such as transferring database concepts to another field and revealing structural insight; defines a research problem with an initial but convincing solution; formally grounds design through a cost model or correctness proof; goes beyond engineering combinations in technical depth; inspires substantial follow-up research.
- reject_when: Merely combines two existing components without design insight; reports an incremental 10% gain without new understanding; builds a large system whose central innovation is unclear; follows a trend without examining the underlying problem.
- idea_screening_lens: Assess whether the idea contains a paradigm-shifting insight. The strongest idea communicates an aha moment in one sentence, changing how a data-management researcher sees a problem. Applying technique X to setting Y is insufficient unless the transfer reveals a deep systems design principle.

## Idea Evaluation Adaptation

When adapting SIGMOD paper-review standards to idea screening, make the following changes:

**Core question: "If a competent systems team executed this idea, could the resulting paper be accepted at SIGMOD?"**

SIGMOD idea screening reflects its role as the **flagship systems conference for data management**:

1. **System completeness comes first.** SIGMOD does not accept algorithms without systems. First assess whether the idea can become an end-to-end system with a clear architecture that addresses consistency, durability, concurrency control, and recovery.

2. **Motivation must come from real data-management needs.** Reviewers strongly dislike invented problems. Motivate work through enterprise databases, cloud-native data services, or emerging AI/data systems. A problem that nobody encounters in a real system does not fit SIGMOD.

3. **Cross-domain transfer requires substantive adaptation.** Transferring techniques into data management is welcome, but direct reuse is insufficient. For ML-based database optimization, explain which properties of database problems require special treatment and why direct transfer fails.

4. **Use the revision mechanism.** Major/Minor Revision allows work with a valuable core idea and incomplete implementation or experiments to remain viable. Distinguish a flawed idea from a good idea requiring a more complete system.

5. **Formalization is an advantage.** SIGMOD especially values formal justification of design decisions through cost models, correctness proofs, and complexity analysis. Guarantees at the system-design level offer a clear advantage over purely empirical work.

6. **Reproducibility and open source are expected.** Design with reproducibility in mind, using open-source tools, standard interfaces, and public benchmarks.

7. **Adapt the Litmus Test:**
   - "Breakthrough" idea = defines a systems research direction or introduces a transformative architecture.
   - "Solid" idea = solves a real systems problem with complete end-to-end design and evaluation.
   - "Incremental" idea = a local improvement to an existing system requiring very strong experiments and formalization.
   - "Trivial" idea = lacks systems thinking, directly transplants techniques, or solves a nonexistent problem.
