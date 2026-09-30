# EAR Workflow Guide

## 1. End-to-End Flow

```
                        [Research topic input]
                             │
                             ▼
                   ┌─────────────────────┐
                   │   Stage 1           │
                   │   /lit-survey       │──→ LANDSCAPE.md + LANDSCAPE.json
                   │   Literature Survey │
                   └────────┬────────────┘
                            │ Gap Matrix (5-15 gaps, 6 types)
                            ▼
                      ◆ Checkpoint 1 ◆
                            │
                            ▼
                   ┌───────────────────┐
                   │   Stage 2         │
                   │   /idea-gen       │──→ IDEAS_RAW.md + IDEAS_FILTERED.md
                   │   Idea Generation │
                   └────────┬──────────┘
                            │ 4-6 surviving ideas
                            ▼
                      ◆ Checkpoint 2 ◆
                            │
                            ▼
                   ┌──────────────────────────────┐
                   │   Stage 3                    │
                   │   /idea-screen               │──→ SCREENING_REPORT.md + SCREENING_RANKED.md
                   │   Multidimensional Screening │
                   └────────┬─────────────────────┘
                            │ Top 1-2 ideas (Composite >= 7.0)
                            ▼
                      ◆ Checkpoint 3 ◆
                            │
                            ▼
                   ┌───────────────────┐
                   │   Stage 4         │
                   │   /idea-refine    │──→ FINAL_PROPOSAL.md + REFINEMENT_REPORT.md
                   │   Deep Refinement │
                   └────────┬──────────┘
                            │
                            ▼
                      ◆ Checkpoint 4 ◆
                            │
                            ▼
              [IDEA_DISCOVERY_REPORT.md summary report]
```

---

## 2. Stage 1: Literature Survey in Detail

### Goal
Search and analyze papers from multiple sources to map the field and identify research gaps.

### Internal Flow

```
[Research topic]
     │
     ├──→ Step 0a: Zotero search (MCP)
     │         │ Collections, tags, annotations, BibTeX
     │         ▼
     ├──→ Step 0b: Obsidian search (MCP)
     │         │ Research notes, tag references, WikiLinks
     │         ▼
     ├──→ Step 0c: Local PDF scan
     │         │ papers/ or literature/ directories
     │         │ Read the first 3 pages per paper, up to 20 papers
     │         ▼
     └──→ Step 1: Web search
               │ arXiv API + Semantic Scholar + Google Scholar
               │ Deduplicate (skip known papers)
               ▼
          Step 2: Analyze each paper
               │ Extract: problem/method/results/limitations/connections
               │ Assign Paper ID: P01, P02, ...
               │ Goal: 15-30 papers
               ▼
          Step 3: Synthesis and Gap Identification
               │
               ├── 3a: Thematic synthesis (3-7 themes)
               │       Label each theme: active / mature / emerging
               │
               └── 3b: Gap matrix
                       │
                       │   6 gap types:
                       │   ┌─────────────────────────────┐
                       │   │ cross-domain transfer       │
                       │   │ untested assumption         │
                       │   │ resolution opportunity      │
                       │   │ scaling frontier            │
                       │   │ missing diagnostic          │
                       │   │ overlooked formulation      │
                       │   └─────────────────────────────┘
                       │   Confidence: HIGH / MEDIUM / LOW
                       │   Goal: 5-15 gaps
                       ▼
          Step 4: Output
               ├── LANDSCAPE.md  (Narrative + tables + gap matrix)
               └── LANDSCAPE.json (Structured, for downstream use)

          (Optional) Step 4c: Trajectory tracking
               ├── Publication trajectories of the top 3 authors
               └── Coauthor cluster map (2-4 research groups)
```

### Data Source Priority

| Priority | Source | Content |
|--------|------|----------|
| 1 | Zotero (MCP) | Collections, tags, PDF highlights, BibTeX |
| 2 | Obsidian (MCP) | Research notes, links between papers |
| 3 | Local PDFs | Original PDF content (first 3 pages) |
| 4 | Web search | arXiv, Semantic Scholar, Google Scholar |

> Graceful degradation: if MCP is not configured, skip it and use local PDFs + web search.

### Output Files

