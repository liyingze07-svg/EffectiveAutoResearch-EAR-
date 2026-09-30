---
name: experiment-audit
description: "Audit experiment code for academic integrity: data leakage, baseline fairness, evaluation gaming, LLM-generated code tricks, and method-code alignment. Use when user says \"audit code\", \"check experiment\", \"review code integrity\", \"verify experiments\", \"code integrity\", \"experiment review\", or wants to verify that experiment code maintains academic standards before reporting results."
argument-hint: "[code-directory-or-file] [-- proposal: path/to/FINAL_PROPOSAL.md] [-- venue: ICML|NeurIPS|VLDB]"
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, WebSearch, WebFetch, Agent, mcp__codex__codex, mcp__codex__codex-reply
---

# Experiment Audit — Academic Integrity of Experiment Code

Audit experiment code for academic integrity: **$ARGUMENTS**

## Overview

When LLMs write experiment code for research ideas, they can introduce **six categories of unintentional academic misconduct**. These are not deliberate fraud, but biases that emerge as a model tries to make code run or produce good results. This skill acts as an **internal Reproducibility Chair**, comprehensively auditing code before results are reported.

Core philosophy:
1. **Code is the sole source of truth for the method.** What matters is what the code does, not what the paper says.
2. **Fair comparison is nonnegotiable.** Treat the proposed method and baselines equally.
3. **Reproducibility is fundamental.** Changing machines or seeds should not fundamentally change results.
4. **Generalization is the real contribution.** A method that works only on a particular instance has no academic value.

```
Experiment code complete
  → Phase 1 (local agent): Code scan and structural understanding
  → Phase 2 (local agent): Six-module audit
  → Phase 3 (Codex/GPT-5.4): Independent cross-audit
  → Phase 4 (local agent): Overall assessment and fix checklist
  → Phase 5: Audit report
```

## Constants

- **REVIEWER_MODEL** = `gpt-5.4` — External model for independent code auditing. (**Model availability depends on your account**: Codex signed in with a ChatGPT account can use only models available to that account; unsupported models return a 400 error. With `--codex-cli`, **do not pass `--model`**; let Codex use its default model. With `--gpt-only`, the model must be available to your OpenAI API key.)
- **SEVERITY_LEVELS** = `{CRITICAL, WARNING, INFO}` — Issue severity.
  - `CRITICAL`: Must fix; otherwise results are unreliable (e.g., data leakage, evaluation cheating)
  - `WARNING`: Should fix; otherwise reviewers may object (e.g., missing multiple seeds, unfair baselines)
  - `INFO`: Suggested improvement for paper quality (e.g., readability, documentation completeness)
- **VERDICT_OPTIONS** = `{PASS, CONDITIONAL_PASS, FAIL}`
  - `PASS`: Code passes the audit; results may be reported
  - `CONDITIONAL_PASS`: WARNING issues but no CRITICAL issues; report after fixes
  - `FAIL`: CRITICAL issues present; fix and rerun the audit
- **MAX_FILES_DEEP_SCAN** = `30` — Maximum files for deep inspection (if exceeded, prioritize the top-30).

## Input

1. **`$ARGUMENTS`** — Must contain one of:
   - Code directory path (e.g., `./experiments/`, `src/`)
   - A single code file path (e.g., `train.py`)
   - If no path is specified, scan all `.py`, `.sh`, `.yaml`, and `.json` files in the current working directory

2. **`-- proposal:` directive** (optional but strongly recommended) — Path to FINAL_PROPOSAL.md or another proposal. Used by Module E (Method-Code Alignment). If omitted, try `refine-logs/FINAL_PROPOSAL.md`.

3. **`-- venue:` directive** (optional) — Target venue for calibrating the reviewer perspective. Default: `ICML`.

### Parsing Logic

