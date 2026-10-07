"""Copycat-reproduction comparison logic, separate from Cattykit itself."""

from __future__ import annotations

from collections.abc import Mapping
from math import sqrt
from typing import Any

import pandas as pd
from cattykit.experiments import (
    chi_square_survival_function,
    mean_absolute_error,
    total_variation_distance,
    two_sided_p_value,
    z_statistic,
)

MIN_ORIGINAL_SOLUTION_FREQUENCY = 10


def comparison_row(
    *,
    problem: str,
    solution: str,
    observed: pd.Series | None,
    expected: pd.Series | dict[str, object] | None,
    tv_distance: float | None = None,
    codelets_z_stat: float | None = None,
    temperature_z_stat: float | None = None,
) -> dict[str, object]:
    """Build one Copycat observed-versus-published comparison row."""
    row: dict[str, object] = {
        "problem": problem,
        "solution": solution,
        "tv_distance": tv_distance,
        "codelets_z_stat": codelets_z_stat,
        "temperature_z_stat": temperature_z_stat,
    }
    for field in (
        "frequency",
        "mean_codelets_run",
        "codelets_standard_error",
        "mean_temperature",
        "temperature_standard_error",
    ):
        actual = (
            None
            if observed is None or pd.isna(observed.get(field))
            else observed.get(field)
        )
        reference = (
            None
            if expected is None or pd.isna(expected.get(field))
            else expected.get(field)
        )
        row[f"observed_{field}"] = actual
        row[f"expected_{field}"] = reference
        row[f"{field}_difference"] = (
            actual - reference if actual is not None and reference is not None else None
        )
    actual_codelets = row["observed_mean_codelets_run"]
    expected_codelets = row["expected_mean_codelets_run"]
    row["codelets_relative_error_magnitude"] = (
        abs(actual_codelets - expected_codelets) / expected_codelets
        if actual_codelets is not None and expected_codelets not in (None, 0)
        else None
    )
    return row


def reproduction_summary(comparison: pd.DataFrame) -> dict[str, Any]:
    """Summarize the Copycat-specific reproduction comparison table."""
    totals = comparison[comparison["solution"] == "Total"]
    errors = totals["codelets_relative_error_magnitude"].dropna()
    return {
        "mean_total_variation_distance": totals["tv_distance"].mean(),
        "max_total_variation_distance": totals["tv_distance"].max(),
        "mean_codelets_relative_error_magnitude": errors.mean(),
        "max_codelets_relative_error_magnitude": errors.max(),
        "codelets_relative_error_magnitude_quantiles": {
            percentile: errors.quantile(percentile / 100)
            for percentile in range(10, 101, 10)
        },
    }


