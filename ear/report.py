"""Recompute the released report aggregates without model calls."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def show_report(as_json: bool = False) -> int:
    bundle = ROOT / "docs/technical-report/v6"
    spec = importlib.util.spec_from_file_location("ear_report_check", ROOT / "scripts/check_report.py")
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    verified = checker.verify_report(bundle)
    metrics = verified["metrics"]
    if as_json:
        print(json.dumps(metrics, ensure_ascii=False, indent=2))
        return 0
    first, last = metrics["inner_rounds"][0], metrics["inner_rounds"][-1]
    generation = next(r for r in metrics["observed_cost_reductions"] if r["generation"] == 3)
    comparison = {r["role"]: r for r in metrics["generation_comparison"] if r["generation"] == 3}
    baseline = comparison["baseline"]["research_invocations_per_pass"]
    selected = comparison["selected"]["research_invocations_per_pass"]
    reduction = generation["research_invocations_per_pass_reduction_percent"]
    print("EAR technical report v6 — reproduced aggregate results")
    print(f"Revision cohort: {last['manuscripts']} completed manuscripts; current-version historical")
    print(f"  assessor passes: {first['current_passes']} -> {last['current_passes']} (initial -> final round).")
    print(f"G3 selected strategy: {baseline:.2f} -> {selected:.2f} research invocations per pass")
    print(f"  ({reduction:.1f}% reduction; 4 episodes per batch).")
    print(f"PASS: {verified['verified_files']} original files match the manifest; recomputed metrics match exactly.")
    print("Historical model assessment; research invocations are a partial cost measure.")
    print("Human time was not measured. This reproduces aggregates, not model runs.")
    print(f"Reports, figures and protocol: {bundle}")
    return 0
