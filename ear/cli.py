"""Thin dispatch; each research workflow retains its own execution semantics."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from .report import show_report
from .workspaces import (ROOT, initialize_rebuttal, paper_slug, prepare_idea,
                         rebuttal_status, require_workspace)


def _run(command: list[str], *, env=None) -> int:
    return subprocess.run(command, env=env).returncode


def _python(script: Path, args: list[str], *, env=None) -> int:
    return _run([sys.executable, "-B", str(script), *args], env=env)


def _workspace(value: str) -> Path:
    return Path(value).expanduser().resolve()


def _math(args: list[str]) -> int:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    return _run([sys.executable, "-B", "-m", "autonomousmath", *args], env=env)


def _idea(args: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="ear idea", add_help=False, allow_abbrev=False)
    parser.add_argument("--workspace", type=_workspace)
    known, forwarded = parser.parse_known_args(args)
    if "--help" in forwarded or "-h" in forwarded:
        print("ear idea [--workspace PATH] <run.sh arguments>", flush=True)
        print("A new workspace receives source/templates only; marked workspaces are reused.", flush=True)
        print("Omit --workspace to use the original autovibeidea directory.\n", flush=True)
        return _run(["bash", str(ROOT / "autovibeidea/run.sh"), "--help"])
    root = ROOT / "autovibeidea"
    if known.workspace:
        root = prepare_idea(known.workspace, create=not any(a in forwarded for a in ("--status", "--stop")))
    return _run(["bash", str(root / "run.sh"), *forwarded])


def _rebuttal(args: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="ear rebuttal", description="Initialize inputs, run the existing harness, or inspect artifacts.")
    parser.add_argument("command", choices=("init", "run", "status"))
    parser.add_argument("args", nargs=argparse.REMAINDER)
    action = parser.parse_args(args)
    sub = argparse.ArgumentParser(prog=f"ear rebuttal {action.command}", allow_abbrev=False)
    sub.add_argument("--workspace", required=True, type=_workspace)
    if action.command == "init":
        sub.add_argument("--from-example", action="store_true", required=True,
                         help="copy the synthetic fixture; replace its inputs before real use")
        sub.add_argument("--paper", default="synthetic-demo")
        options = sub.parse_args(action.args)
        initialize_rebuttal(options.workspace, paper_slug(options.paper))
        print(f"Created synthetic rebuttal workspace: {options.workspace}")
        print(f"Paper: {options.paper}; five contracts rendered; no models called.")
        print("Replace papers/<paper>/ inputs and the campaign card for your own case;")
        print("then regenerate contracts with harness/instantiate.py --force before live use.")
        return 0
    if action.command == "status":
        sub.add_argument("--paper")
        options = sub.parse_args(action.args)
        print(json.dumps(rebuttal_status(options.workspace, options.paper), indent=2))
        return 0
    group = sub.add_mutually_exclusive_group(required=True)
    group.add_argument("--paper")
    group.add_argument("--all", action="store_true")
    sub.epilog = "Other options pass through to harness/runner/orchestrate.py (e.g. --dry-run, --from r1, --model, --judge-model)."
    options, forwarded = sub.parse_known_args(action.args)
    require_workspace(options.workspace, "rebuttal")
    if options.paper:
        paper_slug(options.paper)
        if not (options.workspace / "campaigns" / options.paper / "REBUTTAL_CARD.json").is_file():
            raise ValueError(f"No campaign card for {options.paper}")
    selection = ["--all"] if options.all else ["--paper", options.paper]
    env = dict(os.environ, AUTOREBUTTAL_ROOT=str(options.workspace), PYTHONDONTWRITEBYTECODE="1")
    return _python(options.workspace / "harness/runner/orchestrate.py", selection + forwarded, env=env)


def _control(command: str, args: list[str]) -> int:
    parser = argparse.ArgumentParser(prog=f"ear {command}")
    parser.add_argument("workspace", type=_workspace)
    parser.add_argument("--workflow", choices=("math", "idea", "rebuttal"), required=True)
    options = parser.parse_args(args)
    if options.workflow == "math":
        return _math([command, "--workspace", str(options.workspace)])
    if options.workflow == "idea":
        return _idea([f"--{command}", "--workspace", str(options.workspace)])
    if command == "stop":
        raise ValueError("Rebuttal has no managed stop command; interrupt its foreground process with Ctrl-C.")
    print(json.dumps(rebuttal_status(options.workspace), indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ear", description="EAR: idea discovery, mathematical research and evidence-grounded rebuttals.",
        epilog="Source checkout: python3 -m ear <command> --help. Offline demos need Python 3.10+ only.")
    commands = {"demo": "View report results or run the offline wiring check", "doctor": "Check local prerequisites",
        "idea": "Run AutoVibeIdea; optionally isolate a workspace", "math": "Forward to AutonomousMath (run/doctor/status/stop)",
        "rebuttal": "Initialize, run or inspect a rebuttal workspace", "status": "Read workflow state or artifacts",
        "stop": "Request the workflow's existing stop operation (math/idea)"}
    parser.add_argument("command", choices=commands, help="; ".join(f"{k}: {v}" for k, v in commands.items()))
    parser.add_argument("args", nargs=argparse.REMAINDER)
    options = parser.parse_args(argv)
    try:
        if options.command == "demo":
            sub = argparse.ArgumentParser(prog="ear demo")
            modes = sub.add_subparsers(dest="mode", required=True)
            report = modes.add_parser("report", help="Recompute released aggregates; no model calls")
            report.add_argument("--json", action="store_true")
            check = modes.add_parser("check", help="Validate offline workflow wiring; no model calls")
            check.add_argument("--output", type=_workspace, help="new directory only")
            demo = sub.parse_args(options.args)
            if demo.mode == "report":
                return show_report(demo.json)
            return _python(ROOT / "scripts/offline_demo.py", ["--output", str(demo.output)] if demo.output else [])
        if options.command == "doctor":
            return _python(ROOT / "scripts/doctor.py", options.args)
        if options.command in {"status", "stop"}:
            return _control(options.command, options.args)
        return {"idea": _idea, "math": _math, "rebuttal": _rebuttal}[options.command](options.args)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"ear: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130
