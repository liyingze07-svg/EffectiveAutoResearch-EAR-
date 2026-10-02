"""Evolution adapted from AllAuto SandBox's selection/coach/keep-elite design.

The fixed parent engine supervises evaluations and performs the final review.
Only candidate harnesses are copied into the coach's editable workspace.
"""

from __future__ import annotations

import concurrent.futures
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import threading
import time
from typing import Any


class EvolutionBusy(RuntimeError):
    """Another writer already owns this workspace."""


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    if root.exists():
        for path in sorted(root.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                digest.update(path.relative_to(root).as_posix().encode())
                digest.update(path.read_bytes())
    return digest.hexdigest()


def harness_hash(root: Path) -> str:
    """Ignore coach bookkeeping when deciding whether a real harness edit occurred."""
    digest = hashlib.sha256()
    for name in ("engine", "prompts", "skills"):
        digest.update(name.encode())
        digest.update(tree_hash(root / name).encode())
    if (root / "config.json").is_file():
        digest.update((root / "config.json").read_bytes())
    return digest.hexdigest()


def _process_stamp(pid: int) -> str | None:
    # The start tick prevents a stale record from killing a reused process ID.
    try:
        return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]
    except (OSError, IndexError):
        return None


def _owned_descendants(seeds: dict[int, str]) -> dict[int, str]:
    """Walk only the registered trees, including children spawned by worker threads."""
    found = dict(seeds)
    pending = list(seeds)
    seen = set()
    while pending:
        pid = pending.pop()
        if pid in seen or _process_stamp(pid) != found[pid]:
            continue
        seen.add(pid)
        try:
            children_files = list(Path(f"/proc/{pid}/task").glob("*/children"))
            for children_file in children_files:
                try:
                    children = children_file.read_text().split()
                except OSError:
                    continue
                for value in children:
                    child = int(value)
                    stamp = _process_stamp(child)
                    if stamp and child not in found:
                        found[child] = stamp
                        pending.append(child)
        except OSError:
            continue
    return found


def _signal_owned(processes: dict[int, str], sig: signal.Signals):
    for pid, stamp in reversed(list(processes.items())):
        try:
            if _process_stamp(pid) == stamp:
                os.kill(pid, sig)
        except ProcessLookupError:
            pass


