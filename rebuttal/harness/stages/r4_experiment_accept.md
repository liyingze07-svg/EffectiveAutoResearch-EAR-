# stage r4_experiment_accept — Experiment Code Audit Gate (Once After Completing the Experiment; Two Stages)

> **Executed by a new engine that has not run this experiment** (DRIVE/ACQUIT separation: one engine runs it, and another audits it).
>
> **⚠️ Philosophy (v0.8)**: Acceptance = **audit the code once after completing the experiment**—**not** rerun it every time to prove that it "actually ran".
> The data is assumed real by default (we control the data source ourselves). The audit checks: **① whether the code is correct / whether there are obvious bugs ② whether the run completed (whether results were posted before it finished)
> ③ whether fake data was used ④ whether a fake model / hard-coded numbers were used.** An independent rerun is downgraded to an **optional spot check** (performed only when the code audit raises doubts), **not the default gate**.

## Two Stages (v0.7 Retained, Redundancy Removed)
- **Establish the origin (audit once)**: perform the code audit below; after ACCEPT, record `driver_sha256` + `data_fingerprint` in `origin_audit`.
- **Cheap recheck (every time)**: `orchestrate.accept_experiment` checks—if the driver hash + data fingerprint are both unchanged and the origin verdict∈{ACCEPT,PARTIAL} → **reuse directly without re-auditing**; re-audit only if **the driver changed / the data changed / there is no origin / the previous verdict was REJECT**. **"Rerun the experiment every time" is prohibited.**

## Slots
`{{SLUG}}` `{{EXPID}}` `{{DATA_SOURCE}}` (real data path) `{{DRIVER_SHA}}` (driver.py sha256 calculated by the orchestrator and written back to origin_audit)

## Input (Read-Only)
`campaigns/{{SLUG}}/experiments/{{EXPID}}/`: `driver.py` (primary audit target) `results.json` `run.log` `manifest.json`; `{{DATA_SOURCE}}` (real data).

If `campaigns/{{SLUG}}/REMOTE_ONLY.md` exists, it must first be read in full and obeyed. The acceptance side may perform static code audits and hash checks locally, but any data reading, statistical recomputation, model loading, or optional spot rerun must be executed on the remote environment declared in that file; experiment computation must never be run locally.

## Audit Items (Primarily a Static Code Audit, Once After Completing the Experiment)
| # | What to Check | Passing Condition |
|---|---|---|
| **C1 Code Correctness** | Are there any obvious bugs? | Statically inspect `driver.py`: **it computes the quantity it claims to compute** (consistent with `experiment_request`/goal); no incorrect indexing / incorrect aggregation / off-by-one / unit or sign errors / incorrect baseline; the statistical protocol is reasonable (e.g., CI uses the correct seed) |
| **C2 Complete Run** | Were results posted before the run completed? | `run.log` has a **complete termination** (not a mid-run crash/timeout/immediate exit); `results.json` contains **every declared cell/seed/sample** (if N seed are declared, there must be N; if two arms are declared, both must be present); no "partial results presented as complete" |
| **C3 Real Data** | Was fake data used? | The code reads **real data** from `manifest.data_source_path`; **grep does not find `np.random/randn/synthetic/fake/toy` used as the data source** (bootstrap resampling of real data is allowed); `sample_count` matches the real-data scale. **cheap confirmation**: it is sufficient for `manifest.data_fingerprint` to match the real data; no independent recomputation is required every time |
| **C4 No Fake Model/Hard-Coding** | mock / fabricated numbers? | No `MockModel`/`return <canned>`/monkeypatch returning a constant / hard-coded `derived`; **point estimates can be recomputed from raw with <1% error** (`recompute_check.py`); **procedure-derived values** (bootstrap CI/permutation test) are labeled `procedure_derived` and do not need to be reconstructed by a simplistic script. **"No model" is valid**: pure analysis may reuse frozen real artifacts (manifest declares no-model + fingerprint fallback); model loading is not required |
| **(Optional) Spot Rerun** | Perform only when in doubt | **Only when C1–C4 raise doubts** (e.g., suspected hard-coding/partial results): rerun 1 seed / a small number of samples with the same driver and the same data for comparison. **This is not a default step**—if the code audit passes, no run is needed. |

## Rules
- Audit C1–C4 entirely statically; **do not rerun the experiment by default**. A spot rerun is triggered only when the code audit raises doubts.
- Any failure → verdict `REJECT` + a specific reason (which line of code/which gap) → return it for **code changes/missing artifacts**, without changing the numbers.
- Partial completion (a sub-axis is not_run) → `partial` + which part was not done.

## Output (Write This File)
`campaigns/{{SLUG}}/experiments/{{EXPID}}/ACCEPTANCE.json`:
```json
{ "expid":"{{EXPID}}", "verdict":"ACCEPT|REJECT|PARTIAL",
  "C1_code_correct":true, "C2_complete":true, "C3_real_data":true,
  "C4_no_fake_no_hardcode":{"recompute_max_relerr":0.0,"procedure_derived":["bootstrap_2000x_cluster_ci"]},
  "spot_rerun":{"done":false,"reason":"code audit clean; not needed"},
  "origin_audit":{"driver_sha256":"{{DRIVER_SHA}}","data_fingerprint":{"...":"..."}},
  "reasons":[] }
```
receipt: `{expid, verdict, code_audit_clean}`. `origin_audit` allows the orchestrator to determine "whether it can be cheaply reused next time without re-auditing."
