#!/usr/bin/env python3
"""Run deterministic EAR tools and a synthetic rebuttal dry-run; no models or keys.

This verifies installation and wiring, NOT generated research/rebuttal quality.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def run(command, cwd, env=None):
    result = subprocess.run([sys.executable, "-B", *map(str, command)], cwd=cwd,
                            env=env, text=True, capture_output=True, check=True)
    return result.stdout


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, help="new directory only; default: a fresh temporary directory")
    args = ap.parse_args()
    if args.output:
        out = args.output.resolve()
        if out.exists():
            ap.error("--output already exists; choose a new directory (nothing is overwritten)")
        out.mkdir(parents=True)
    else:
        out = Path(tempfile.mkdtemp(prefix="ear-offline-demo-"))

    ideas = out / "autovibeidea"
    ideas.mkdir()
    for name in ("IDEA_NODES.jsonl", "SEARCH_STATE.json"):
        shutil.copy2(ROOT / "autovibeidea/examples/search-demo" / name, ideas / name)
    tool = ROOT / "autovibeidea/tools"
    validation = run([tool / "idea_nodes.py", "--path", ideas / "IDEA_NODES.jsonl", "validate"], out)
    node_count = sum(bool(line.strip()) for line in (ideas / "IDEA_NODES.jsonl").read_text(encoding="utf-8").splitlines())
    report = run([tool / "mcts_search.py", "--path", ideas / "IDEA_NODES.jsonl",
                  "--state", ideas / "SEARCH_STATE.json", "report", "--provenance"], out)
    (ideas / "SEARCH_REPORT.txt").write_text(report, encoding="utf-8")
    print(validation.strip())

    demo = out / "rebuttal"
    # Copy only the source formats needed for a standalone dry-run, never real campaigns or .env files.
    for relative, patterns in {
        "harness": ("*.md", "HARNESS_VERSION"),
        "harness/templates": ("*.md", "*.json"),
        "harness/stages": ("*.md",),
        "harness/strategies": ("*.md", "*.json"),
        "harness/runner": ("*.py",),
        "rebuttal_verifier": ("*.py",),
    }.items():
        dest = demo / relative
        dest.mkdir(parents=True, exist_ok=True)
        for pattern in patterns:
            for source in (ROOT / "rebuttal" / relative).glob(pattern):
                shutil.copy2(source, dest / source.name)
    slug = "synthetic-demo"
    fixture = ROOT / "rebuttal/examples/offline-demo"
    campaign = demo / "campaigns" / slug
    campaign.mkdir(parents=True)
    shutil.copy2(fixture / "REBUTTAL_CARD.json", campaign / "REBUTTAL_CARD.json")
    paper = demo / "papers" / slug
    shutil.copytree(fixture / "Tex", paper / "Tex")
    shutil.copy2(fixture / "review.md", paper / "review.md")
    print(run([ROOT / "rebuttal/harness/instantiate.py", "--slug", slug,
               "--harness", demo / "harness", "--campaigns", demo / "campaigns"], out).strip())
    for name in ("CLAUDE", "GOAL", "SPEC", "VERIFY", "RESOURCE"):
        if "{{" in (campaign / f"{name}.md").read_text(encoding="utf-8"):
            raise RuntimeError(f"Unfilled placeholder in {name}.md")
    env = dict(os.environ, AUTOREBUTTAL_ROOT=str(demo), PYTHONDONTWRITEBYTECODE="1")
    dry = run([demo / "harness/runner/orchestrate.py", "--paper", slug, "--dry-run"], out, env)
    (demo / "DRY_RUN.txt").write_text(dry, encoding="utf-8")
    summary = {"mode": "offline", "model_calls": 0, "synthetic_rebuttal_inputs": True,
               "idea_nodes": node_count, "contracts_rendered": 5, "rebuttal_dry_run": "passed",
               "quality_evaluated": False}
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("PASS: idea validation/report, five contracts, and synthetic rebuttal dry-run.")
    print(f"Outputs: {out}")
    print("No model called. No generated rebuttal or research-quality claim is implied.")
    return 0


if __name__ == "__main__":
    os.umask(0o077)
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(exc.stderr, file=sys.stderr)
        raise SystemExit(exc.returncode)