1. Parse `$ARGUMENTS` to identify the code path.
2. Parse `-- proposal:` for the proposal path. If omitted, search in order:
   - `refine-logs/FINAL_PROPOSAL.md`
   - `outputs/SCREENING_RANKED.md` (use the top-ranked idea description)
   - If neither exists, run Module E without a proposal reference (internal code consistency only).
3. Parse `-- venue:` for the target venue.

---

## Phase 1: Code Scan and Structural Understanding

Build a global understanding of the experiment code before auditing.

### Step 1.1: Discover Code Files

```
Scan the target directory for:
- Training scripts (train.py, run_*.py, main.py, etc.)
- Evaluation scripts (eval.py, test.py, evaluate.py, etc.)
- Data-processing scripts (data*.py, dataset*.py, preprocess*.py, etc.)
- Configuration files (*.yaml, *.json, *.toml, config*.py, etc.)
- Baseline implementations (baseline*.py or the baselines/ directory)
- Utility scripts (utils*.py, helpers*.py, etc.)
- Shell scripts (*.sh; often contain run parameters)
```

Use `Glob` and `Grep` to locate key files quickly. If the total exceeds MAX_FILES_DEEP_SCAN (30), prioritize:
1. Main training loops (files containing loss computation)
2. Evaluation scripts (files containing metric computation)
3. Data loading/processing files
4. Configuration files
5. Other files

### Step 1.2: Build a Code Map

Read key files and produce a concise structural map:

```markdown
## Code Structure
- Training entry point: train.py (L1-L300)
  - Data loading: data_loader.py → Dataset class
  - Model definition: model.py → ProposedModel class
  - Loss: losses.py → combined_loss()
  - Evaluation: eval.py → evaluate()
- Baseline:
  - baselines/method_a.py → MethodA class
  - baselines/method_b.py → MethodB class
- Configuration: config.yaml
- Run script: run_all.sh
```

### Step 1.3: Identify Data Flow

Trace data from raw input to final metrics:

```
Raw data → Preprocessing → Data split → Training/validation/test sets
                                    ↓           ↓
                               Model training → Evaluation → Reported metrics
```

Pay particular attention to:
- Where are preprocessing parameters (mean, std, vocabulary, tokenizer) computed, and on which data?
- When is the data split? Is the full dataset used before splitting?
- Does any test-set information flow back into training?

---

## Phase 2: Six-Module Audit

For every issue found in each module, record:
- **Issue ID**: `A-01`, `B-02`, etc. (module prefix + sequence number)
- **Severity**: CRITICAL / WARNING / INFO
- **Location**: `file_path:line_number`
- **Description**: Identify the specific code and problem
- **Impact**: Explain how it affects the credibility of experimental results
- **Suggested fix**: Concrete code changes

### Module A: Data Pipeline Integrity

Check for information leakage or inappropriate data-processing operations.

#### A.1 Data Leakage Detection

Search for these patterns:

```python
# Anti-pattern 1: Preprocessing statistics use all data, including test data
# Search terms: fit(), fit_transform(), .mean(), .std(), .vocab
# Check whether inputs to these operations contain test-set data

# Anti-pattern 2: Feature engineering leaks label information
# Search terms: target_encode, label_encode (target information in non-target columns)
# Check whether feature construction uses y/label/target

# Anti-pattern 3: Future-information leakage in time-series data
# Search terms: shift(), rolling(); inspect window direction
# Check whether future time steps are used

# Anti-pattern 4: Cross-split contamination after splitting
# Search: locations of train_test_split calls
# Check whether splitting occurs before or after preprocessing

# Anti-pattern 5: Data-augmentation leakage
# Check whether augmented samples cross train/test boundaries (e.g., crops of one image appear in both)
```

Concrete search strategy:
1. Use `Grep` to search for `fit_transform|\.fit\(|\.mean\(|\.std\(|normalize|standardize|vocab`
2. Trace each match's input data to determine whether it includes the test set
3. Use `Grep` to search for `train_test_split|split|\.train\b|\.test\b|\.val\b` to locate splits
4. Check the relative ordering of splitting and preprocessing