- **`outputs/LANDSCAPE.md`** -- Includes Executive Summary, Paper Table, Thematic Analysis, Gap Matrix, Trajectory Analysis, and References
- **`outputs/LANDSCAPE.json`** -- Structured JSON with fields: `papers[]`, `themes[]`, `gaps[]`, `trajectory{}`

---

## 3. Stage 2: Idea Generation in Detail

### Goal
Generate 8-12 ideas from the literature landscape and apply multiple filters to retain 4-6 strong directions.

### Funnel (v2: Two-Phase Generation)

```
         ┌─────────────────────────────────────────────────────┐
         │      Phase 1: Landscape validation                  │
         │  Read LANDSCAPE.json (or run a quick inline survey) │
         └───────────────────┬─────────────────────────────────┘
                             ▼
         ┌──────────────────────────────────────────────────────────────────┐
         │   Phase 2a: Landscape critique ← new in v2                       │
         │  gpt-5.4 · xhigh · New thread                                    │
         │  Systematically critique structural weaknesses in the landscape: │
         │    ① Unverified Assumptions                                      │
         │    ② Incorrectly Generalized Methods                             │
         │    ③ Experimental Design Flaws                                   │
         │    ④ Cross-Domain Misfits                                        │
         │  Output: CRITIQUE-01...N critique list                           │
         │  Save: outputs/CRITICAL_ANALYSIS.md                              │
         └───────────────────┬──────────────────────────────────────────────┘
                             │ CRITIQUE manifest
                             ▼
         ┌────────────────────────────────────────────────────────┐
         │   Phase 2b: Critique-grounded idea generation ← v2     │
         │  gpt-5.4 · codex-reply (Same thread)                   │
         │  Each idea must anchor to at least one CRITIQUE-ID     │
         │  Each idea contains 11 fields:                         │
         │    Title / Anchored Critique (new in v2)               │
         │    Thesis / Problem / Mechanism                        │
         │    Non-obvious                                         │
         │    Theorem/Conjecture Scaffold (new in v2)             │
         │    Contribution type / Risk                            │
         │    Effort / Closest work                               │
         │  Diversity: ≥50% of ideas anchor to distinct critiques │
         └───────────────────┬────────────────────────────────────┘
                             │ 8-12 ideas
              ╔══════════════╧════════════════════════════════╗
              ║    Phase 3: Initial screening (three filters) ║
              ╚══════════════╤════════════════════════════════╝
                             │
┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
│ 3a Feasibility    │ │ 3b Novelty        │ │ 3c Impact         │
│                   │ │ Quick check       │ │ "So What?"        │
│ FEASIBLE /        │ │ LIKELY NOVEL /    │ │ HIGH /            │
│ CAVEATS /         │ │ NEEDS CHECK /     │ │ MEDIUM /          │
│ INFEASIBLE        │ │ ALREADY DONE      │ │ LOW               │
└───────────────────┘ └───────────────────┘ └───────────────────┘
          └──────────────────┬──────────────────┘
                            │ Eliminated: INFEASIBLE / ALREADY DONE / LOW IMPACT
                            │ Remaining: 5-8 ideas
                            ▼
              ┌────────────────────────────────────────────────┐
              │ Phase 4: Professor He's four-dimension scoring │
              │                                                │
              │  Longevity     (1-5)                           │
              │  Passion       (1-5)                           │
              │  Application   (1-5)                           │
              │  Uniqueness    (1-5)                           │
              │                                                │
              │  Pass threshold: >= 12/20                      │
              └─────────────┬──────────────────────────────────┘
                            │ 4-6 ideas
                            ▼
              ┌────────────────────────────────────────────────┐
              │ Phase 5: Anti-pattern check                    │
              │                                                │
              │  1. Overly trendy (Trend chasing)              │
              │  2. Overly niche  (Too narrow)                 │
              │  3. A+B stitching (Stitched combination)       │
              │  4. Scale-dependent(Scale dependence)          │
              │                                                │
              │  Flag warnings; do not automatically eliminate │
              └─────────────┬──────────────────────────────────┘
                            │
                            ▼
              ┌────────────────────────────┐
              │ Phase 6: Output            │
              │  IDEAS_RAW.md (All 8-12)   │
              │  IDEAS_FILTERED.md (4-6)   │
              └────────────────────────────┘
```

