from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp-{os.getpid()}")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


class StateStore:
    def __init__(self, root: Path):
        self.root = root
        self.path = root / "state.json"
        self.state = read_json(self.path, {"version": 1, "episodes": [], "status": "idle"})
        if not isinstance(self.state, dict) or not isinstance(self.state.get("episodes"), list):
            raise ValueError("Invalid state.json; preserve it and choose a new workspace")

    def save(self) -> None:
        self.state["updated_at"] = utc_now()
        atomic_json(self.path, self.state)

    def event(self, kind: str, **fields: Any) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        event = {"ts": utc_now(), "event": kind, **fields}
        with (self.root / "events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + "\n")


@contextmanager
def runtime_lock(root: Path):
    """One supervisor per data directory; never take over a live writer."""
    root.mkdir(parents=True, exist_ok=True)
    path = root / ".runner.lock"
    # flock releases even after SIGKILL; the PID is for display, not ownership.
    import fcntl
    with path.open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("Another engine owns this workspace") from exc
        lock.seek(0)
        lock.truncate()
        lock.write(str(os.getpid()))
        lock.flush()
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def wait_until(root: Path, deadline: float) -> bool:
    """Interruptible pacing: a STOP file ends the loop, including quota backoff."""
    while time.time() < deadline:
        if (root / "STOP").exists():
            return False
        time.sleep(min(1.0, max(0.0, deadline - time.time())))
    return not (root / "STOP").exists()


def terminate_tree(process: subprocess.Popen) -> None:
    """Stop a bounded call's descendants without signalling the supervisor group."""
    descendants = []
    pending = [process.pid]
    # Linux child lists expose PIDs only, never sensitive command arguments.
    while pending:
        parent = pending.pop()
        try:
            children = Path(f"/proc/{parent}/task/{parent}/children").read_text().split()
        except OSError:
            children = []
        for value in children:
            pid = int(value)
            descendants.append(pid)
            pending.append(pid)
    pids = list(reversed(descendants)) + [process.pid]
    for signum in (signal.SIGTERM, signal.SIGKILL):
        for pid in pids:
            try:
                os.kill(pid, signum)
            except ProcessLookupError:
                pass
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            continue
        if signum == signal.SIGTERM:
            # A parent can exit while its child ignores SIGTERM; still clean descendants.
            continue
