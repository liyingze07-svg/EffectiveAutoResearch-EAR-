#!/usr/bin/env python3
"""Check portable source and optional private exclusion terms without printing matches.

Private deny lists stay outside the checkout. This complements secret_scan.py;
it does not inspect or publish ignored runtime research outputs.
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
from pathlib import Path
import re
import subprocess


# Published release from e287d39; its 48 members match the unpacked v6 report.
# Pin the exact archive, not an extension: other ZIP files remain disallowed.
RELEASE_ARCHIVES = {
    "docs/technical-report/EAR_Technical_Report_v6_Bilingual_Public.zip":
        "e4244a835f96eeab507d563d387803c1a2f5cc22e9f9b5639c31d9bebe8dd31c",
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--scope", default=".", help="source subtree to audit (default: entire checkout)")
    ap.add_argument("--denylist", type=Path, help="private newline-separated exclusion terms, outside the checkout")
    args = ap.parse_args()
    root = args.root.resolve()
    terms = []
    if args.denylist:
        if args.denylist.resolve().is_relative_to(root):
            ap.error("keep the private deny list outside the repository")
        terms = [re.sub(r"[\W_]+", "", x).casefold() for x in args.denylist.read_text().splitlines() if x.strip()]
    raw = subprocess.check_output(["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", args.scope])
    failures = scanned = 0
    for name in sorted(set(x.decode() for x in raw.split(b"\0") if x)):
        p = root / name
        normalized_name = re.sub(r"[\W_]+", "", name).casefold()
        if any(t and t in normalized_name for t in terms):
            print(f"HIT private exclusion in source filename: {name} [content redacted]")
            failures += 1
        if not p.is_file() or p.is_symlink():
            continue
        data = p.read_bytes()
        if name in RELEASE_ARCHIVES:
            if hashlib.sha256(data).hexdigest() != RELEASE_ARCHIVES[name]:
                print(f"HIT release archive checksum mismatch: {name} [content redacted]")
                failures += 1
            continue
        if b"\0" in data:
            if p.suffix not in {".png", ".jpg", ".jpeg", ".pdf"}:
                print(f"HIT binary runtime material: {name} [content redacted]")
                failures += 1
            continue
        scanned += 1
        for number, line in enumerate(data.decode("utf-8", errors="replace").splitlines(), 1):
            normalized = re.sub(r"[\W_]+", "", line).casefold()
            kinds = []
            if any(t and t in normalized for t in terms):
                kinds.append("private exclusion")
            if re.search(r"/(?:home|Users)/(?!<|\{|example\b)[A-Za-z0-9_.-]+/", line):
                kinds.append("machine-specific home path")
            for address in re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", line):
                try:
                    ip = ipaddress.ip_address(address)
                except ValueError:
                    continue
                if not ip.is_loopback and not ip.is_unspecified and not address.startswith(("192.0.2.", "198.51.100.", "203.0.113.")):
                    kinds.append("machine address")
            for kind in set(kinds):
                print(f"HIT {kind}: {name}:{number} [content redacted]")
                failures += 1
    print(f"{'FAIL' if failures else 'Clean'}: {failures} findings; scanned {scanned} public source files")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
