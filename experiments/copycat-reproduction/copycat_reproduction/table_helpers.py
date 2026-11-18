"""Copycat-reproduction comparison logic."""

from __future__ import annotations

from collections.abc import Mapping
from math import sqrt
from statistics import fmean
from typing import Any

import pandas as pd
from cattykit.experiments import (
    chi_square_survival_function,
    mean_absolute_error,
    total_variation_distance,
    two_sided_p_value,
    z_statistic,
)


def comparison_table(
    observed: dict[str, Any], original: dict[str, Any]
) -> pd.DataFrame:
    """Compute per-problem answer, temperature, and codelet comparison measures."""
    original_cases = {case["problem"]: case for case in original["results"]}
    rows = []
    for observed_case in observed["results"]:
        gold_case = original_cases[observed_case["problem"]]
        gold_results = gold_case["solutions"]
        observed_results = observed_case["solutions"]
        shared_results = [
            (observed_results[solution], gold_result)
            for solution, gold_result in gold_results.items()
            if solution in observed_results
        ]
        temperature_z_scores = [
            z_statistic(
                observed_mean=observed_result["temperature_mean"],
                expected_mean=gold_result["temperature_mean"],
                observed_standard_error=observed_result["temperature_standard_error"],
                expected_standard_error=gold_result["temperature_standard_error"],
            )
            for observed_result, gold_result in shared_results
            if observed_result["frequency"] >= 2 and gold_result["frequency"] >= 2
            # Singletons cannot provide an estimated standard error
        ]
        temperature_absolute_errors = [
            abs(observed_result["temperature_mean"] - gold_result["temperature_mean"])
            for observed_result, gold_result in shared_results
        ]
        comparable_run_count = sum(
            gold_result["frequency"] for _, gold_result in shared_results
        )
        weighted_temperature_absolute_error = (
            fmean(
                temperature_absolute_errors,
                weights=(gold_result["frequency"] for _, gold_result in shared_results),
            )
            if comparable_run_count
            else float("nan")
        )
        gold_only_solutions = gold_results.keys() - observed_results.keys()
        observed_only_solutions = observed_results.keys() - gold_results.keys()
        codelets_z = z_statistic(
            observed_mean=observed_case["codelets"]["mean"],
            expected_mean=gold_case["codelets"]["mean"],
            observed_standard_error=observed_case["codelets"]["standard_error"],
            expected_standard_error=gold_case["codelets"]["standard_error"],
        )
        rows.append(
            {
                "id": gold_case["id"],
                "problem": observed_case["problem"],
                "solution_total_variation_distance": total_variation_distance(
                    {
                        key: value["frequency"]
                        for key, value in observed_results.items()
                    },
                    {key: value["frequency"] for key, value in gold_results.items()},
                ),
                "temperature_mean_absolute_error": mean_absolute_error(
                    (
                        observed_result["temperature_mean"]
                        for observed_result, _ in shared_results
                    ),
                    (
                        gold_result["temperature_mean"]
                        for _, gold_result in shared_results
                    ),
                )
                if shared_results
                else float("nan"),
                "temperature_run_frequency_weighted_mean_absolute_error": (
                    weighted_temperature_absolute_error
                ),
                "temperature_max_absolute_error": max(
                    temperature_absolute_errors, default=float("nan")
                ),
                "temperature_z_chi_square": sum(
                    score**2 for score in temperature_z_scores
                ),
                "temperature_z_count": len(temperature_z_scores),
                "temperature_z_singleton_excluded_count": (
                    len(shared_results) - len(temperature_z_scores)
                ),
                "temperature_max_absolute_z_stat": max(
                    (abs(score) for score in temperature_z_scores), default=0.0
                ),
                # total distinct answers in both gold and observed
                "shared_solution_count": len(shared_results),
                # total runs for those comparable answers in the gold data
                "shared_gold_run_count": comparable_run_count,
                "gold_only_solution_count": len(gold_only_solutions),
                "gold_only_run_count": sum(
                    gold_results[solution]["frequency"]
                    for solution in gold_only_solutions
                ),
                "observed_only_solution_count": len(observed_only_solutions),
                "observed_only_run_count": sum(
                    observed_results[solution]["frequency"]
                    for solution in observed_only_solutions
                ),
                "codelets_relative_error": (
                    abs(
                        observed_case["codelets"]["mean"]
                        - gold_case["codelets"]["mean"]
                    )
                    / abs(gold_case["codelets"]["mean"])
                    if gold_case["codelets"]["mean"]
                    else 0.0
                ),
                "codelets_z_stat": codelets_z,
                "codelets_z_p_value": two_sided_p_value(codelets_z),
            }
        )
    return pd.DataFrame(rows).sort_values(
        "id", key=lambda values: values.map(_id_sort_key)
    )


def _id_sort_key(problem_id: str) -> tuple[int, ...]:
    return tuple(int(part) for part in problem_id.split("."))


