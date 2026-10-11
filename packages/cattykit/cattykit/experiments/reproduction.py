"""Comparison of repeated model runs with reference behaviour."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .runner import run_experiment
from .statistics import total_variation_distance, z_statistic


def run_reproduction(
    model_name: str,
    gold_behaviour: dict[str, pd.DataFrame | list[dict[str, Any]]],
    iterations: int,
    output_file: str | Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Run a model and compare its standard summaries with reference behaviour.

    ``gold_behaviour`` maps each problem to rows using the schema returned by
    :func:`summarize_runs`, excluding its ``problem`` column.  The comparison
    contains one row for each reference answer and each problem's ``Total``
    row.  This makes the routine suitable for any Cattykit model that records
    the standard answer, temperature, and codelet-count measurements.
    """
    observed = run_experiment(
        model_name, list(gold_behaviour), iterations, verbose=False
    ).summary
    rows: list[dict[str, object]] = []
    for problem, behaviour in gold_behaviour.items():
        expected = _as_dataframe(behaviour)
        actual = observed.loc[observed["problem"] == problem]
        actual_answers = actual.loc[actual["solution"] != "Total"]
        expected_answers = expected.loc[expected["solution"] != "Total"]
        rows.append(
            _comparison_row(
                problem=problem,
                solution="Total",
                observed=_total_row(actual, problem, "observed"),
                expected=_total_row(expected, problem, "reference"),
                tv_distance=total_variation_distance(
                    dict(
                        zip(
                            actual_answers["solution"],
                            actual_answers["frequency"],
                            strict=True,
                        )
                    ),
                    dict(
                        zip(
                            expected_answers["solution"],
                            expected_answers["frequency"],
                            strict=True,
                        )
                    ),
                ),
                codelets_z_stat=_z_statistic(
                    _total_row(actual, problem, "observed"),
                    _total_row(expected, problem, "reference"),
                    "mean_codelets_run",
                    "codelets_standard_error",
                ),
            )
        )
        for expected_answer in expected_answers.itertuples(index=False):
            matches = actual_answers.loc[
                actual_answers["solution"] == expected_answer.solution
            ]
            actual_answer = None if matches.empty else matches.iloc[0]
            rows.append(
                _comparison_row(
                    problem=problem,
                    solution=str(expected_answer.solution),
                    observed=actual_answer,
                    expected=expected_answer._asdict(),
                    temperature_z_stat=(
                        None
                        if actual_answer is None
                        else _z_statistic(
                            actual_answer,
                            expected_answer._asdict(),
                            "mean_temperature",
                            "temperature_standard_error",
                        )
                    ),
                )
            )
    comparison = pd.DataFrame(rows)
    if output_file is not None:
        comparison.to_csv(output_file, index=False)
    return comparison, reproduction_summary(comparison)


def reproduction_summary(comparison: pd.DataFrame) -> dict[str, Any]:
    """Summarize the generic error measures in a reproduction comparison.

    Temperature errors are weighted by the reference answer frequency.  The
    maximum temperature metric is the maximum of the frequency-weighted mean
    errors for each problem, rather than the error of a single answer.
    """
    totals = comparison.loc[comparison["solution"] == "Total"]
    answer_rows = comparison.loc[comparison["solution"] != "Total"]
    temperature_rows = answer_rows.loc[
        answer_rows["mean_temperature_difference"].notna()
        & answer_rows["expected_frequency"].notna()
    ].copy()
    temperature_rows["absolute_temperature_error"] = temperature_rows[
        "mean_temperature_difference"
    ].abs()
    temperature_mean_error = _frequency_weighted_mean(temperature_rows)
    problem_temperature_mean_errors = {
        problem: _frequency_weighted_mean(rows)
        for problem, rows in temperature_rows.groupby("problem", sort=False)
    }
    codelets_errors = totals["codelets_relative_error_magnitude"].dropna()
    return {
        "mean_total_variation_distance": totals["tv_distance"].mean(),
        "max_total_variation_distance": totals["tv_distance"].max(),
        "mean_temperature_absolute_error_magnitude": temperature_mean_error,
        "max_temperature_absolute_error_magnitude": max(
            problem_temperature_mean_errors.values(), default=0.0
        ),
        "temperature_absolute_error_magnitude_by_problem": (
            problem_temperature_mean_errors
        ),
        "mean_codelets_relative_error_magnitude": codelets_errors.mean(),
        "max_codelets_relative_error_magnitude": codelets_errors.max(),
        "codelets_relative_error_magnitude_quantiles": {
            percentile: codelets_errors.quantile(percentile / 100)
            for percentile in range(10, 101, 10)
        },
    }


def _frequency_weighted_mean(rows: pd.DataFrame) -> float:
    """Return the reference-frequency-weighted temperature error for rows."""
    total_frequency = rows["expected_frequency"].sum()
    if total_frequency == 0:
        return 0.0
    return float(
        (rows["absolute_temperature_error"] * rows["expected_frequency"]).sum()
        / total_frequency
    )


def _as_dataframe(behaviour: pd.DataFrame | list[dict[str, Any]]) -> pd.DataFrame:
    if isinstance(behaviour, pd.DataFrame):
        return behaviour.copy()
    return pd.DataFrame(behaviour)


def _total_row(results: pd.DataFrame, problem: str, description: str) -> pd.Series:
    totals = results.loc[results["solution"] == "Total"]
    if len(totals) != 1:
        raise ValueError(
            f"Expected exactly one Total row for {description} behaviour of "
            f"{problem!r}, found {len(totals)}."
        )
    return totals.iloc[0]


def _z_statistic(
    observed: pd.Series | dict[str, Any],
    expected: pd.Series | dict[str, Any],
    mean_column: str,
    standard_error_column: str,
) -> float | None:
    values = (
        observed[mean_column],
        expected[mean_column],
        observed[standard_error_column],
        expected[standard_error_column],
    )
    return None if any(pd.isna(value) for value in values) else z_statistic(*values)


def _comparison_row(
    *,
    problem: str,
    solution: str,
    observed: pd.Series | None,
    expected: pd.Series | dict[str, Any],
    tv_distance: float | None = None,
    codelets_z_stat: float | None = None,
    temperature_z_stat: float | None = None,
) -> dict[str, object]:
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
            0 if observed is None and field == "frequency" else _value(observed, field)
        )
        reference = _value(expected, field)
        row[f"observed_{field}"] = actual
        row[f"expected_{field}"] = reference
        row[f"{field}_difference"] = (
            actual - reference if actual is not None and reference is not None else None
        )
    observed_codelets = row["observed_mean_codelets_run"]
    expected_codelets = row["expected_mean_codelets_run"]
    row["codelets_relative_error_magnitude"] = (
        abs(observed_codelets - expected_codelets) / abs(expected_codelets)
        if observed_codelets is not None and expected_codelets not in (None, 0)
        else None
    )
    return row


def _value(row: pd.Series | dict[str, Any] | None, field: str) -> object | None:
    if row is None:
        return None
    value = row[field]
    return None if pd.isna(value) else value