#### A.2 Data Filtering Review

```python
# Anti-pattern: Silently filtering "hard" samples
# Search: filter, drop, remove, skip, ignore, mask (in dataset contexts)
# Check whether filtering criteria are justified and applied equally to all methods
# Watch for filtering based on model outputs (e.g., "only samples with confidence > 0.5 count")
```

#### A.3 Data Split Validity

```python
# Checks:
# 1. Is a fixed seed used for splitting?
# 2. Are split ratios reasonable and standard?
# 3. Is structured data (time series, users, groups) split according to its structure?
# 4. Are validation and test sets strictly separate?
# 5. Is the validation set being used as a test set?
```

### Module B: Baseline Fairness

This is an easy target for reviewer criticism. LLMs often carefully tune their own method while implementing baselines hastily.

#### B.1 Resource Fairness

For every baseline and the proposed method, check:

| Item | Specific Checks |
|--------|------------|
| **Learning rate** | Are learning-rate schedules equivalent? Does the proposed method receive more carefully tuned warmup/decay? |
| **Training duration** | Do all methods train for the same epochs/steps? Is one stopped early while others train longer? |
| **Model capacity** | Are parameter counts comparable? Does the proposed method use a larger backbone? |
| **Data augmentation** | Do all methods use the same augmentation strategy? Are some augmentations exclusive to the proposed method? |
| **Pretrained weights** | Do all methods use weights from the same source and version? |
| **Hyperparameter search budget** | Does the proposed method receive more tuning runs? |
| **Inference compute** | Is test-time compute equivalent? Are ensembles and test-time augmentation applied fairly? |

Search strategy:
1. Use `Grep` to search hyperparameter terms such as `lr|learning_rate|num_epochs|batch_size|warmup|weight_decay`
2. Compare configurations for the proposed method and every baseline
3. Check especially for `max_epochs` restrictions applied only to baselines
4. Check whether baseline code comes from official implementations (inspect imports and source comments)

#### B.2 Implementation Completeness

```python
# Anti-pattern 1: Simplified baseline implementations
# Check for baseline comments such as "simplified", "basic", or "simple"
# Check whether key components from the original paper are missing

# Anti-pattern 2: Outdated baseline hyperparameters
# Check whether baseline hyperparameters match the original paper

# Anti-pattern 3: Missing necessary baseline tricks
# Check whether tricks from the baseline paper, such as label smoothing or mixup,
# are included in this implementation

# Anti-pattern 4: Unfavorable baseline defaults
# Check whether baseline defaults reflect its best configuration
```

#### B.3 Baseline Source Verification

```
For each baseline:
1. Check for source comments (official repository, third-party implementation, self-implementation)
2. For self-implementations, flag WARNING: "Baseline [X] is self-implemented rather than official code.
   Verify that its performance matches the original paper."
3. For official code, check whether it is the latest stable version
```

### Module C: Evaluation Protocol Compliance

#### C.1 Randomness Control

```python
# Checks:
# 1. Is a global random seed set?
#    Search: seed, random_state, torch.manual_seed, np.random.seed, random.seed
# 2. Are multiple seeds run? (At least 3; 5 recommended)
#    Search: seeds = [...], for seed in, --seed
# 3. Is mean ± std reported?
#    Search: mean, std, ±, standard deviation
# 4. Is CUDA randomness controlled?
#    Search: torch.backends.cudnn.deterministic, torch.backends.cudnn.benchmark
# 5. Are there signs of seed shopping?
#    Check whether only the best seed is reported or seed-list values were selectively chosen
```

#### C.2 Metric Compliance

