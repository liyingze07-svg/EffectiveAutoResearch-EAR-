#!/usr/bin/env python3
"""Install this engine's skills into an explicitly selected local workspace."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def install(workspace: Path, *, host: str = "both", force: bool = False) -> list[Path]:
    source = Path(__file__).resolve().parents[1] / "skills"
    skills = sorted(p for p in source.iterdir() if p.is_dir() and (p / "SKILL.md").is_file())
    if not skills:
        raise ValueError(f"No packaged skills found in {source}")
    workspace = workspace.expanduser().resolve()
    destinations = []
    roots = {"claude": [".claude"], "codex": [".agents"], "both": [".claude", ".agents"]}[host]
    for root in roots:
        for skill in skills:
            target = workspace / root / "skills" / skill.name
            # Replacing a target symlink could write or delete outside the workspace.
            for ancestor in [workspace / root, workspace / root / "skills", target]:
                if ancestor.is_symlink():
                    raise ValueError(f"Refusing symlink installation destination: {ancestor}")
            if target.exists() and not force:
                raise FileExistsError(f"Skill already installed: {target}; pass --force to replace")
            if target.exists() and not target.is_dir():
                raise ValueError(f"Installation destination is not a directory: {target}")
            if source == target or source in target.parents or target in source.parents:
                raise ValueError("Choose an installation workspace outside the packaged skills")
            destinations.append((skill, target))

    installed = []
    for skill, target in destinations:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(skill, target)
        installed.append(target)
    return installed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True, help="Destination research workspace")
    parser.add_argument("--host", choices=["both", "claude", "codex"], default="both")
    parser.add_argument("--force", action="store_true", help="Replace same-named workspace skills")
    args = parser.parse_args()
    try:
        paths = install(args.workspace, host=args.host, force=args.force)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Skill installation failed: {exc}\n")
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