def comparison_table(
    reproduction: dict[str, Any], original: dict[str, Any]
) -> pd.DataFrame:
    """Compute per-problem answer, temperature, and codelet comparison measures."""
    original_cases = {case["problem"]: case for case in original["results"]}
    rows = []
    for reproduced in reproduction["results"]:
        gold = original_cases[reproduced["problem"]]
        observed_solutions = reproduced["solutions"]
        retained = [
            (observed_solutions[solution], expected)
            for solution, expected in gold["solutions"].items()
            if solution in observed_solutions
            and expected["frequency"] >= MIN_ORIGINAL_SOLUTION_FREQUENCY
        ]
        temperature_z_scores = [
            z_statistic(
                observed_mean=observed["temperature_mean"],
                expected_mean=expected["temperature_mean"],
                observed_standard_error=observed["temperature_standard_error"],
                expected_standard_error=expected["temperature_standard_error"],
            )
            for observed, expected in retained
        ]
        temperature_absolute_errors = [
            abs(observed["temperature_mean"] - expected["temperature_mean"])
            for observed, expected in retained
        ]
        codelets_z = z_statistic(
            observed_mean=reproduced["codelets"]["mean"],
            expected_mean=gold["codelets"]["mean"],
            observed_standard_error=reproduced["codelets"]["standard_error"],
            expected_standard_error=gold["codelets"]["standard_error"],
        )
        rows.append(
            {
                "id": gold["id"],
                "problem": reproduced["problem"],
                "solution_total_variation_distance": total_variation_distance(
                    {
                        key: value["frequency"]
                        for key, value in observed_solutions.items()
                    },
                    {
                        key: value["frequency"]
                        for key, value in gold["solutions"].items()
                    },
                ),
                "temperature_mean_absolute_error": mean_absolute_error(
                    (observed["temperature_mean"] for observed, _ in retained),
                    (expected["temperature_mean"] for _, expected in retained),
                ),
                "temperature_max_absolute_error": max(
                    temperature_absolute_errors, default=0.0
                ),
                "temperature_z_chi_square": sum(
                    score**2 for score in temperature_z_scores
                ),
                "temperature_z_count": len(temperature_z_scores),
                "temperature_max_absolute_z_stat": max(
                    (abs(score) for score in temperature_z_scores), default=0.0
                ),
                "codelets_relative_error": (
                    abs(reproduced["codelets"]["mean"] - gold["codelets"]["mean"])
                    / abs(gold["codelets"]["mean"])
                    if gold["codelets"]["mean"]
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


def error_summary(comparison: pd.DataFrame) -> pd.DataFrame:
    """Summarize the scale-appropriate errors across all 29 problems."""
    metrics = {
        "Answer TV distance": comparison["solution_total_variation_distance"],
        "Temperature mean absolute error": comparison[
            "temperature_mean_absolute_error"
        ],
        "Temperature max absolute error": comparison[
            "temperature_max_absolute_error"
        ],
        "Codelets-run relative error": comparison["codelets_relative_error"],
    }
    return pd.DataFrame(
        {
            "error_metric": name,
            "mean_error": values.mean(),
            "max_error": values.max(),
        }
        for name, values in metrics.items()
    )


def comparison_markdown(comparison: pd.DataFrame, error: pd.DataFrame) -> str:
    """Render a concise paper-facing baseline summary table."""
    errors = error.set_index("error_metric")
    temperature_count = int(comparison["temperature_z_count"].sum())
    temperature_chi_square = float(comparison["temperature_z_chi_square"].sum())
    codelet_chi_square = float((comparison["codelets_z_stat"] ** 2).sum())
    table = pd.DataFrame(
        [
            (
                "Answer TV distance",
                comparison["solution_total_variation_distance"].mean(),
            ),
            (
                "Temperature mean absolute error",
                errors.loc["Temperature mean absolute error", "mean_error"],
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
                "Codelets-run relative error",
                errors.loc["Codelets-run relative error", "mean_error"],
            ),
            ("Codelets-run RMS z", sqrt(codelet_chi_square / len(comparison))),
        ],
        columns=["Measure", "Value"],
    )
    return (
        "# Comparison statistics\n\n"
        + table.to_markdown(index=False, floatfmt=".3f")
        + "\n"
    )


def method_summary_row(method: str, comparison: pd.DataFrame) -> dict[str, Any]:
    """Build one row of the three-method comparison table."""
    temperature_count = int(comparison["temperature_z_count"].sum())
    temperature_chi_square = float(comparison["temperature_z_chi_square"].sum())
    codelets_chi_square = float((comparison["codelets_z_stat"] ** 2).sum())
    return {
        "method": method,
        "answer_tv_distance_mean": comparison[
            "solution_total_variation_distance"
        ].mean(),
        "temperature_mean_absolute_error": comparison[
            "temperature_mean_absolute_error"
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
        "codelets_run_relative_error": comparison["codelets_relative_error"].mean(),
        "codelets_run_rms_z_stat": sqrt(codelets_chi_square / len(comparison)),
        "codelets_run_z_chi_square": codelets_chi_square,
        "codelets_run_z_p_value": chi_square_survival_function(
            codelets_chi_square, len(comparison)
        ),
    }


def method_comparison_markdown(
    title: str, summary: pd.DataFrame, method_labels: Mapping[str, str]
) -> str:
    """Render method columns using the same measures as the baseline table."""
    measures = (
        ("Answer TV distance", "answer_tv_distance_mean"),
        ("Temperature mean absolute error", "temperature_mean_absolute_error"),
        ("Temperature max absolute error", "temperature_max_absolute_error"),
        ("Temperature RMS z", "temperature_rms_z_stat"),
        (r"Temperature max \|z\|", "temperature_max_absolute_z_stat"),
        ("Codelets-run relative error", "codelets_run_relative_error"),
        ("Codelets-run RMS z", "codelets_run_rms_z_stat"),
    )
    table = pd.DataFrame(
        {
            "Measure": [label for label, _ in measures],
            **{
                method_labels[row.method]: [
                    getattr(row, field) for _, field in measures
                ]
                for row in summary.itertuples(index=False)
            },
        }
    )
    return f"# {title}\n\n" + table.to_markdown(index=False, floatfmt=".3f") + "\n"