```python
# Checks:
# 1. Is the metric standard for this task?
#    Compare with benchmark conventions in the field
# 2. Are all standard metrics reported, or only favorable ones?
#    Flag WARNING when only 1 metric is reported
# 3. Are any metrics custom-defined?
#    If so, check whether definitions are reasonable or favor the proposed method
# 4. Is higher or lower better? Are metric directions consistent?
# 5. Are statistical significance tests performed?
#    Search: t-test, wilcoxon, bootstrap, p-value, significance
```

#### C.3 Checkpoint Selection

```python
# Anti-pattern: Choosing the best checkpoint using the test set
# Search: best_model, save_best, early_stopping
# Check whether the "best" checkpoint is selected on validation or test data
# Correct practice: Select on validation data, then report a one-time test-set evaluation
#
# Anti-pattern: Repeated test-set evaluation with only the best result reported
# Search: Test-evaluation frequency and result-recording logic
```

#### C.4 Reporting Completeness

```python
# Checks:
# 1. Are results from all experiments reported, without cherry-picking?
# 2. Are failed experiments and negative results recorded?
# 3. Are computational resources reported (GPU hours, memory usage)?
# 4. Are inference latency/throughput reported for efficiency-related contributions?
```

### Module D: Code Specificity Detection

This is a common failure point in LLM-generated code: implementations that "just work" for a particular instance.

#### D.1 Hard-Coded Value Detection

```python
# Search: Numeric constants throughout the code, excluding common values such as 0, 1, and 2
# For each hard-coded number, ask:
# 1. Is it a hyperparameter that belongs in configuration?
# 2. Is it dataset-specific (e.g., num_classes=10 applies only to CIFAR-10)?
# 3. How was it obtained? Is its source documented?
# 4. Would it remain valid on another dataset?
#
# Pay particular attention to:
# - Hidden thresholds (e.g., if confidence > 0.73)
# - Fixed dimensions (e.g., hard-coded hidden_dim=768 instead of reading configuration)
# - Loss weights (e.g., 0.7 and 0.3 in loss = 0.7 * loss_a + 0.3 * loss_b)
```

#### D.2 Conditional-Branch Specificity

```python
# Anti-pattern: Branches tailored to particular datasets or samples
# Search: if.*dataset.*==, if.*name.*==, if.*"CIFAR", if.*"ImageNet"
# Check whether these branches are legitimate adaptations (e.g., dataset-specific num_classes)
# or unjustified special treatment (e.g., different losses for specific datasets)
#
# Anti-pattern: Hard-coded input shapes
# Search: Concrete numbers in reshape and view
# Check whether shape transformations are tied to a particular data format
```

#### D.3 Configuration Externalization

```python
# Check that all configurable values are actually read from configuration:
# 1. Architecture parameters (layers, dimensions, heads, etc.)
# 2. Training hyperparameters (learning rate, batch size, epochs, etc.)
# 3. Data paths
# 4. Evaluation parameters
# 5. Hardware-specific settings
#
# Flag hard-coded values that should be configurable
```

#### D.4 Structural Generalizability

```python
# Key question: Can this code run on another dataset unchanged, or with configuration changes only?
#
# Checks:
# 1. Is data loading parameterized (paths, formats, column names, etc.)?
# 2. Are model input/output dimensions parameterized?
# 3. Is preprocessing general-purpose?
# 4. Is there a dataset-agnostic abstraction layer?
# 5. Can the code run directly on a dataset from the same domain but a different distribution?
```

### Module E: Method-Code Alignment

If a proposal is available, compare its method description with the implementation item by item.

#### E.1 Algorithm-Step Alignment

```
For every algorithmic step in the proposal:
1. Find the corresponding implementation
2. Check that it faithfully implements the described logic
3. Flag missing steps: described in the proposal but absent from code
4. Flag extra steps: present in code but undescribed in the proposal ("bonus steps")
```

**"Bonus steps" are the most dangerous signal.** Undocumented implementation steps may be:
- Essential tricks that make the method work (must be described in the paper)
- Dataset-specific hacks (should be removed)
- Unrequested LLM-added "optimizations" (require scrutiny)

