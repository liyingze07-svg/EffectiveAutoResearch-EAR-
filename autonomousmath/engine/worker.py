"""Bounded child execution of the mutable engine, outside the fixed referee process."""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
from pathlib import Path
import sys

from .config import EngineConfig
from .prompts import build_prompt, install_assets
from .providers import CLIProvider, OfflineProvider
from .state import atomic_json


def run_turn(request: dict) -> dict:
    """Candidate engines may replace this function and its complete research logic."""
    config = EngineConfig.load(overrides=request["config"])
    campaign = Path(request["campaign_dir"])
    engine_root = Path(request["engine_root"])
    install_assets(engine_root, campaign)
    prompt = build_prompt(engine_root, Path(request["fixed_root"]), campaign,
                          config.direction, request["turn"], request.get("feedback", ""))
    (campaign / "GOAL_PROMPT.md").write_text(prompt, encoding="utf-8")
    provider = OfflineProvider(config) if config.offline else CLIProvider(config)
    return provider.run(prompt, campaign, request.get("session_id")).as_dict()


def _candidate_worker(candidate_root: Path):
    base = candidate_root / "engine"
    if not (base / "worker.py").is_file() or not (base / "__init__.py").is_file():
        raise ValueError("candidate-root requires engine/__init__.py and engine/worker.py")
    spec = importlib.util.spec_from_file_location("_autonomousmath_candidate_engine",
                                                  base / "__init__.py", submodule_search_locations=[str(base)])
    if spec is None or spec.loader is None:
        raise ValueError("Cannot load candidate engine")
    package = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = package
    spec.loader.exec_module(package)
    return importlib.import_module(spec.name + ".worker").run_turn


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--response", required=True, type=Path)
    parser.add_argument("--candidate-root", type=Path)
    args = parser.parse_args()
    request = json.loads(args.request.read_text(encoding="utf-8"))
    execute = _candidate_worker(args.candidate_root) if args.candidate_root else run_turn
    try:
        response = execute(request)
    except Exception as exc:
        response = {"returncode": 1, "error_kind": "worker_error", "text": "",
                    "reason": type(exc).__name__}
    atomic_json(args.response, response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
