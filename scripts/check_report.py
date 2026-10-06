#!/usr/bin/env python3
"""Verify the frozen v6 report and recompute its released aggregates; no models.

The manifest checks byte preservation, not the authenticity of research claims.
Recomputation verifies published aggregate arithmetic, not private campaigns.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = ROOT / "docs" / "technical-report" / "v6"


def verify_report(report_root: Path = REPORT_ROOT) -> dict:
    report_root = report_root.resolve()
    manifest = json.loads((report_root / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("format_version") != 1 or not manifest.get("files"):
        raise ValueError("unsupported or empty report manifest")
    for name, expected in manifest["files"].items():
        path = report_root / name
        if path.is_symlink() or not path.resolve().is_relative_to(report_root):
            raise ValueError(f"manifest entry escapes the report: {name}")
        data = path.read_bytes()
        if len(data) != expected["bytes"] or hashlib.sha256(data).hexdigest() != expected["sha256"]:
            raise ValueError(f"report integrity mismatch: {name}")

    # Keep the two report editions and all reusable result figures discoverable.
    required = {"reports/EAR_Technical_Report_EN.pdf", "reports/EAR_Technical_Report_CN.pdf",
                "data/protocol.json", "data/claims.csv", "data/derived_metrics.json", "scripts/recompute.py"}
    required.update(f"figures/{language}/{figure}.{suffix}"
                    for language in ("en", "cn")
                    for figure in ("inner_progress", "evolution_progress", "cost_comparison")
                    for suffix in ("svg", "png", "pdf"))
    if missing := required - manifest["files"].keys():
        raise ValueError(f"report assets missing from manifest: {', '.join(sorted(missing))}")

    completed = subprocess.run(
        [sys.executable, "-I", "-B", str(report_root / "scripts" / "recompute.py")],
        check=True, capture_output=True, text=True, timeout=30,
    )
    recomputed = json.loads(completed.stdout)
    packaged = json.loads((report_root / "data" / "derived_metrics.json").read_text(encoding="utf-8"))
    if recomputed != packaged:
        raise ValueError("recomputed metrics differ from data/derived_metrics.json")
    return {"verified_files": len(manifest["files"]), "metrics": recomputed}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-root", type=Path, default=REPORT_ROOT)
    args = parser.parse_args()
    try:
        result = verify_report(args.report_root)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    metrics = result["metrics"]
    population = metrics["population_totals"]
    rounds = metrics["inner_rounds"]
    print(f"PASS: {result['verified_files']} original files match the release manifest; recomputed metrics match exactly.")
    print(f"G0–G3: {population['episodes']} episodes, {population['research_invocations']} research invocations, "
          f"{population['written_manuscripts']} written manuscripts, "
          f"{population['selected_best_assessor_passes']} selected-best historical assessor passes.")
    print(f"Fixed manuscript cohort: current-version passes {rounds[0]['current_passes']} → "
          f"{rounds[-1]['current_passes']}; historical protocol, not the portable terminal gate.")
    print("Aggregate arithmetic verified. No model calls; active human time was not measured.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
