"""Small, explicit workspace adapters; the original workflows own their state."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MARKER = ".ear-workspace.json"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def require_workspace(path: Path, workflow: str) -> dict:
    marker = path / MARKER
    if not marker.is_file():
        raise ValueError(f"Not an EAR {workflow} workspace: {path}")
    metadata = read_json(marker)
    if not isinstance(metadata, dict) or metadata.get("workflow") != workflow:
        raise ValueError(f"Workspace belongs to a different workflow: {path}")
    return metadata


def _mark(path: Path, workflow: str, **extra):
    (path / MARKER).write_text(json.dumps({"workflow": workflow,
        "source_checkout": str(ROOT), **extra}, indent=2) + "\n", encoding="utf-8")


def _check_destination(path: Path):
    # In particular, avoid recursively copying a source tree into itself.
    for name in ("autovibeidea", "autonomousmath", "rebuttal", "ear", "docs", "assets", "examples", "scripts", "tests", ".git", ".github"):
        if path.is_relative_to(ROOT / name):
            raise ValueError("Place workspaces under runs/ or outside the checkout, not inside source directories")


def _copy_resources(source: Path, destination: Path):
    """Copy source formats, never symlinks, credentials, caches, or run outputs."""
    excluded = {"outputs", "refine-logs", "__pycache__", "campaigns", "papers", "archive"}
    for item in sorted(source.rglob("*")):
        relative = item.relative_to(source)
        if any(part.startswith(".") or part in excluded for part in relative.parts):
            continue
        if item.is_symlink() or any(parent.is_symlink() for parent in item.parents if parent != source):
            continue
        if not item.is_file() or ".local." in item.name:
            continue
        if item.suffix not in {".py", ".sh", ".md", ".json", ".txt"} and item.name != "HARNESS_VERSION":
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)


def prepare_idea(path: Path, *, create: bool) -> Path:
    _check_destination(path)
    if path.exists():
        require_workspace(path, "idea")
        if not (path / "run.sh").is_file():
            raise ValueError(f"Incomplete idea workspace: {path}")
        return path
    if not create:
        raise ValueError(f"Idea workspace does not exist: {path}")
    path.mkdir(parents=True, mode=0o700, exist_ok=False)
    source = ROOT / "autovibeidea"
    # Explicit roots exclude examples, batch lists and output data.
    for name in ("tools", "skills", "venue-profiles", "docs"):
        _copy_resources(source / name, path / name)
    for name in ("run.sh", "CODEX_COMPAT.md", "README.md"):
        shutil.copy2(source / name, path / name)
    _mark(path, "idea")
    return path


def paper_slug(value: str) -> str:
    if not value or value in {".", ".."} or Path(value).name != value or "\\" in value:
        raise ValueError("--paper must be a single directory name")
    return value


def initialize_rebuttal(path: Path, slug: str) -> None:
    paper_slug(slug)
    _check_destination(path)
    path.mkdir(parents=True, mode=0o700, exist_ok=False)
    source = ROOT / "rebuttal"
    for name in ("harness", "rebuttal_verifier"):
        _copy_resources(source / name, path / name)
    # Only a blank config template is copied, never a configured .env.
    shutil.copy2(source / "rebuttal_verifier/.env.example", path / "rebuttal_verifier/.env.example")
    fixture = source / "examples/offline-demo"
    campaign = path / "campaigns" / slug
    campaign.mkdir(parents=True)
    shutil.copy2(fixture / "REBUTTAL_CARD.json", campaign / "REBUTTAL_CARD.json")
    paper = path / "papers" / slug
    shutil.copytree(fixture / "Tex", paper / "Tex")
    shutil.copy2(fixture / "review.md", paper / "review.md")
    result = subprocess.run([sys.executable, "-B", str(path / "harness/instantiate.py"),
        "--slug", slug, "--harness", str(path / "harness"), "--campaigns", str(path / "campaigns")],
        capture_output=True, text=True)
    if result.returncode:
        raise ValueError(result.stderr.strip() or "Could not render rebuttal contracts")
    _mark(path, "rebuttal", example_inputs=True, paper=slug)


def rebuttal_status(path: Path, paper: str | None = None) -> dict:
    require_workspace(path, "rebuttal")
    campaigns = path / "campaigns"
    names = [paper_slug(paper)] if paper else sorted(p.name for p in campaigns.iterdir() if p.is_dir())
    entries = []
    for name in names:
        campaign = campaigns / name
        if not (campaign / "REBUTTAL_CARD.json").is_file():
            raise ValueError(f"No campaign card for {name}")
        ledger = campaign / "ledger/loop_results.json"
        entries.append({"paper": name, "reviewer_results": read_json(ledger) if ledger.is_file() else None,
            "drafts": sorted(p.name for p in (campaign / "drafts").glob("*.md")),
            "ac_comment_exists": (campaign / "AC_COMMENT.md").is_file()})
    return {"workflow": "rebuttal", "workspace": str(path), "process_status": "not_tracked",
        "note": "Artifact snapshot only; missing results do not establish whether a process is running.",
        "campaigns": entries}
