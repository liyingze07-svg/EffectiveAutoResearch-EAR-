#!/usr/bin/env python3
"""Scan the whole EAR worktree or staged blobs, without printing matched contents.

Heuristic protection, not a proof that a repository is free of secrets.
Exit status: 0 clean, 1 matches, 2 incomplete/failed scan.
"""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys

RULES = [
    ("OpenRouter key", r"sk-or-v1-[A-Za-z0-9_-]{20,}"),
    ("provider key", r"sk-(?:ant|proj|live)-[A-Za-z0-9_-]{20,}"),
    ("long sk key", r"sk-[A-Za-z0-9]{32,}"),
    ("HuggingFace token", r"hf_[A-Za-z0-9]{30,}"),
    ("GitHub token", r"gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}"),
    ("private key", r"-----BEGIN (?:RSA |OPENSSH |EC |DSA |ENCRYPTED )?PRIVATE KEY-----"),
    ("Bearer token", r"Bearer [A-Za-z0-9._-]{24,}"),
    ("plaintext password", r'''(?i)\b(?:password|passwd)\s*[:=]\s*["']?([^\s"';,]{6,})'''),
    ("sshpass password", r'''sshpass\s+-p\s*["']?([^\s"']+)'''),
]


def placeholder(value):
    # Exempt only the matched value, never an entire line containing "example".
    value = value.strip("\"'")
    if value.startswith(("$", "<")):
        return True
    if value.lower() in ("redacted", "placeholder", "your_key", "your-key", "your_password"):
        return True
    tail = re.sub(r"^(?:sk-or-v1-|sk-(?:ant|proj|live)-|sk-|hf_|gh[pousr]_|Bearer )", "", value)
    return bool(re.fullmatch(r"[xX]+", tail))


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.PIPE)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--staged", action="store_true")
    args = ap.parse_args()
    try:
        root = Path(os.fsdecode(git(Path(__file__).resolve().parent, "rev-parse", "--show-toplevel")).strip())
        command = ("diff", "--cached", "--name-only", "--diff-filter=ACMRT", "-z") if args.staged else (
            "ls-files", "--cached", "--others", "--exclude-standard", "-z")
        paths = sorted(set(p for p in git(root, *command).split(b"\0") if p))
        hits = scanned = 0
        for raw in paths:
            name = os.fsdecode(raw)
            path = root / name
            if args.staged:
                data = git(root, "show", f":{name}")
            else:
                if path.is_symlink() or not path.exists() or not path.is_file():
                    continue
                data = path.read_bytes()
            if b"\0" in data:
                continue
            scanned += 1
            for number, line in enumerate(data.decode("utf-8", errors="replace").splitlines(), 1):
                for label, pattern in RULES:
                    for match in re.finditer(pattern, line):
                        value = match.group(1) if match.lastindex else match.group()
                        if not placeholder(value):
                            print(f"HIT {label}: {name!r}:{number} [content redacted]")
                            hits += 1
                            break
        print(f"{'FAIL' if hits else 'Clean'}: {hits} hits; scanned {scanned} {'staged blobs' if args.staged else 'worktree files'}")
        return 1 if hits else 0
    except (OSError, subprocess.CalledProcessError):
        print("Scan failed or incomplete; do not treat this as a clean result.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