#### E.2 Loss-Function Alignment

```python
# Checks:
# 1. Does the implemented loss match the proposal's equation?
# 2. Do loss-component weights match the proposal?
# 3. Are there undocumented regularization terms?
# 4. Is the loss conditional, with some terms disabled in certain cases?
```

#### E.3 Architecture Alignment

```python
# Checks:
# 1. Does the architecture (layers, dimensions, activations, etc.) match the proposal?
# 2. Are there undocumented skip connections, dropout, or normalization?
# 3. Does the inference path match the proposal?
# 4. Are training/inference differences fully documented?
```

#### E.4 No-Proposal Mode

If no proposal is found:
1. Skip algorithm-step alignment
2. Still check internal consistency:
   - Do comments match actual logic?
   - Do README/docstring descriptions match code?
   - Do configuration parameter names match their use in code?
3. Flag: "⚠️ No proposal reference. Module E checked internal code consistency only. Provide a proposal to enable full alignment verification."

### Module F: LLM Code Trap Detection

This distinctive module detects common LLM-generated patterns that look like learning but actually cheat.

#### F.1 Pattern Matching Disguised as Learning

```python
# Anti-pattern: Replacing genuine model learning with if-else rules, string matching, regexes, or lookup tables
# Search for:
#   - Long if-elif chains (>5 branches) in the inference path
#   - Dictionaries/hashmaps directly mapping inputs to outputs
#   - String templates constructing "predictions"
#   - Hard-coded answer lists
#
# Key question: Are predictions learned or obtained through rule matching?
# Would the model still work if all rule matching were removed?
```

#### F.2 Memorization Detection

```python
# Anti-pattern: The model or code memorizes training/test samples
# Checks:
# 1. Are data samples embedded in code?
#    Search: Long string constants, hard-coded vectors/matrices, sample data in JSON
# 2. Are there signs of overfitting during training?
#    Check whether training continues until 100% training accuracy
# 3. Do test samples appear in training code?
#    Search: References to test_data or eval_data in the training loop
```

#### F.3 Hidden Behavior in "Helper" Functions

```python
# Anti-pattern: Apparently harmless helper functions perform the core work
# Checks:
# 1. Do generic-looking functions in utils.py or helpers.py actually contain model logic?
# 2. Is "post-processing" actually a core method component?
#    How much does performance drop without it?
# 3. Is "data preprocessing" actually feature engineering?
#    Preprocessing must treat all methods fairly, not favor only the proposed method
```

#### F.4 Training-Time Information Leakage

```python
# Anti-pattern: Clever abstractions expose test-time information during training
# Checks:
# 1. Does the DataLoader return labels/answers in certain modes?
# 2. Are there inappropriate training/evaluation differences in forward()?
# 3. Does "teacher forcing" remain enabled at test time?
# 4. Do global variables or class attributes retain information they should not during training?
```

#### F.5 Code Clone Detection

```python
# Anti-pattern: Code copied from an existing solution with only variable names changed
# Checks:
# 1. Is the structure highly similar to a well-known open-source implementation?
# 2. Do comments or variable names retain traces of another project?
# 3. If proposed-method and baseline code are highly similar,
#    is there a substantive methodological difference?
```

---

## Phase 3: Independent Cross-Audit

Send key code to an external LLM for independent auditing to reduce the bias of reviewing one's own implementation.

### Step 3.1: Prepare Audit Material

Extract the following for external review:
1. **Core training loop** (training loop + loss computation)
2. **Evaluation code** (metric computation + result reporting)
3. **Data-processing code** (loading + preprocessing + splitting)
4. **Key differences between baselines and the proposed method**
5. **CRITICAL issues found by the local agent in Phase 2** (for cross-validation)

If the code exceeds 500 lines, send only the most important parts and a structural summary.

### Step 3.2: External LLM Audit

