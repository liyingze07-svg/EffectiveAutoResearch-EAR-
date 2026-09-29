# stage r4_experiment_run — run one experiment

> Fresh engine context. experiment_request + the paper's real code and real data → an auditable artifact. **A different engine will audit this artifact afterwards, so nothing may be fabricated.**

## Slots `{{SLUG}}` `{{EXPID}}`
## Inputs (read-only): the request for `{{EXPID}}` in `campaigns/{{SLUG}}/ledger/experiment_queue.json`, and `papers/{{SLUG}}/` (the paper's code and data — **read-only, never modify, never commit**).

## Rules
0. **Check the execution domain first.** If `campaigns/{{SLUG}}/REMOTE_ONLY.md` exists, read it in full and obey it. When that file exists, all data preparation, statistics, inference, training, evaluation and smoke runs must happen on the remote host it declares; the local machine may only run static lint, orchestration and small summaries or hashes. Do not run locally merely because a task happens to be CPU-only.
1. Use the paper's **real** data and existing code. **Never use `np.random`, synthetic or toy data as the data source** (bootstrap resampling of real data is fine).
2. Write `driver.py`, lint it statically, run it (locally for CPU work; for GPU go through the declared remote runner with its lock, and wrap every remote call in a timeout), then store `{raw, derived}`.
3. **Never invent a number.** The wall-time limit follows whatever the experiment request explicitly registers; when nothing is registered, default to 40 minutes. If the run fails, the data is missing, or it times out → `status: failed|partial` plus the reason (a legitimate outcome; downstream moves down the warrant ladder and concedes). Do not truncate a multi-epoch remote training run that is converging normally and that the request explicitly allowed more time for, merely to fit the 40-minute default.
4. The working directory is only `campaigns/{{SLUG}}/experiments/{{EXPID}}/`.

## Output (everything in the directory above): `results.json` (`{raw, derived}`, with a recipe attached to `derived`), `run.log`, `driver.py`, and `manifest.json` (host, started_utc, duration_sec, seed_count, sample_count, data_source_path, **data_fingerprint**, model_id, cmd). Receipt: `{expid, status, key_numbers, data_source_path}`.
