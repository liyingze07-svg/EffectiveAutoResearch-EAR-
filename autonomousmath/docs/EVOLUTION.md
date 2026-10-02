# Evolving the mathematical engine

AutonomousMath's original goal prompt drives the research loop: seek and verify an
open problem, alternate prover and skeptic, harden claims, write a manuscript, and
revise against independent review. The AllAuto SandBox implementation added a
second loop around complete research episodes: compare a population of strategies,
retain an elite, use a coach to diagnose failed episodes, then mutate, cross over,
or explore for the next generation.

This portable implementation preserves those principles. The earlier SandBox
genome consisted of phase prompts and parameters. Here the candidate's `engine/`,
`prompts/`, `skills/`, and `config.json` are all editable. This includes the loop
composition, tool usage and worker code. A documented worker/artifact interface
connects the evolved code to the fixed parent supervisor.

The final reviewer stays in the original package's `referee/`; it is never copied
into a candidate or coached workspace. Reviewer-panel skills are also excluded.
The parent engine obtains the candidate's proof and manuscript, performs its own
review, and produces the authoritative result. A candidate's self-declared
acceptance is not an optimizer result. The immutable review rubric and permanent
baseline are hashed and checked during evolution.

## Try the complete offline loop

From the repository root:

```sh
python3 -m autonomousmath.optimizer evolve \
  --workspace /tmp/autonomousmath-evolution \
  --offline --generations 2 \
  --direction 'Prove a precise finite-sample learning guarantee.'
python3 -m autonomousmath.optimizer serve \
  --workspace /tmp/autonomousmath-evolution --port 8765
```

The two generations invoke the actual parent engine CLI, copy candidate harnesses,
perform labelled demonstration edits, compare the fixed task set and save results.
They do not call a model, discover a new theorem, or establish a quality improvement.
Offline simulated scores/acceptance are explicitly labelled; real acceptance is
zero. Opening the dashboard does not start any evolution.

For a real model run, explicitly omit `--offline` in a new workspace:

```sh
python3 -m autonomousmath.optimizer evolve \
  --workspace ./workspaces/live-evolution --backend codex \
  --generations 2 --parallelism 1 \
  --direction 'Your fixed research direction and evaluation task.'
```

That command spends calls on research, final review and the mutation coach. Both
Codex and Claude CLI backends are supported. Codex coaches use workspace-write;
Claude coaches use the same explicit tools and edit policy as the research worker.
Neither requests a sandbox or approval bypass. The existing local
CLI authentication is used; no credentials are copied into candidate directories.

To continue until stopped, add `--continuous`. This is a sustained evolution loop,
not an automatically installed background service. Run it under a terminal session
manager or your own supervisor if it should survive a terminal disconnect.

## Evaluation and selection

Each generation uses the same immutable direction list from `tasks.json`, the
same number of episodes per task, and a permanent baseline. The parent engine runs
each candidate with `--candidate-root` and produces reviewed result records. The
headline selection metric averages normalized quality, manuscript completion
rate and final-review acceptance rate. Offline fixtures use their separately
labelled simulated acceptance rate. Failures, retries and model/coach calls stay
visible; infrastructure failures remain distinguished from rejected mathematics.
There is no currency-cost model. Quality, completion and acceptance remain the
primary criterion; ties prefer fewer calls per effective result, then fewer
review revisions per effective result. A more efficient equal-quality strategy
can replace the elite. Calls include failed attempts and review work recorded by
the parent engine.

Elite retention protects the best observed strategy. Targeted mutation uses its
failure profile; semantic crossover combines two parents; an exploration child
allows a larger strategy change. The offspring stay separate from the baseline.
The coach can change how quality is achieved, and cannot obtain a legitimate pass
by reducing review, forging a result or rewriting the fixed acceptance rule.

Per-task results live in `runs/genN/<candidate>/taskI-epJ/`. The generation summary
is `runs/genN/results.json`; `evolution_state.json` records history, lineage,
completed episodes, coach calls, retries and active child processes. Completed
episodes are reused after interruption. Task multiplicity and backend mode are
saved for a partial generation; a resumed generation completes the same comparison.
Changing the fixed task set or final reviewer requires a fresh workspace.
Offline/live mode and the configured backend are also fixed for a workspace, so
fixture scores cannot be carried into a live comparison.

## Local control

The dashboard binds to localhost. Its control writes require a per-server token
and reject a different browser Origin/Host. It displays the current generation,
active episodes, quality/written/pass curves, baseline gap and candidate lineage.
It refreshes every two seconds.

- **Start / resume:** acquires the workspace's single-writer lock. Repeated starts
  do not create competing evolution processes.
- **Pause:** stops scheduling new episodes and lets in-flight work finish. Results
  are checkpointed before the writer returns.
- **Emergency stop:** captures the registered processes and their descendants,
  including reviewers in separate sessions, before stopping the parent. Each
  signal checks the process-start stamp, and surviving owned descendants are
  killed after a grace period. No global process-name killing is used.
- **Controls:** parallelism (1–4), generations per start, continuous mode and
  interval are scheduling settings. The browser does not switch an offline demo
  into a live model run.

Candidate code is executable research tooling. The local control token protects
HTTP writes; it is not an operating-system isolation boundary for evolved code.
Use your usual container or account isolation when running untrusted candidates.

## Provenance

The selection/coach design, episode failure profile, permanent baseline,
elite retention, semantic crossover, exploration and state recovery were adapted
from the existing AllAuto SandBox mathematical pipeline. Its machine-specific
shell scripts, service endpoints, absolute paths and production publishing hooks
are replaced here with a portable standard-library implementation.