```
mcp__codex__codex:
  model: REVIEWER_MODEL
  config: {"model_reasoning_effort": "xhigh"}
  prompt: |
    You are the Reproducibility Chair of a top ML conference. Audit the experiment code below
    for issues affecting academic integrity.

    This code was generated by an LLM. Pay special attention to these LLM-specific traps:
    1. Hard-coded values tailored to specific datasets or samples
    2. Rule matching disguised as model learning
    3. Unfair baseline configurations (less training, worse hyperparameters)
    4. Data leakage (test-set preprocessing statistics, label leakage through features)
    5. Evaluation cheating (test-set checkpoint selection, seed shopping, favorable metrics only)
    6. "Bonus steps": Code absent from the paper's description that may be a hack

    ## Code Structure Overview
    [CODE_STRUCTURE_SUMMARY]

    ## Core Training Code
    ```python
    [TRAINING_CODE]
    ```

    ## Evaluation Code
    ```python
    [EVALUATION_CODE]
    ```

    ## Data-Processing Code
    ```python
    [DATA_CODE]
    ```

    ## Key Differences: Proposed Method vs Baselines
    [DIFF_SUMMARY]

    ## Prior Internal Audit Findings (Cross-Validate These)
    [LOCAL_AGENT_FINDINGS]

    Provide:

    ### 1. Independently Discovered Issues
    For each issue:
    - Severity: CRITICAL / WARNING / INFO
    - Category: Data leakage / Baseline unfairness / Evaluation cheating / Code specificity / LLM traps / Other
    - Location: File name + line or function
    - Description
    - Impact: How does it affect results? Could it inflate them, and by how much?
    - Fix

    ### 2. Cross-Validation of Prior Findings
    For each prior issue:
    - Do you agree?
    - If not, why?
    - Should severity change?

    ### 3. Generalizability Assessment
    - Can this code run directly on other datasets?
    - Which parts are dataset-specific?
    - What must change to generalize?

    ### 4. Overall Assessment
    - PASS / CONDITIONAL_PASS / FAIL
    - Top 3 risks
    - As a reviewer, what concerns would you raise about code quality?
```

**Codex MCP failure handling**: If `mcp__codex__codex` is unavailable:
1. Have the local agent perform the cross-audit using the same dimensions
2. Log: "⚠️ Codex MCP unavailable. Cross-audit performed by the local agent (self-review mode; reduced objectivity)."
3. Multiply the number of self-review CRITICAL findings by 1.2 to compensate for potential missed issues
4. Continue without interruption.

### Step 3.3: Integrate Findings

Merge Phase 2 (local-agent audit) and Phase 3 (external-LLM audit) findings:
1. Deduplicate: Merge identical issues from both sources
2. Cross-validate: If severity differs, use the higher level
3. Attribute independent findings: Label issues found by only one source
4. Preserve disagreements: Record both views when judgments differ

---

## Phase 4: Overall Assessment and Fix Checklist

### Step 4.1: Compute Module Scores

For each module (A-F), compute:

```
Module score = 10 - (CRITICAL count × 3) - (WARNING count × 1) - (INFO count × 0.2)
Clamp to a minimum of 0 and maximum of 10
```

### Step 4.2: Compute the Overall Score

```
AUDIT_SCORE = (
    0.25 × Module_A_score  +   # Data pipeline integrity
    0.20 × Module_B_score  +   # Baseline fairness
    0.20 × Module_C_score  +   # Evaluation protocol compliance
    0.15 × Module_D_score  +   # Code specificity
    0.10 × Module_E_score  +   # Method-code alignment
    0.10 × Module_F_score      # LLM code traps
)
```

### Step 4.3: Determine the Overall Verdict

