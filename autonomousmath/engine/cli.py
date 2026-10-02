from __future__ import annotations

import argparse
import json
from pathlib import Path
import signal
import sys

from .config import EngineConfig
from .runner import doctor, run
from .state import read_json


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="autonomousmath", description="Complete goal-driven research, with a separate fixed referee.")
    parser.add_argument("--version", action="version", version="AutonomousMath 0.1.0")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "doctor"):
        cmd = commands.add_parser(name, help="Execute goal episodes" if name == "run" else "Check dependencies without calling models")
        cmd.add_argument("--config", type=Path, help="JSON engine configuration")
        cmd.add_argument("--backend", choices=("codex", "claude"))
        cmd.add_argument("--workspace", "--data-root", dest="workspace")
        cmd.add_argument("--offline", action="store_true", default=None, help="Deterministic reject/refine/accept fixture; never a research pass")
        if name == "doctor":
            continue
        cmd.add_argument("--direction")
        group = cmd.add_mutually_exclusive_group()
        group.add_argument("--episodes", type=int)
        group.add_argument("--continuous", action="store_true", default=None)
        cmd.add_argument("--candidate-root", help="Mutable engine/prompts/skills root; fixed referee remains in the parent package")
        cmd.add_argument("--dry-run", action="store_true", default=None)
        cmd.add_argument("--model")
        cmd.add_argument("--effort")
        cmd.add_argument("--timeout-sec", type=int)
        cmd.add_argument("--max-turns", type=int)
        cmd.add_argument("--max-calls", type=int)
        cmd.add_argument("--max-review-revisions", type=int)
        cmd.add_argument("--max-infra-retries", type=int)
        cmd.add_argument("--cooldown-sec", type=int)
        cmd.add_argument("--interval-sec", type=int)
        cmd.add_argument("--review-backends", help="Exactly two comma-separated independent backends")
        cmd.add_argument("--no-resume", dest="resume", action="store_false", default=None)
        cmd.add_argument("--sandbox", choices=("workspace-write", "danger-full-access"))
    for name in ("status", "stop"):
        cmd = commands.add_parser(name, help="Read state" if name == "status" else "Stop before the next goal/review batch; retain checkpoints")
        cmd.add_argument("--workspace", "--data-root", default=".autonomousmath")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    def stop_signal(signum, frame):
        raise KeyboardInterrupt
    previous_handler = signal.signal(signal.SIGTERM, stop_signal)
    try:
        if args.command in ("status", "stop"):
            root = Path(args.workspace).expanduser().resolve()
            if args.command == "stop":
                root.mkdir(parents=True, exist_ok=True)
                (root / "STOP").write_text("operator stop\n", encoding="utf-8")
                result = {"status": "stop_requested", "workspace": str(root)}
            else:
                result = read_json(root / "state.json", {"status": "not_started", "workspace": str(root)})
        else:
            overrides = vars(args).copy()
            if overrides.get("review_backends"):
                overrides["review_backends"] = [v.strip() for v in overrides["review_backends"].split(",")]
            if overrides.get("episodes") is not None:
                overrides["continuous"] = False
            config = EngineConfig.load(args.config, overrides)
            result = doctor(config) if args.command == "doctor" else run(config)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 2 if result.get("status") == "blocked" or result.get("ok") is False else 0
    except (ValueError, OSError, RuntimeError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False))
        return 2
    finally:
        signal.signal(signal.SIGTERM, previous_handler)


if __name__ == "__main__":
    raise SystemExit(main())