def _begin_owned_stop(seeds: dict[int, str]) -> dict[int, str]:
    owned = _owned_descendants(seeds)
    _signal_owned(owned, signal.SIGTERM)
    # A registered process is its session leader. This also catches new inherited
    # group members while separately tracked reviewer sessions are signalled above.
    for pid, stamp in seeds.items():
        try:
            if _process_stamp(pid) == stamp and os.getpgid(pid) == pid:
                os.killpg(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    return owned


def _finish_owned_stop(owned: dict[int, str], grace_seconds: float = 2):
    deadline = time.monotonic() + grace_seconds
    captured = owned
    while time.monotonic() < deadline:
        captured = _owned_descendants(captured)
        time.sleep(.05)
    _signal_owned(_owned_descendants(captured), signal.SIGKILL)


def _terminate_owned(seeds: dict[int, str]):
    _finish_owned_stop(_begin_owned_stop(seeds))


DEFAULT_TASKS = [
    "Prove a precise finite-sample guarantee for a learning or estimation problem; identify novelty and assumptions.",
    "Prove a precise optimization or online-learning theorem; give a complete proof and check boundary cases.",
]

DEFAULT_CONTROL = {
    "enabled": False, "parallelism": 1, "population_size": 4,
    "episodes_per_task": 1, "generations": 2, "continuous": False,
    "interval_seconds": 0, "offline": True, "backend": "codex",
    "timeout_seconds": 3600,
}


def aggregate(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Quality, written rate and accepted rate; offline acceptance stays separate."""
    valid = [r for r in records if r.get("status") not in {"infra_fail", "cancelled", "blocked", "checkpoint"}]
    count = len(valid)
    scores = [max(0.0, min(10.0, float(r.get("quality_score", r.get("score", 0)) or 0))) for r in valid]
    quality = sum(scores) / count if count else 0.0
    written = sum(bool(r.get("artifact_written")) for r in valid) / count if count else 0.0
    accepted = sum(bool(r.get("accepted")) and not r.get("offline") for r in valid) / count if count else 0.0
    simulated = sum(bool(r.get("fixture_accepted", r.get("accepted"))) and bool(r.get("offline"))
                    for r in valid) / count if count else 0.0
    offline = bool(records) and all(r.get("offline") for r in records)
    selection_accept = simulated if offline else accepted
    effective = sum(bool(r.get("fixture_accepted", r.get("accepted"))) if r.get("offline")
                    else bool(r.get("accepted")) for r in valid)
    if not effective:
        effective = sum(bool(r.get("artifact_written")) for r in valid)
    calls = sum(int(r.get("calls", 0) or 0) for r in records)
    revisions = sum(int(r.get("review_revisions", 0) or 0) for r in records)
    return {
        "n": len(records), "n_valid": count, "mean_quality": round(quality, 4),
        "written_rate": round(written, 4), "accept_rate": round(accepted, 4),
        "simulated_accept_rate": round(simulated, 4), "offline": offline,
        "composite": round((quality / 10.0 + written + selection_accept) / 3.0, 4),
        "calls": calls, "review_revisions": revisions, "effective_results": effective,
        "calls_per_effective_result": calls / effective if effective else None,
        "revisions_per_effective_result": revisions / effective if effective else None,
        "retries": sum(int(r.get("retries", 0) or 0) for r in records),
    }


def selection_key(metrics: dict[str, Any]) -> tuple[float, float, float]:
    """Quality remains primary; equally good harnesses prefer less repeated work."""
    calls = metrics.get("calls_per_effective_result")
    revisions = metrics.get("revisions_per_effective_result")
    return (metrics["composite"], -(calls if calls is not None else 1e30),
            -(revisions if revisions is not None else 1e30))


def failure_digest(records: list[dict[str, Any]]) -> str:
    """Give the coach actual failures, reviewer feedback and retry counts."""
    return json.dumps([
        {key: record.get(key) for key in
         ("task", "status", "quality_score", "score", "accepted", "offline", "artifact_written",
          "calls", "retries", "review_revisions", "feedback", "error", "report_dir")}
        for record in records
    ], ensure_ascii=False, indent=2)


class Evolution:
    def __init__(self, workspace: str | Path, source_root: str | Path | None = None):
        self.workspace = Path(workspace).resolve()
        self.source_root = Path(source_root).resolve() if source_root else Path(__file__).resolve().parents[1]
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.state_path = self.workspace / "evolution_state.json"
        self.control_path = self.workspace / "control.json"
        self._guard = threading.RLock()
        self._panic = threading.Event()
        self._processes: dict[int, subprocess.Popen] = {}

    @contextlib.contextmanager
    def _file_guard(self):
        with self._guard, (self.workspace / ".state.lock").open("a") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            yield

    def control(self) -> dict[str, Any]:
        with self._file_guard():
            return dict(DEFAULT_CONTROL, **read_json(self.control_path, {}))

    def set_control(self, updates: dict[str, Any]) -> dict[str, Any]:
        allowed = set(DEFAULT_CONTROL)
        if set(updates) - allowed:
            raise ValueError("unknown control field")
        bounds = {"parallelism": (1, 4), "population_size": (2, 8), "episodes_per_task": (1, 16),
                  "generations": (1, 10000), "interval_seconds": (0, 86400), "timeout_seconds": (1, 86400)}
        for key, (low, high) in bounds.items():
            if key in updates and (type(updates[key]) is not int or not low <= updates[key] <= high):
                raise ValueError(f"{key} must be an integer between {low} and {high}")
        for key in ("enabled", "offline", "continuous"):
            if key in updates and type(updates[key]) is not bool:
                raise ValueError(f"{key} must be a boolean")
        if "backend" in updates and updates["backend"] not in ("codex", "claude"):
            raise ValueError("backend must be codex or claude")
        with self._file_guard():
            mode = read_json(self.state_path, {}).get("mode", {})
            for key in ("offline", "backend"):
                if key in updates and key in mode and updates[key] != mode[key]:
                    raise ValueError("evaluation mode is fixed for this workspace; use a new workspace")
            control = {**DEFAULT_CONTROL, **read_json(self.control_path, {}), **updates}
            atomic_json(self.control_path, control)
            return control

    def snapshot(self) -> dict[str, Any]:
        with self._file_guard():
            state = read_json(self.state_path, {})
            active_episodes = []
            for entry in state.get("active_children", {}).values():
                if not entry.get("episode_workspace"):
                    continue
                episode_state = read_json(Path(entry["episode_workspace"]) / "state.json", {})
                episodes = episode_state.get("episodes", [])
                if episodes:
                    episode = episodes[-1]
                    active_episodes.append({"label": entry["label"], **{key: episode.get(key) for key in
                        ("status", "calls", "retries", "review_revisions", "quality_score", "artifact_written")}})
            return {"state": state, "control": dict(DEFAULT_CONTROL, **read_json(self.control_path, {})),
                    "active": self.active(), "active_episodes": active_episodes, "workspace": str(self.workspace)}

    def active(self) -> bool:
        with (self.workspace / ".writer.lock").open("a") as stream:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(stream, fcntl.LOCK_UN)
                return False
            except BlockingIOError:
                return True

    def _change_state(self, callback):
        with self._file_guard():
            state = read_json(self.state_path, {})
            callback(state)
            state["updated_at"] = time.time()
            atomic_json(self.state_path, state)
            return state

    def _register(self, process: subprocess.Popen, label: str, episode_workspace: Path | None = None):
        with self._guard:
            self._processes[process.pid] = process
        def change(state):
            state.setdefault("active_children", {})[str(process.pid)] = {
                "pid": process.pid, "start_tick": _process_stamp(process.pid), "label": label,
                "episode_workspace": str(episode_workspace) if episode_workspace else None}
        self._change_state(change)

    def _unregister(self, process: subprocess.Popen):
        with self._guard:
            self._processes.pop(process.pid, None)
        self._change_state(lambda state: state.setdefault("active_children", {}).pop(str(process.pid), None))

    def emergency_stop(self):
        self.set_control({"enabled": False})
        self._panic.set()
        # Capture the whole tree BEFORE the parent dies: reviewers may have their
        # own session and become orphaned when the parent is stopped.
        children = self.snapshot()["state"].get("active_children", {})
        seeds = {entry["pid"]: entry["start_tick"] for entry in children.values() if entry.get("start_tick")}
        owned = _begin_owned_stop(seeds)
        # A non-daemon finite cleanup survives CLI/dashboard exit; abandoning it
        # would strand a reviewer that ignores TERM in another session.
        threading.Thread(target=_finish_owned_stop, args=(owned,), name="evolution-stop", daemon=False).start()
        def change(state):
            state["status"] = "stopping"
            state["emergency_stop_at"] = time.time()
        self._change_state(change)

    def _execute(self, argv: list[str], cwd: Path, log: Path, label: str,
                 stdin: str | None = None) -> tuple[int, str]:
        log.parent.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ)
        # Keep the authoritative package import in the parent, never child/PYTHONPATH.
        env["PYTHONPATH"] = str(self.source_root.parent)
        process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True)
        self._register(process, label, log.parent if label.startswith("gen") else None)
        stamp = _process_stamp(process.pid)
        seeds = {process.pid: stamp} if stamp else {}
        timed_out = False
        try:
            try:
                output, _ = process.communicate(stdin, timeout=self.control()["timeout_seconds"])
            except subprocess.TimeoutExpired:
                timed_out = True
                _terminate_owned(seeds)
                output, _ = process.communicate(timeout=5)
            log.write_text(output or "", encoding="utf-8")
            return (124 if timed_out else process.returncode), output or ""
        except BaseException:
            # Interrupts and IO failures must not unregister paid work while it
            # continues detached. Capture/stop its tree before dropping ownership.
            _terminate_owned(seeds)
            process.communicate(timeout=5)
            raise
        finally:
            self._unregister(process)

    def _copy_candidate(self, source: Path, destination: Path):
        destination.mkdir(parents=True, exist_ok=True)
        for name in ("engine", "prompts", "skills"):
            if (source / name).is_dir():
                shutil.copytree(source / name, destination / name,
                                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "reviewer-panel", "SAC_PROMPT.md"),
                                dirs_exist_ok=True)
        # Configuration is evolvable, but no reviewer configuration/assets are copied.
        if (source / "config.json").is_file():
            shutil.copy2(source / "config.json", destination / "config.json")
        forbidden = destination / "referee"
        if forbidden.exists():
            raise ValueError("candidate contains a frozen referee directory")

    def initialize(self, tasks: list[str] | None = None):
        with self._file_guard():
            state = read_json(self.state_path, {})
            task_path = self.workspace / "tasks.json"
            if state:
                existing = read_json(task_path, [])
                if tasks is not None and tasks != existing:
                    raise ValueError("tasks are fixed for this evolution workspace; use a new workspace")
                if tree_hash(self.source_root / "referee") != state["reviewer_hash"]:
                    raise ValueError("frozen reviewer changed; create a fresh comparison workspace")
                return state
            tasks = tasks or list(DEFAULT_TASKS)
            if not all(isinstance(task, str) and task.strip() for task in tasks):
                raise ValueError("tasks must contain nonempty direction strings")
            atomic_json(task_path, tasks)
            atomic_json(self.control_path, dict(DEFAULT_CONTROL, **read_json(self.control_path, {})))
            baseline = self.workspace / "candidates" / "baseline"
            self._copy_candidate(self.source_root, baseline)
            atomic_json(baseline / "lineage.json", {"kind": "baseline", "parents": [], "created_at": time.time()})
            state = {"version": 1, "generation": 0, "status": "idle", "history": [],
                     "population": ["baseline"], "elite": "baseline", "elite_score": None,
                     "baseline_hash": tree_hash(baseline), "reviewer_hash": tree_hash(self.source_root / "referee"),
                     "tasks_hash": hashlib.sha256(json.dumps(tasks).encode()).hexdigest(),
                     "coach_calls": 0, "coach_retries": 0, "active_children": {}, "jobs": {},
                     "lineage": {"baseline": {"kind": "baseline", "parents": []}},
                     "mode": {key: read_json(self.control_path, DEFAULT_CONTROL)[key] for key in ("offline", "backend")},
                     "created_at": time.time()}
            atomic_json(self.state_path, state)
            return state

    def _check_fixed(self, state: dict[str, Any]):
        if tree_hash(self.source_root / "referee") != state["reviewer_hash"]:
            raise ValueError("frozen reviewer was modified")
        if tree_hash(self.workspace / "candidates" / "baseline") != state["baseline_hash"]:
            raise ValueError("permanent baseline was modified")
        tasks = read_json(self.workspace / "tasks.json", [])
        if hashlib.sha256(json.dumps(tasks).encode()).hexdigest() != state["tasks_hash"]:
            raise ValueError("fixed evaluation task set was modified")

    def _evaluate(self, generation: int, name: str, task_index: int, repeat: int,
                  task: str, control: dict[str, Any]) -> dict[str, Any]:
        candidate = self.workspace / "candidates" / name
        episode = self.workspace / "runs" / f"gen{generation}" / name / f"task{task_index}-ep{repeat}"
        argv = [sys.executable, "-m", "autonomousmath", "run", "--backend", control["backend"],
                "--workspace", str(episode), "--direction", task, "--episodes", "1",
                "--candidate-root", str(candidate)]
        if control["offline"]:
            argv.append("--offline")
        if (candidate / "config.json").is_file():
            config = read_json(candidate / "config.json", {})
            if not isinstance(config, dict):
                raise ValueError("candidate config must be a JSON object")
            # Review settings and CLI executables remain parent-owned. Mutable code
            # can still choose research tools, but cannot swap the final review CLI.
            config = {key: value for key, value in config.items()
                      if not key.startswith("review_") and key not in
                      {"codex_command", "claude_command", "offline", "dry_run", "workspace",
                       "candidate_root", "direction", "episodes", "continuous"}}
            atomic_json(episode / "research_config.json", config)
            argv.extend(["--config", str(episode / "research_config.json")])
        started = time.time()
        returncode, output = self._execute(argv, self.source_root.parent, episode / "evaluation.log",
                                           f"gen{generation}/{name}/{task_index}/{repeat}")
        summary = None
        for line in reversed(output.splitlines()):
            try:
                value = json.loads(line)
                if isinstance(value, dict) and isinstance(value.get("results"), list):
                    summary = value
                    break
            except ValueError:
                continue
        result = dict(summary["results"][0]) if summary and summary["results"] else {
            "status": "cancelled" if self._panic.is_set() else "infra_fail", "score": 0,
            "accepted": False, "artifact_written": False, "error": f"engine exit {returncode}; see evaluation.log"}
        # Only parent CLI's reviewed report is authoritative; candidate claims are never consulted.
        result.update({"task": task, "task_index": task_index, "repeat": repeat, "candidate": name,
                       "offline": control["offline"], "duration_seconds": round(time.time() - started, 3),
                       "log": str(episode / "evaluation.log"), "returncode": returncode})
        if not result.get("feedback") and isinstance(result.get("final_review"), dict):
            result["feedback"] = result["final_review"].get("reviews", [])
        return result

    def _breed(self, generation: int, parents: list[str], name: str, kind: str,
               records: dict[str, list[dict[str, Any]]], offline: bool, backend: str):
        child = self.workspace / "candidates" / name
        if child.exists() and (child / "lineage.json").is_file():
            return  # Crash recovery never redoes a completed coach operation.
        child.mkdir(parents=True, exist_ok=True)
        self._copy_candidate(self.workspace / "candidates" / parents[0], child)
        # No referee assets or authority are available to the mutation operator.
        prompt = (
            f"You are the {kind} operator for AutonomousMath. Modify THIS candidate harness in place. "
            "Everything in engine/, prompts/, skills/ and config.json is mutable: code, tools, prompts, "
            "loop composition and research strategy. The final reviewer belongs to a separate parent "
            "process and is immutable. Do not modify any file outside this candidate, do not create a "
            "referee module, forge results, skip review or weaken final acceptance. Improve rigorous "
            "papers, written rate and genuine pass rate; reduce failed attempts through better research. "
            "Preserve worker entry and its documented artifact contract. Diagnose failures before editing.\n"
            + ("Make a coherent bold exploration beyond the current strategy.\n" if kind == "explore" else "")
            + "PARENT RESULTS:\n" + "\n".join(f"{parent}:\n{failure_digest(records.get(parent, []))}" for parent in parents)
        )
        if len(parents) > 1:
            other = self.workspace / "candidates" / parents[1]
            parts = []
            def order(path):
                relative = path.relative_to(other).as_posix()
                return (0 if relative == "prompts/goal.prompt" else
                        1 if path.suffix in (".prompt", ".js") else
                        2 if path.name == "SKILL.md" else 3, relative)
            for path in sorted(other.rglob("*"), key=order):
                if path.is_file() and path.suffix in (".py", ".md", ".json", ".prompt", ".js", ".yaml", ".yml", ".toml", ".env") and "__pycache__" not in path.parts:
                    parts.append(f"FILE {path.relative_to(other)}\n{path.read_text(errors='replace')}")
            reference = "\n".join(parts)
            prompt += "\nSECOND PARENT HARNESS (reference only):\n" + reference[:100000]
            if len(reference) > 100000:
                prompt += ("\n[Second-parent inline reference truncated at 100000 characters. "
                           f"Read remaining files from this READ-ONLY parent directory: {other}. "
                           "Do not modify that directory; edit only THIS child.]\n")
        atomic_json(child / "coach_input.json", {"kind": kind, "parents": parents, "prompt": prompt,
                                                  "offline": offline})
        old_hash = harness_hash(child)
        if offline:
            # Demonstrates copying/edits/lineage without claiming LLM strategy improvement.
            demo = child / "prompts" / "EVOLUTION_DEMO.md"
            demo.parent.mkdir(parents=True, exist_ok=True)
            demo.write_text(f"Offline structural demo: {kind}, generation {generation}, parents {parents}.\n"
                            "No model was called and no research quality improvement is claimed.\n")
            outcome = "offline_demo_edit"
        else:
            if backend == "codex":
                argv = ["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", str(child), "-"]
            else:
                # Match the noninteractive research-worker tool/edit policy; no bypass.
                argv = ["claude", "-p", "--output-format", "text", "--permission-mode", "acceptEdits",
                        "--permission-prompts", "none", "--allowedTools",
                        "Bash,Read,Write,Edit,Glob,Grep,WebSearch,WebFetch,Agent,Skill"]
            outcome = "clone"
            for attempt in range(2):
                self._change_state(lambda state: state.update(coach_calls=state.get("coach_calls", 0) + 1,
                    coach_retries=state.get("coach_retries", 0) + (1 if attempt else 0)))
                rc, _ = self._execute(argv, child, child / "coach.log", f"coach/{name}", prompt)
                if rc == 0 and harness_hash(child) != old_hash:
                    outcome = "edited"
                    break
                if self._panic.is_set():
                    outcome = "cancelled"
                    break
        if any(path.exists() or path.is_symlink() for path in
               (child / "referee", child / "skills" / "reviewer-panel")):
            raise ValueError("coach attempted to add frozen reviewer assets")
        lineage = {"kind": kind, "parents": parents, "generation": generation,
                   "outcome": outcome, "offline": offline, "created_at": time.time()}
        atomic_json(child / "lineage.json", lineage)
        self._change_state(lambda state: state.setdefault("lineage", {}).update({name: lineage}))

    def run(self, *, generations: int | None = None, tasks: list[str] | None = None,
            enable: bool = True, settings: dict[str, Any] | None = None) -> dict[str, Any]:
        with (self.workspace / ".writer.lock").open("a") as writer:
            try:
                fcntl.flock(writer, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise EvolutionBusy("this workspace already has an active evolution writer") from error
            self._panic.clear()
            if settings:
                self.set_control(settings)
            state = self.initialize(tasks)
            if enable:
                self.set_control({"enabled": True})
            target = state["generation"] + (generations or self.control()["generations"])
            def start_state(s):
                s.update(status="running", active_children={})
                s.pop("error", None)
            self._change_state(start_state)
            try:
                while self.control()["enabled"] and not self._panic.is_set():
                    state = read_json(self.state_path, {})
                    control = self.control()
                    if not control["continuous"] and state["generation"] >= target:
                        break
                    self._check_fixed(state)
                    generation = state["generation"]
                    # A resumed partial generation keeps its original task multiplicity/backend.
                    plan = state.get("generation_plan")
                    if not plan or plan.get("generation") != generation:
                        plan = {"generation": generation, "episodes_per_task": control["episodes_per_task"],
                                "offline": control["offline"], "backend": control["backend"]}
                        self._change_state(lambda s: s.update(generation_plan=plan))
                    control.update({key: plan[key] for key in ("episodes_per_task", "offline", "backend")})
                    tasks = read_json(self.workspace / "tasks.json", [])
                    participants = list(dict.fromkeys(["baseline"] + state["population"]))
                    jobs = [(name, index, repeat, task) for name in participants for index, task in enumerate(tasks)
                            for repeat in range(control["episodes_per_task"])]
                    pending = []
                    for name, index, repeat, task in jobs:
                        key = f"{generation}/{name}/{index}/{repeat}"
                        previous = state["jobs"].get(key)
                        if previous is None or previous.get("status") in ("cancelled", "infra_fail", "blocked", "checkpoint"):
                            pending.append((key, name, index, repeat, task))
                    with concurrent.futures.ThreadPoolExecutor(max_workers=control["parallelism"]) as pool:
                        active: dict[concurrent.futures.Future, str] = {}
                        try:
                            while pending or active:
                                while pending and len(active) < control["parallelism"] and self.control()["enabled"] and not self._panic.is_set():
                                    key, name, index, repeat, task = pending.pop(0)
                                    active[pool.submit(self._evaluate, generation, name, index, repeat, task, control)] = key
                                if not active:
                                    break
                                done, _ = concurrent.futures.wait(active, timeout=0.25,
                                                                 return_when=concurrent.futures.FIRST_COMPLETED)
                                for future in done:
                                    key = active.pop(future)
                                    result = future.result()
                                    self._change_state(lambda s, k=key, r=result: s["jobs"].update({k: r}))
                        except BaseException:
                            # Ctrl-C lands on the scheduling thread, not a worker's
                            # communicate(): stop owned calls before executor waits.
                            self.emergency_stop()
                            raise
                    state = read_json(self.state_path, {})
                    # Soft stop stops scheduling new episodes; in-flight results are checkpointed.
                    if not self.control()["enabled"] or self._panic.is_set():
                        break
                    records = {name: [state["jobs"][f"{generation}/{name}/{index}/{repeat}"]
                                      for index, _ in enumerate(tasks) for repeat in range(control["episodes_per_task"])]
                               for name in participants}
                    metrics = {name: aggregate(value) for name, value in records.items()}
                    if not any(value["n_valid"] for value in metrics.values()):
                        self.set_control({"enabled": False})
                        self._change_state(lambda s: s.update(status="blocked",
                            error="All evaluations were blocked by infrastructure; no selection or mutation was performed."))
                        break
                    ranked = sorted(participants, key=lambda name: selection_key(metrics[name]), reverse=True)
                    champion = ranked[0]
                    elite = state["elite"]
                    champion_key = selection_key(metrics[champion])
                    previous_elite_key = state.get("elite_key")
                    if previous_elite_key is None or champion_key > tuple(previous_elite_key):
                        elite = champion
                    best = state.get("elite_score")
                    elite_score = max(best if best is not None else -1.0, metrics[champion]["composite"])
                    summary = {"generation": generation, "metrics": metrics, "champion": champion,
                               "elite": elite, "baseline": "baseline", "offline": control["offline"],
                               "gap_vs_baseline": round(metrics[champion]["composite"] - metrics["baseline"]["composite"], 4),
                               "tasks_hash": state["tasks_hash"], "finished_at": time.time()}
                    atomic_json(self.workspace / "runs" / f"gen{generation}" / "results.json", summary)
                    self._change_state(lambda s: s.update(status="breeding"))
                    other = next((name for name in ranked if name != elite), "baseline")
                    children = [(f"gen{generation + 1}-mutate", [elite], "mutate"),
                                (f"gen{generation + 1}-explore", [elite], "explore")]
                    if other != elite:
                        children.insert(0, (f"gen{generation + 1}-cross", [elite, other], "crossover"))
                    next_population = [elite]
                    for name, parents, kind in children:
                        if len(next_population) >= control["population_size"] or not self.control()["enabled"]:
                            break
                        self._breed(generation + 1, parents, name, kind, records, control["offline"], control["backend"])
                        next_population.append(name)
                    if not self.control()["enabled"]:
                        break
                    self._check_fixed(read_json(self.state_path, {}))
                    def advance(s):
                        s["generation"] = generation + 1
                        s["population"] = next_population
                        s["elite"] = elite
                        s["elite_score"] = elite_score
                        s["elite_key"] = list(champion_key if previous_elite_key is None or champion_key > tuple(previous_elite_key)
                                              else previous_elite_key)
                        s["history"].append(summary)
                        s["status"] = "running"
                    self._change_state(advance)
                    end = time.monotonic() + control["interval_seconds"]
                    while time.monotonic() < end and self.control()["enabled"] and not self._panic.is_set():
                        self._panic.wait(min(0.25, end - time.monotonic()))
                status = "paused" if not self.control()["enabled"] else "completed"
                if read_json(self.state_path, {}).get("status") == "blocked":
                    status = "blocked"
                self.set_control({"enabled": False})
                self._change_state(lambda s: s.update(status=status))
            except BaseException as error:
                self.set_control({"enabled": False})
                self._change_state(lambda s: s.update(status="error", error=str(error)))
                raise
            return self.snapshot()
