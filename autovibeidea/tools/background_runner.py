#!/usr/bin/env python3
"""Linux background supervisor: own the task tree, reap it, then publish status.

Cancellation uses pidfds and /proc start times, never an unverified saved PID.
As a child subreaper, this process also owns grandchildren that detach or outlive
their parent. The launcher's FD 9 lock is intentionally NOT passed to workers.
"""
import argparse
import ctypes
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
GRACE_SECONDS = 2.0


def identity(pid):
    try:
        fields = (Path("/proc") / str(pid) / "stat").read_text().rsplit(")", 1)[1].split()
        return {"pid": pid, "ppid": int(fields[1]), "start": fields[19], "state": fields[0]}
    except (OSError, ValueError, IndexError):
        return None


def signal_process(record, signum):
    """Hold an identity-stable handle before comparing and signaling."""
    try:
        fd = os.pidfd_open(record["pid"])
    except ProcessLookupError:
        return False
    try:
        current = identity(record["pid"])
        if current is None or current["start"] != record["start"]:
            return False
        signal.pidfd_send_signal(fd, signum)
        return True
    except ProcessLookupError:
        return False
    finally:
        os.close(fd)


def descendants():
    records = {}
    for path in Path("/proc").iterdir():
        if path.name.isdigit():
            record = identity(int(path.name))
            if record:
                records[record["pid"]] = record
    owned = {os.getpid()}
    while True:
        found = {pid for pid, record in records.items() if record["ppid"] in owned}
        if found <= owned:
            break
        owned.update(found)
    return [records[pid] for pid in owned - {os.getpid()} if pid in records]


def reap_adopted(worker):
    # Let Popen reap its own child first, preserving the actual worker exit code.
    worker.poll()
    if worker.returncode is not None:
        while True:
            try:
                pid, _ = os.waitpid(-1, os.WNOHANG)
            except ChildProcessError:
                return
            if pid == 0:
                return


def finish_tree(worker):
    """Terminate descendants, including detached/adopted ones, before unlock."""
    deadline = time.monotonic() + GRACE_SECONDS
    while True:
        reap_adopted(worker)
        children = descendants()
        if not children:
            return
        signum = signal.SIGTERM if time.monotonic() < deadline else signal.SIGKILL
        for child in children:
            if child["state"] != "Z":
                signal_process(child, signum)
        time.sleep(0.05)


def write_state(state):
    tmp = OUTPUTS / ".pipeline.run.json.tmp"
    tmp.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    tmp.replace(OUTPUTS / "pipeline.run.json")


def require_linux_handles():
    if not sys.platform.startswith("linux") or not hasattr(os, "pidfd_open") or not hasattr(signal, "pidfd_send_signal"):
        raise RuntimeError("background control requires Linux/WSL2, Python 3.10+ and pidfd support")
    fd = os.pidfd_open(os.getpid())  # Fail before launching on an unsupported kernel.
    os.close(fd)


def run(direction, venue):
    OUTPUTS.mkdir(exist_ok=True)
    requested = None

    def request_stop(signum, _frame):
        nonlocal requested
        if requested is None:
            requested = signum

    for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(signum, request_stop)
    worker = None
    rc = 1
    state = {"pid": os.getpid(), "root": str(ROOT), "status": "starting"}
    try:
        require_linux_handles()
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.prctl(36, 1, 0, 0, 0) != 0:  # PR_SET_CHILD_SUBREAPER
            raise OSError(ctypes.get_errno(), "cannot enable child subreaper")
        state["start"] = identity(os.getpid())["start"]
        state["status"] = "running"
        write_state(state)
        with (OUTPUTS / "pipeline.log").open("w", encoding="utf-8") as log:
            if requested is None:
                worker = subprocess.Popen(
                    ["bash", str(ROOT / "tools/run_codex_skill.sh"),
                     "--skill", "skills/idea-pipeline/SKILL.md",
                     "--args", f'"{direction}" -- venue: {venue}',
                     "--role", "an automated research agent"],
                    cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                    start_new_session=True, close_fds=True,
                )
                while worker.poll() is None and requested is None:
                    time.sleep(0.05)
                code = worker.returncode
                rc = code if code is not None and code >= 0 else 128 - code if code is not None else 1
    except (OSError, RuntimeError) as exc:
        print(f"Background runner failed: {exc}", file=sys.stderr)
        rc = 1
    finally:
        if worker is not None:
            finish_tree(worker)
        if requested is not None:
            rc = 128 + requested
        state.update(status="stopped" if requested else "completed" if rc == 0 else "failed", exit_code=rc)
        write_state(state)
        if rc == 0:
            (OUTPUTS / "DONE").write_text(datetime.now(timezone.utc).isoformat() + "\n")
        else:
            (OUTPUTS / "FAILED").write_text(str(rc) + "\n")
    return rc


def stop():
    require_linux_handles()
    try:
        state = json.loads((OUTPUTS / "pipeline.run.json").read_text(encoding="utf-8"))
        if state.get("root") != str(ROOT) or not isinstance(state.get("pid"), int) or state["pid"] <= 1:
            raise ValueError("invalid runner identity")
        if state.get("status") not in ("starting", "running"):
            print(f"Pipeline is already {state.get('status')}; no signal sent.")
            return 0
        fd = os.pidfd_open(state["pid"])
    except (OSError, ValueError, KeyError):
        print("No verified running pipeline. If it is still starting, retry shortly; no signal sent.", file=sys.stderr)
        return 1
    try:
        current = identity(state["pid"])
        if not current or current["start"] != state.get("start"):
            print("Stale runner identity; no signal sent.", file=sys.stderr)
            return 1
        signal.pidfd_send_signal(fd, signal.SIGTERM)
        if not select.select([fd], [], [], GRACE_SECONDS + 6)[0]:
            print("Stop requested, but cleanup is still pending; workspace remains locked.", file=sys.stderr)
            return 1
        finished = json.loads((OUTPUTS / "pipeline.run.json").read_text(encoding="utf-8"))
        if (finished.get("pid"), finished.get("start")) != (state["pid"], state["start"]) or finished.get("status") not in ("stopped", "completed", "failed"):
            print("Runner exited without a matching cleanup receipt; inspect launcher.log and --status.", file=sys.stderr)
            return 1
        print("Pipeline stopped; its child processes have been terminated.")
        return 0
    except ProcessLookupError:
        print("Pipeline already exited; no further signal sent.")
        return 0
    finally:
        os.close(fd)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    subs = ap.add_subparsers(dest="action", required=True)
    start = subs.add_parser("run")
    start.add_argument("direction")
    start.add_argument("venue", nargs="?", default="ICML")
    subs.add_parser("stop")
    args = ap.parse_args()
    return stop() if args.action == "stop" else run(args.direction, args.venue)


if __name__ == "__main__":
    os.umask(0o077)
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError) as exc:
        print(f"Background control failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
