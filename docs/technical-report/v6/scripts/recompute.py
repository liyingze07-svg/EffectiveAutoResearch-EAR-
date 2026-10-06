#!/usr/bin/env python3
"""Recompute report tables from released aggregates, without private artifacts.

Default: print JSON to stdout. --output writes that JSON to a requested path.
Assessor F1 values are reported aggregate inputs, not reestimated predictions.
"""
import argparse
import csv
import json
from pathlib import Path


PUBLIC_ROOT = Path(__file__).resolve().parents[1]


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def safe_ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def recompute(data_dir):
    protocol = json.loads((data_dir / "protocol.json").read_text(encoding="utf-8"))
    rounds = []
    for row in read_csv(data_dir / "round_aggregates.csv"):
        n = int(row["manuscripts"])
        rounds.append({
            "round": int(row["round"]), "manuscripts": n,
            "current_passes": int(row["current_passes"]),
            "current_pass_rate": int(row["current_passes"]) / n,
            "current_mean_score": float(row["current_score_sum"]) / n,
            "selected_best_passes_at_cutoff": int(row["selected_best_passes_at_cutoff"]),
            "selected_best_mean_score_at_cutoff": float(row["selected_best_score_sum_at_cutoff"]) / n,
        })
    assert [r["round"] for r in rounds] == [0, 1, 2, 3]
    assert all(r["manuscripts"] == protocol["math_cohort"]["written_manuscripts"] for r in rounds)

    generations = []
    for row in read_csv(data_dir / "generation_population.csv"):
        r = {key: int(value) for key, value in row.items()}
        r["population_pass_rate"] = r["selected_best_assessor_passes"] / r["episodes"]
        generations.append(r)
    assert [g["generation"] for g in generations] == protocol["math_cohort"]["generations"]
    totals = {key: sum(g[key] for g in generations) for key in
              ["episodes", "research_invocations", "written_manuscripts", "selected_best_assessor_passes"]}
    totals["population_pass_rate"] = totals["selected_best_assessor_passes"] / totals["episodes"]
    totals["written_conditional_pass_rate"] = totals["selected_best_assessor_passes"] / totals["written_manuscripts"]
    totals["research_invocations_per_pass"] = totals["research_invocations"] / totals["selected_best_assessor_passes"]
    assert all(totals[k] == protocol["math_cohort"][k] for k in
               ["episodes", "research_invocations", "written_manuscripts", "selected_best_assessor_passes"])
    assert rounds[-1]["selected_best_passes_at_cutoff"] == totals["selected_best_assessor_passes"]

    comparisons = []
    for row in read_csv(data_dir / "generation_comparison.csv"):
        r = {key: (value if key == "role" else float(value) if key == "mean_historical_fitness" else int(value))
             for key, value in row.items()}
        assert r["episodes"] == 4
        r["pass_rate"] = r["selected_best_assessor_passes"] / r["episodes"]
        r["research_invocations_per_pass"] = safe_ratio(r["research_invocations"], r["selected_best_assessor_passes"])
        comparisons.append(r)
    assert len(comparisons) == 2 * len(generations)

    cost_fields = ["episodes", "selected_best_assessor_passes", "research_invocations",
                   "reviewer_requests", "review_roll_invocations", "refinement_attempts_reconstructed"]
    costs = []
    for row in read_csv(data_dir / "selected_cost.csv"):
        r = {"generation": int(row["generation"]), "role": row["role"]}
        r.update({key: int(row[key]) for key in cost_fields})
        assert r["review_roll_invocations"] == 3 * r["reviewer_requests"]
        comparison = next(c for c in comparisons if c["generation"] == r["generation"] and c["role"] == r["role"])
        assert r["research_invocations"] == comparison["research_invocations"]
        assert r["selected_best_assessor_passes"] == comparison["selected_best_assessor_passes"]
        costs.append(r)
    for role in ["baseline", "selected"]:
        subset = [r for r in costs if r["role"] == role]
        if len(subset) < 2:
            continue
        r = {"generation": "pooled", "role": role}
        r.update({key: sum(x[key] for x in subset) for key in cost_fields})
        costs.append(r)
    for r in costs:
        r["outer_invocation_proxy"] = r["research_invocations"] + r["review_roll_invocations"] + r["refinement_attempts_reconstructed"]
        r["research_invocations_per_pass"] = safe_ratio(r["research_invocations"], r["selected_best_assessor_passes"])
        r["outer_proxy_per_pass"] = safe_ratio(r["outer_invocation_proxy"], r["selected_best_assessor_passes"])

    reductions = []
    for generation in dict.fromkeys(r["generation"] for r in costs):
        base = next(r for r in costs if r["generation"] == generation and r["role"] == "baseline")
        selected = next(r for r in costs if r["generation"] == generation and r["role"] == "selected")
        r = {"generation": generation}
        for metric in ["research_invocations_per_pass", "outer_proxy_per_pass"]:
            r[metric + "_reduction_percent"] = (100 * (1 - selected[metric] / base[metric])
                                                if base[metric] is not None and selected[metric] is not None else None)
        reductions.append(r)

    evaluator = []
    for row in read_csv(data_dir / "rebuttal_evaluator.csv"):
        row["source_cohort_n"] = int(row["source_cohort_n"])
        row["reported_value"] = float(row["reported_value"])
        evaluator.append(row)
    assert len(evaluator) == 3
    assert [r["source_cohort_n"] for r in evaluator] == [36, 57, 57]
    strict = protocol["historical_assessment"]["retained_vote_sensitivity"]
    return {
        "basis": "Released aggregate counts and score sums; evaluator F1 values are reported aggregate inputs.",
        "active_human_time_measured": protocol["objective"]["active_human_time_measured"],
        "reporting_window": protocol["reporting_window"],
        "population_totals": totals,
        "inner_rounds": rounds,
        "inner_last_minus_initial_mean": rounds[-1]["current_mean_score"] - rounds[0]["current_mean_score"],
        "inner_individual_summary": {
            "final_vs_initial": protocol["math_cohort"]["final_vs_initial_score"],
            "last_round_below_own_best_score": protocol["math_cohort"]["last_round_below_own_best_score"],
            "selected_best_pass_but_last_round_not_pass": protocol["math_cohort"]["selected_best_pass_but_last_round_not_pass"],
        },
        "generation_population": generations,
        "generation_comparison": comparisons,
        "selected_cost": costs,
        "observed_cost_reductions": reductions,
        "strict_retained_vote_diagnostic": strict,
        "rebuttal_evaluator_reported": evaluator,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=PUBLIC_ROOT / "data")
    parser.add_argument("--output", type=Path, help="Optional JSON output; default is stdout only.")
    args = parser.parse_args()
    text = json.dumps(recompute(args.data_dir), ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"Wrote {args.output.name}")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