def comparison_markdown(comparison: pd.DataFrame) -> str:
    """Render a concise paper-facing baseline summary table."""
    temperature_count = int(comparison["temperature_z_count"].sum())
    temperature_chi_square = float(comparison["temperature_z_chi_square"].sum())
    codelet_chi_square = float((comparison["codelets_z_stat"] ** 2).sum())
    table = pd.DataFrame(
        [
            (
                "Mean answer TV distance",
                comparison["solution_total_variation_distance"].mean(),
            ),
            (
                "Max answer TV distance",
                comparison["solution_total_variation_distance"].max(),
            ),
            (
                "Mean runs with observed-only answers",
                comparison["observed_only_run_count"].mean(),
            ),
            (
                "Temperature unweighted mean absolute error",
                comparison["temperature_mean_absolute_error"].mean(),
            ),
            (
                "Temperature weighted mean absolute error",
                comparison["temperature_run_frequency_weighted_mean_absolute_error"].mean(),
            ),
            (
                "Temperature max absolute error",
                comparison["temperature_max_absolute_error"].max(),
            ),
            (
                "Temperature RMS z",
                sqrt(temperature_chi_square / temperature_count)
                if temperature_count
                else 0.0,
            ),
            (
                r"Temperature max \|z\|",
                comparison["temperature_max_absolute_z_stat"].max(),
            ),
            (
                "Codelets-run mean relative error",
                comparison["codelets_relative_error"].mean(),
            ),
            (
                "Codelets-run max relative error",
                comparison["codelets_relative_error"].max(),
            ),
            ("Codelets-run RMS z", sqrt(codelet_chi_square / len(comparison))),
        ],
        columns=["Measure", "Value"],
    )
    table["Value"] = table["Value"].map(
        lambda value: value if isinstance(value, str) else f"{float(value):.3f}"
    )
    return (
        table.to_markdown(
            index=False,
            disable_numparse=True,
            colalign=("left", "right"),
        )
        + "\n"
    )


def method_summary_row(
    method: str,
    comparison: pd.DataFrame,
    raw_runs: pd.DataFrame,
    snaggable_problems: set[str],
) -> dict[str, Any]:
    """Build one row of the three-method comparison table."""
    if "snag_count" not in raw_runs.columns:
        raise ValueError("Raw results must include snag_count for method summaries.")
    snaggable_runs = raw_runs.loc[raw_runs["problem"].isin(snaggable_problems)]
    if snaggable_runs.empty:
        raise ValueError("Raw results contain no runs for the snaggable problem set.")
    temperature_count = int(comparison["temperature_z_count"].sum())
    temperature_chi_square = float(comparison["temperature_z_chi_square"].sum())
    codelets_chi_square = float((comparison["codelets_z_stat"] ** 2).sum())
    return {
        "method": method,
        "answer_tv_distance_mean": comparison[
            "solution_total_variation_distance"
        ].mean(),
        "answer_tv_distance_max": comparison["solution_total_variation_distance"].max(),
        "temperature_mean_absolute_error": comparison[
            "temperature_mean_absolute_error"
        ].mean(),
        "temperature_run_frequency_weighted_mean_absolute_error": comparison[
            "temperature_run_frequency_weighted_mean_absolute_error"
        ].mean(),
        "temperature_max_absolute_error": comparison[
            "temperature_max_absolute_error"
        ].max(),
        "temperature_rms_z_stat": sqrt(temperature_chi_square / temperature_count)
        if temperature_count
        else 0.0,
        "temperature_max_absolute_z_stat": comparison[
            "temperature_max_absolute_z_stat"
        ].max(),
        "temperature_z_chi_square": temperature_chi_square,
        "temperature_z_p_value": chi_square_survival_function(
            temperature_chi_square, temperature_count
        ),
        "mean_observed_only_answer_run_count": comparison[
            "observed_only_run_count"
        ].mean(),
        "codelets_run_mean_relative_error": comparison[
            "codelets_relative_error"
        ].mean(),
        "codelets_run_max_relative_error": comparison["codelets_relative_error"].max(),
        "codelets_run_rms_z_stat": sqrt(codelets_chi_square / len(comparison)),
        "codelets_run_z_chi_square": codelets_chi_square,
        "codelets_run_z_p_value": chi_square_survival_function(
            codelets_chi_square, len(comparison)
        ),
        "mean_snag_count_on_snaggable_problems": round(
            snaggable_runs["snag_count"].sum() / len(snaggable_runs), 3
        ),
        "max_snag_count": int(raw_runs["snag_count"].max()),
    }


def method_comparison_markdown(
    summary: pd.DataFrame, method_labels: Mapping[str, str]
) -> str:
    """Render method columns using the same measures as the baseline table."""
    measures = (
        ("Mean answer TV distance", "answer_tv_distance_mean"),
        ("Max answer TV distance", "answer_tv_distance_max"),
        (
            "Mean runs with observed-only answers",
            "mean_observed_only_answer_run_count",
        ),
        (
            "Temperature unweighted mean absolute error",
            "temperature_mean_absolute_error",
        ),
        (
            "Temperature weighted mean absolute error",
            "temperature_run_frequency_weighted_mean_absolute_error",
        ),
        ("Temperature max absolute error", "temperature_max_absolute_error"),
        ("Temperature RMS z", "temperature_rms_z_stat"),
        (r"Temperature max \|z\|", "temperature_max_absolute_z_stat"),
        ("Codelets-run mean relative error", "codelets_run_mean_relative_error"),
        ("Codelets-run max relative error", "codelets_run_max_relative_error"),
        ("Codelets-run RMS z", "codelets_run_rms_z_stat"),
        (
            "Mean snag count on snaggable problems",
            "mean_snag_count_on_snaggable_problems",
        ),
        ("Max snag count", "max_snag_count"),
    )
    table = pd.DataFrame(
        {
            "Measure": [label for label, _ in measures],
            **{
                method_labels[row.method]: [
                    _format_method_summary_value(field, getattr(row, field))
                    for _, field in measures
                ]
                for row in summary.itertuples(index=False)
            },
        }
    )
    return (
        table.to_markdown(
            index=False,
            disable_numparse=True,
            colalign=("left", *("right" for _ in method_labels)),
        )
        + "\n"
    )


def _format_method_summary_value(field: str, value: object) -> str:
    """Apply metric-specific display precision to a method-summary value."""
    if field == "mean_snag_count_on_snaggable_problems":
        return f"{float(value):.3f}"
    if field == "max_snag_count":
        return str(int(value))
    return f"{float(value):.3f}"