| AUDIT_SCORE | CRITICAL Count | Verdict |
|-------------|------------|------|
| >= 7.0 and CRITICAL = 0 | 0 | **PASS** — Code passes; results may be reported |
| >= 5.0 or CRITICAL = 0 | 0 | **CONDITIONAL_PASS** — Report after fixing WARNING issues |
| < 5.0 or CRITICAL > 0 | > 0 | **FAIL** — Serious issues; fix and rerun the audit |

Any CRITICAL issue automatically produces FAIL, regardless of the total score.

### Step 4.4: Generate the Fix Checklist

Prioritize all issues:
1. **CRITICAL (must fix)**: Largest impact first
2. **WARNING (should fix)**: Lowest fix difficulty first
3. **INFO (optional improvements)**: Rank by improvement potential

For each issue, provide:
- Concrete code changes, not generic directions
- Estimated fix time
- Expected effect after fixing

---

## Phase 5: Audit Report Output

Create `outputs/` if needed:
```bash
mkdir -p outputs
```

### `outputs/AUDIT_REPORT.md`

A complete audit report with detailed findings for every module.

```markdown
# Experiment Code Audit Report

**Audit target**: [code path]
**Proposal reference**: [proposal path / none]
**Target venue**: [venue]
**Audit date**: [YYYY-MM-DD]
**Overall verdict**: PASS / CONDITIONAL_PASS / FAIL
**Overall score**: X.X/10

## Executive Summary

[Summarize the audit in 2-3 paragraphs: issue count, most serious problems, and overall code quality.]

## Score Overview

| Module | Score | CRITICAL | WARNING | INFO |
|------|------|----------|---------|------|
| A. Data Pipeline Integrity | X.X/10 | N | N | N |
| B. Baseline Fairness | X.X/10 | N | N | N |
| C. Evaluation Protocol Compliance | X.X/10 | N | N | N |
| D. Code Specificity | X.X/10 | N | N | N |
| E. Method-Code Alignment | X.X/10 | N | N | N |
| F. LLM Code Traps | X.X/10 | N | N | N |
| **Total** | **X.X/10** | **N** | **N** | **N** |

## Module A: Data Pipeline Integrity

### Findings

#### A-01 [CRITICAL] Preprocessing Statistics Use the Full Dataset
- **Location**: `data_loader.py:45`
- **Issue**: `StandardScaler.fit()` is called on combined train/test data
- **Impact**: Test information leaks into preprocessing parameters, inflating test metrics
- **Fix**: Replace `scaler.fit(all_data)` with `scaler.fit(train_data)`, then use `scaler.transform(test_data)`

#### A-02 [WARNING] ...
[...]

## Module B: Baseline Fairness
[Same structure]

## Module C: Evaluation Protocol Compliance
[Same structure]

## Module D: Code Specificity
[Same structure]

## Module E: Method-Code Alignment
[Same structure]

## Module F: LLM Code Traps
[Same structure]

## Cross-Audit Results

### Independent External LLM Findings
[List issues found by the external LLM but missed by the local agent]

### Cross-Validation Results
[List agreements and disagreements]

### Generalizability Assessment
[External LLM assessment of code generalizability]

## Overall Assessment
- **Verdict**: PASS / CONDITIONAL_PASS / FAIL
- **CRITICAL issue count**: N
- **Top risks**:
  1. [Risk 1]
  2. [Risk 2]
  3. [Risk 3]
- **Reviewer perspective**: [Specific code/experiment concerns a reviewer would raise]
```

### `outputs/AUDIT_CHECKLIST.md`

A concise, actionable fix checklist for developers.