### Output Files

- **`outputs/IDEAS_RAW.md`** -- All generated ideas (including elimination records)
- **`outputs/IDEAS_FILTERED.md`** -- Surviving ideas ranked by He Score + elimination table + risk distribution

---

## 4. Stage 3: Multidimensional Screening in Detail (Core Innovation)

### Goal
Evaluate each idea across three modules to produce a composite score and recommended action, parallelizing where dependencies allow.

### Three-Module Architecture

```
Input: 4-6 ideas
    │
    ├── Module A: Novelty assessment
    │      4-phase workflow; multisource search; cross-validation
    │      → Novelty 0-10
    │
    ├── Module B: Reviewer simulation (after Module A)
    │      3 reviewers + Meta Review
    │      → Venue 0-10
    │
    └── Module C: Strategic assessment (can run alongside Module B)
           5 dimensions; local assessment
           → Strategic 0-10

Novelty + Venue + Strategic + Feasibility (0-10)
    │
    ▼
Composite Score: weighted composite scoring
    │
    ▼
Rank + Recommend
```

> **Execution dependency**: Module A must finish before Module B (B needs A's novelty score and closest prior work). Module C can run in parallel with B.

---

### Module A: Novelty assessment (4 Phases)

```
Phase A: Extract core claims
    │  Identify 3-5 technical claims that must be novel
    ▼
Phase B: Multisource literature search
    │  Web search (arXiv/Scholar) + cross-references to LANDSCAPE.json
    │  At least 3 search strategies per claim
    │  Year filter 2024-2026
    ▼
Phase C: Cross-model verification
    │  gpt-5.4 · xhigh reasoning
    │  For each claim, answer:
    │    1. Has the exact mechanism already been published?
    │    2. Are there closely related alternative approaches?
    │    3. Would reviewers at the target venue consider it sufficiently novel?
    ▼
Phase D: Novelty report
    │  Score: 0-10
    │  Recommendation: PROCEED / CAUTION / ABANDON
    │  Each claim: HIGH / MEDIUM / LOW
    └──→ Closest-prior-work comparison table
```

### Module B: Reviewer simulation

```
Step 1: Load venue profile
    │  venue-profiles/{VENUE}.md
    │  Extract: calibration tiers + reviewer profiles + verdict options
    ▼
Step 2: Build review prompt (English)
    │  Inject: idea description + novelty score (from Module A)
    │  gpt-5.4 · xhigh reasoning
    ▼
Step 3: Three independent reviewers
    │
    │  Reviewer 1 (Applied researcher): Efficiency/scalability/real-world impact
    │  Reviewer 2 (Empiricist): Experimental rigor/baselines/reproducibility
    │  Reviewer 3 (Theorist):     Novelty/mathematical depth/insight
    │
    │  Each reviewer provides:
    │    Calibration tier (Tier 1/2/3) + strengths + weaknesses + verdict + "What would make me accept"
    ▼
Step 4: Meta Review
    │  Key disputes (reviewers should disagree)
    │  Final verdict + top 3 execution risks
    ▼
Step 5: Verdict → Numeric mapping
    │  Strong Reject=1, Reject=3, Weak Reject=4
    │  Weak Accept=6, Accept=8, Strong Accept=10
    │
    └──→ Venue Score = Mean of three reviewers (1 decimal place)
```

### Module C: Strategic assessment (5 dimensions)

| Dimension | Score Range | Key Question |
|------|---------|----------|
| **Longevity** Durability | 1-10 | Will researchers still care about this problem in 5 years? |
| **Roadmap Viability** Roadmap | 1-10 | After Paper 1, what are Papers 2 and 3? |
| **Application Grounding** Practical grounding | 1-10 | Who outside academia would care about this result? |
| **Execution Uniqueness** Execution uniqueness | 1-10 | Why this team rather than Google/DeepMind/FAIR? |
| **Iteration Readiness** Iteration speed | 1-10 | How quickly can we determine whether this idea works? |

**Strategic Score** = Mean across 5 dimensions (1 decimal place)

---

### Composite Scoring Formula

```
COMPOSITE = 0.25 * Novelty + 0.35 * Venue + 0.20 * Strategic + 0.20 * Feasibility
```

| Weight | Module | Source |
|------|------|------|
| 0.25 | Novelty (Novelty) | Module A |
| 0.35 | Venue (Venue review) | Module B |
| 0.20 | Strategic (Strategic fit) | Module C |
| 0.20 | Feasibility (Feasibility) | Inherited from idea-gen or estimated by the local agent |

> Override weights with the `-- weights:` directive.

### Decision Thresholds

```
 COMPOSITE >= 7.0  ──→  PROCEED         Enter /idea-refine for deep refinement
 5.0 <= COMP < 7.0 ──→  PROCEED WITH CAUTION  Address weaknesses before refinement
 COMPOSITE < 5.0   ──→  ABANDON         Archive; stop investing effort
```

### Output Files

- **`outputs/SCREENING_REPORT.md`** -- Full three-module report per idea + composite calculation
- **`outputs/SCREENING_RANKED.md`** -- Ranked table + concise reports + next steps

---

## 5. Stage 4: Deep Refinement in Detail

### Goal
Develop a rough idea into a concrete, submission-ready proposal using a Problem Anchor, Skeleton, and iterative review.

### Iterative Refinement Loop (v2: Theoretical Grounding + Socratic Mode + Deep Expansion)

```
Phase 0: Problem Anchor (Anchoring)
    │  Freeze the immutable core problem:
    │    Core problem / required bottleneck / non-goals / constraints / success criteria
    ▼
Phase 0.5: Skeleton Extraction (Skeleton extraction)
    │  State A: What does the reviewer currently believe?
    │  State B: What must the reviewer believe after reading?
    │  Skeleton Path: 3-5 indispensable logical steps
    │  Save to refine-logs/skeleton.md
    ▼
Phase 1: Build Proposal (Build initial proposal)
    │  1.1 Scan source material (local papers + web)
    │  1.2 Identify technical gaps
    │  1.3 Choose the sharpest route (Route A: minimal and elegant vs Route B: frontier-native)
    │  1.4 Specify the method (11 required items)
    │  1.4.T ← v2 Theoretical grounding:
    │      T1 Formalizability Scan — Identify formalizable mechanisms and draft equations
    │      T2 Assumption Inventory — List assumptions and label STANDARD/RESTRICTIVE/UNVERIFIED
    │  1.4.TE ← v2 Theory-Experiment Alignment Matrix:
    │      Map each theoretical claim to a standard validation protocol (ML subfield conventions)
    │      ┌───────────────────────────────────────────────────────────────────────────────┐
    │      │ Convergence bound → Training curves + learning-rate sensitivity (≥3 seeds)    │
    │      │ Generalization bound → Data-scaling experiments (≥4 scales)                   │
    │      │ Sample complexity → Label-efficiency experiments (≥5 fractions)               │
    │      │ Approximation ratio → Synthetic instances compared with exact solutions (≥20) │
    │      │ Computational complexity → wall-clock + FLOP (≥5 sizes)                       │
    │      │ Expressivity → Constructive proof + empirical separation on synthetic tasks   │
    │      │ ...                                                                           │
    │      └───────────────────────────────────────────────────────────────────────────────┘
    │      NOT FEASIBLE claim → ⚠️ Theory-Experiment Gap (Provide three alternatives)
    │  1.5 Evaluation outline
    │  1.6 Write round-0-initial-proposal.md
    ▼
Phase 2 Entry: Mode selection ← new in v2
    │
    ├── Default (no -- mode) ──→ Standard review loop (below)
    ├── -- mode: socratic-auto ──→ Socratic dialogue loop (fully automatic)
    └── -- mode: socratic-human ──→ Socratic dialogue loop (human-in-the-loop)

────────────────────────────────────────────────────────
Standard path (default):
────────────────────────────────────────────────────────

┌─→ Phase 2: External Review (External review)
│       │  gpt-5.4 · xhigh reasoning · 7-dimension scoring
│       │
│       │  7 scoring dimensions:
│       │  ┌─────────────────────────────────────────────────────┐
│       │  │ Problem Fidelity     Problem fidelity     15%       │
│       │  │ Method Specificity   Method specificity     25%     │
│       │  │ Contribution Quality Contribution quality       25% │
│       │  │ Frontier Leverage    Frontier leverage     15%      │
│       │  │ Feasibility          Feasibility         10%        │
│       │  │ Validation Focus     Validation focus      5%       │
│       │  │ Venue Readiness      Venue readiness      5%        │
│       │  └─────────────────────────────────────────────────────┘
│       │  Verdict: READY (>=9) / REVISE / RETHINK
│       ▼
│   Phase 3: Top-2 Diagnosis + Revise (Diagnosis and revision)
│       │  3.1 Parse review feedback → update score-history.md
│       │  3.2 Top-2 diagnosis (fix only the 2 biggest problems)
│       │      ├── Where will readers become confused?
│       │      ├── What would a hostile reviewer write?
│       │      └── Which skeleton step is broken?
│       │  3.3 Skeleton Gap Check (Skeleton completeness check)
│       │  3.4 Revise (with Anchor Check + Simplicity Check)
│       ▼
│   Phase 4: Re-evaluation (Re-review in the same thread)
│       │  gpt-5.4 · codex-reply (Same thread)
│       │  Re-score 7 dimensions + Drift Warning
│       │
│       ├── Score >= 9 and READY and no drift? ──Yes──┐
│       │                                          │
│       └── No (and round < 3) ──→ Return to Phase 3      │
│                                                  │
└── (Up to 3 revision rounds)                                 │
                                                   ▼
────────────────────────────────────────────────────────
Socratic path (-- mode: socratic):     ← new in v2
────────────────────────────────────────────────────────

    Phase 2S: GPT asks questions (Turn 0, New thread)
        │  Rule: no scoring until it declares full understanding
        │  Per turn: 3-5 concrete mechanism questions (not vague criticism)
        │    Good: "Is the Step2 loss supervised or self-supervised?"
        │    Bad:  "The method is unclear"
        ▼
    Turn Handler (Up to 5 turns):
        │
        ├── Detect "I fully understand this method" ──Yes──→ Final scoring ──┐
        │                                                  │
        ├── Extract questions → [socratic-human mode: PAUSE for human input]  │
        │             [socratic-auto mode: local agent answers automatically] │
        │                                                  │
        └── Integrate answers + expand proposal → continue dialogue                   │
                                                           │
    (Force scoring at MAX_TURNS=5)                            │
                                                           │
    One scoring pass (7 dimensions) → go directly to Phase 5.5 ◄────────────────┘

────────────────────────────────────────────────────────
Both paths converge:
────────────────────────────────────────────────────────

Phase 5.5: Deep Expansion Pass ← new in v2 (Run on both paths)
    │  Scan the best current proposal for [EXPAND] sections:
    │    ├── Method component has prose only, no equations/pseudocode → [EXPAND]
    │    ├── Loss is named but not defined → [EXPAND]
    │    ├── Module lacks input/output dimensions → [EXPAND]
    │    └── Training recipe lacks concrete hyperparameters → [EXPAND]
    │  gpt-5.4 · codex-reply (Same thread)
    │  Each [EXPAND] section requires:
    │    ① Complete loss equation (all terms defined)
    │    ② 5-15 lines of pseudocode
    │    ③ Module interfaces (input/output dimensions and types)
    │    ④ Hyperparameter ranges + rationale
    │  Rerun Theory-Experiment Alignment checks (catch new theoretical claims)
    │  Output: refine-logs/round-N-expanded.md
    ▼
Phase 5: Final Report (Final output)
    ├── refine-logs/skeleton.md
    ├── refine-logs/round-N-expanded.md  ← new in v2 (Deep Expansion output)
    ├── refine-logs/REVIEW_SUMMARY.md
    ├── refine-logs/FINAL_PROPOSAL.md    (From the expanded version)
    ├── refine-logs/REFINEMENT_REPORT.md
    └── refine-logs/score-history.md
```

### Skeleton Extraction Concept

The skeleton defines the proposal's logical spine: the shortest path from the reviewer's current understanding (State A) to the target understanding (State B).

```
State A                          State B
What the reviewer currently believes              What the reviewer must believe after reading
(Conventional wisdom/unknowns)              (Changed understanding/new beliefs/new tools)
        │                              ▲
        │    Skeleton Path             │
        └──→ Step 1 → Step 2 → ... → Step N
             Every step is indispensable: skipping one prevents the reader from reaching State B
```

Run a Skeleton Gap Check in every revision round: each proposal section must map to a skeleton step. An unmapped section is either unnecessary or evidence of an incomplete skeleton.

### Top-2 Diagnosis Discipline

Fix only the 2 biggest problems per round instead of addressing every review comment at once. This prevents the proposal from oscillating between conflicting suggestions and keeps revisions focused.

### Four Core Checks (Every Round)

1. **Anchor Check** -- Do the revisions still address the original problem?
2. **Simplicity Check** -- Is the main contribution still focused? Can components be removed or merged?
3. **Skeleton Gap Check** -- Does each skeleton step have a corresponding section?
4. **Drift Warning** -- Do review suggestions cause drift from the original problem?

---

## 6. Multimodel Collaboration

```
    Local agent (execution layer)                         External LLM / gpt-5.4 (Review/generation layer)
    ─────────────────                       ──────────────────────────────────────
    Literature search / PDF / Zotero / Obsidian       Landscape critique Phase 2a (xhigh) ← v2
    Gap identification & thematic synthesis                      Critique-anchored idea generation Phase 2b (xhigh) ← v2
    Initial screening: feasibility / quick novelty check / impact        Novelty cross-validation (Phase C)
    Professor He's four-dimension scoring                          Reviewer simulation: 3 reviewers + meta-review (xhigh)
    Anti-pattern check                               Standard iterative review: 7-dimension scoring (xhigh)
    Skeleton extraction / Problem Anchor               Re-review: same thread codex-reply (xhigh)
    Theoretical grounding analysis (Phase 1.4.T) ← v2          Socratic dialogue (active-questioning mode) ← v2
    Theory-Experiment Matrix ← v2           Deep Expansion (Fill in equations/pseudocode) ← v2
    Proposal drafting & revision
    Strategic-fit assessment (Module C)
    Maintain simplicity / push back on overcomplication

    ◄──────── Codex MCP (mcp__codex__codex / codex-reply) ────────►
                Or (--gpt-only) tools/gpt_call.sh → OpenAI API ← v2

    Design principles:
    • The local agent handles structured reasoning, search, filtering, drafting, and theory-alignment checks
    • The external LLM handles critique, divergent ideation, adversarial review, and Socratic questioning
    • All external LLM calls use xhigh reasoning effort
    • Phase 2a's threadId is reused throughout Phase 2b, review rounds, and Phase 5.5
    • GPT-only path: CODEX_MODE=gpt-api (./run.sh --gpt-only) ← v2
```

---

## 7. Data Flow

```
Stage 1: /lit-survey
    │
    ├──→ outputs/LANDSCAPE.md        (Narrative + tables + gap matrix)
    └──→ outputs/LANDSCAPE.json      (Structured data for downstream use)
              │
              │ Read gaps[] + papers[]
              ▼
Stage 2: /idea-gen
    │
    ├──→ outputs/CRITICAL_ANALYSIS.md (Landscape critique list CRITIQUE-XX) ← v2
    ├──→ outputs/IDEAS_RAW.md         (All 8-12 ideas, including Anchored Critique + Theorem Scaffold)
    └──→ outputs/IDEAS_FILTERED.md    (4-6 surviving ideas + elimination table)
              │
              │ Read surviving ideas + feasibility
              ▼
Stage 3: /idea-screen
    │
    ├──→ outputs/SCREENING_REPORT.md (Full three-module report)
    └──→ outputs/SCREENING_RANKED.md (Ranked table + concise report)
              │
              │ Top 1-2 ideas + Review feedback
              ▼
Stage 4: /idea-refine
    │
    ├──→ refine-logs/skeleton.md
    ├──→ refine-logs/round-0-initial-proposal.md  (Includes Theoretical Grounding + T-E Matrix) ← v2
    ├──→ refine-logs/round-N-review.md
    ├──→ refine-logs/round-N-refinement.md
    ├──→ refine-logs/round-N-expanded.md          (Deep Expansion Pass output) ← v2
    ├──→ refine-logs/socratic-turn-T-*.md         (In Socratic dialogue mode) ← v2
    ├──→ refine-logs/REVIEW_SUMMARY.md
    ├──→ refine-logs/FINAL_PROPOSAL.md            (From the expanded version)
    ├──→ refine-logs/REFINEMENT_REPORT.md
    └──→ refine-logs/score-history.md
              │
              ▼
Final: outputs/IDEA_DISCOVERY_REPORT.md (End-to-end summary)
```

---

## 8. Checkpoint Mechanism

The pipeline (`/idea-pipeline`) places checkpoints between stages so users can intervene or adjust the process.

```
  Stage 1 ──→ Checkpoint 1 ──→ Stage 2 ──→ Checkpoint 2 ──→ Stage 3 ──→ Checkpoint 3 ──→ Stage 4 ──→ Checkpoint 4
               "Literature survey complete"                "Idea generation complete"              "Screening complete"                  "Refinement complete"
```

| Checkpoint | Presented Content | User Options | AUTO_PROCEED Behavior |
|------------|---------|---------|-------------------|
| **1 (After survey)** | Paper count, gap count, top 3 themes | Confirm / adjust scope / search again | Continue automatically with current results |
| **2 (After generation)** | Surviving ideas + He Score + Risk | Select ideas / change direction / regenerate | Screen all filtered ideas |
| **3 (After screening)** | Ranked table + Composite Score + reviewer consensus | Confirm refinement / select specific ideas / change venue | Refine the top REFINE_TOP_N ideas |
| **4 (After refinement)** | Final score + Verdict + method paper | Accept / continue iterating / adjust manually | Produce final report |

### AUTO_PROCEED Mechanism

- **Default**: `true`
- When `AUTO_PROCEED = true`, if the user does not respond at a checkpoint, the pipeline automatically selects the best option and continues.
- Use `-- auto: false` to require user confirmation at every checkpoint.

---

## 9. Venue Profile System

### Location
```
venue-profiles/
├── _template.md     Template
├── ICML.md          ICML Configuration
├── NeurIPS.md       NeurIPS Configuration
└── VLDB.md          VLDB Configuration
```

### Profile Schema

```
┌─────────────────────────────────────────────────────────────────┐
│               Venue Profile                                     │
├─────────────────────────────────────────────────────────────────┤
│ Metadata                                                        │
│   name:            Venue abbreviation (ICML)                    │
│   full_name:       Full name                                    │
│   type:            ML | systems | NLP | ...                     │
│   acceptance_rate: ~25%                                         │
│   verdict_options: Strong Reject → Strong Accept                │
│   allows_revision: true | false                                 │
├─────────────────────────────────────────────────────────────────┤
│ Calibration Tiers (Calibration criteria)                        │
│                                                                 │
│   Tier 1: Top-tier work                                         │
│     characteristics + attitude (Rigorous affirmation)           │
│                                                                 │
│   Tier 2: Above average (Solid-Incremental)                     │
│     characteristics + attitude (Skeptical scrutiny)             │
│                                                                 │
│   Tier 3: Mediocre/flawed                                       │
│     characteristics + attitude (Strict minimum-standard checks) │
├─────────────────────────────────────────────────────────────────┤
│ Reviewer Profiles (Reviewer profiles)                           │
│                                                                 │
│   Reviewer 1: [Role name]                                       │
│     focus / accept_when / reject_when                           │
│                                                                 │
│   Reviewer 2: [Role name]                                       │
│     focus / accept_when / reject_when                           │
│                                                                 │
│   Reviewer 3: [Role name]                                       │
│     focus / accept_when / reject_when                           │
├─────────────────────────────────────────────────────────────────┤
│ Idea Evaluation Adaptation                                      │
│   Key question: "If this idea is executed correctly,            │
│            would the resulting paper fit this venue?"           │
└─────────────────────────────────────────────────────────────────┘
```

### Use in Module B

```
/idea-screen "ideas" -- venue: ICML
         │
         ▼
Read venue-profiles/ICML.md
         │
         ├── Extract Calibration Tiers → inject into review prompt
         ├── Extract Reviewer Profiles → define 3 reviewer roles
         └── Extract Verdict Options → restrict verdict options
         │
         ▼
Build English review prompt → gpt-5.4 (xhigh)
         │
         ▼
3 independent reviewers + Meta Review
```

> **Fallback**: If the profile file is missing, automatically use the built-in generic "Top ML Venue" configuration.
> **`-- venue: all`**: Use all available profiles for comparative review.