```markdown
# Experiment Code Fix Checklist

**Audit date**: [YYYY-MM-DD]
**Overall verdict**: PASS / CONDITIONAL_PASS / FAIL
**Overall score**: X.X/10

## CRITICAL — Must Fix (Results Are Unreliable Otherwise)

- [ ] **A-01** `data_loader.py:45` — Preprocessing statistics use all data
  - Fix: `scaler.fit(all_data)` → `scaler.fit(train_data)`
  - Estimated time: 10 minutes

- [ ] **C-03** `eval.py:120` — Test-set checkpoint selection
  - Fix: Select checkpoints on validation data; use the test set only once for final reporting
  - Estimated time: 30 minutes

## WARNING — Should Fix (Reviewers May Object)

- [ ] **B-02** `config.yaml:15` — Proposed method trains for 200 epochs; baseline only 100
  - Fix: Equalize training duration or use early stopping
  - Estimated time: 5 minutes

- [ ] **C-01** `train.py:30` — Only 1 random seed
  - Fix: Run 3-5 seeds and report mean ± std
  - Estimated time: N/A (requires multiple runs)

## INFO — Suggested Improvements (Enhance Paper Quality)

- [ ] **D-05** `model.py:78` — Hard-coded hidden_dim=768
  - Fix: Move to configuration
  - Estimated time: 5 minutes

## Rerun the Audit After Fixing

After fixing CRITICAL and WARNING issues, rerun `/experiment-audit` to verify the changes.
```

### Large File Handling

If `Write` fails, use a Bash heredoc:
```bash
cat << 'AUDIT_EOF' > outputs/AUDIT_REPORT.md
[content]
AUDIT_EOF
```

---

## Execution Order

1. **Parse input**: Identify code path, proposal path, and venue.
2. **Phase 1**: Scan files and build code-structure and data-flow maps.
3. **Phase 2**: Audit modules in order (A → B → C → D → E → F). Modules A-D may run in parallel; Module E depends on the proposal.
4. **Phase 3**: Organize Phase 2 findings and send them to the external LLM for cross-auditing.
5. **Phase 4**: Integrate findings, compute scores, determine the verdict, and generate the fix checklist.
6. **Phase 5**: Write report files.

---

## Key Rules

1. **Write all output in English.** Use English for issue descriptions, impact analysis, and suggested fixes in AUDIT_REPORT.md and AUDIT_CHECKLIST.md, while preserving code snippets and file paths.
2. **Zero tolerance for CRITICAL issues.** Any code with a CRITICAL issue must receive FAIL, regardless of its score. Academic integrity has no gray area.
3. **Provide concrete code fixes.** Do not merely say "there is a problem"; say "replace `scaler.fit(all_data)` on line 45 with `scaler.fit(train_data)`". Actionability is essential.
4. **Distinguish legitimate adaptation from improper hacks.** Dataset-specific `num_classes` is legitimate. Dataset-specific losses are improper unless well justified.
5. **Dual-model cross-validation.** Local findings must be cross-checked by an external LLM. Independently corroborated findings are more credible.
6. **Avoid over-reporting.** Limit INFO issues to 10. Focus on issues affecting result credibility, not style preferences.
7. **Fully autonomous operation.** Do not ask questions, wait for confirmation, or offer choices. Make and record decisions autonomously.
8. **Large file handling**: If Write fails, use a Bash heredoc without asking the user.
9. **ALWAYS use `config: {"model_reasoning_effort": "xhigh"}`** for all Codex calls.
10. **For large codebases (> MAX_FILES_DEEP_SCAN), prioritize high-risk files.** Training loops > evaluation scripts > data processing > configuration > other files.

## Composing with Other Skills

```
/idea-refine → [code implementation] → /experiment-audit  ← you are here → [fixes] → [experiment execution]
```

- **Input from `/idea-refine`**: `refine-logs/FINAL_PROPOSAL.md` — Used for Module E's method-code alignment check.
- **This skill is independent**: It can also audit arbitrary experiment code on its own.
- **Output**: `outputs/AUDIT_REPORT.md` and `outputs/AUDIT_CHECKLIST.md` for developers to inspect and act on.

The audit skill is the final quality gate between idea and paper. Its purpose is not to obstruct research, but to ensure results withstand reviewer scrutiny. Passing the audit lets researchers report results confidently without worrying about challenges to experimental design.
