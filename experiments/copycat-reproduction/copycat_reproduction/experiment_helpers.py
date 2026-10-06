"""Shared, non-executing helpers for the Copycat reproduction pipeline."""

from __future__ import annotations

import json
from math import sqrt
from pathlib import Path
from typing import Any

import pandas as pd
from cattykit.experiments import (
    chi_square_survival_function,
    mean_absolute_error,
    run_experiment,
    summarize_runs,
    total_variation_distance,
    two_sided_p_value,
    z_statistic,
)

from .paths import FIGURES, TEMPLATE_PATH
from .table_helpers import comparison_row, reproduction_summary


MIN_ORIGINAL_SOLUTION_FREQUENCY = 10


def result_case(
    problem: str, summary: pd.DataFrame, source: dict[str, Any], problem_id: str
) -> dict[str, Any]:
    """Convert a Cattykit run summary into the Copycat result-data schema."""
    solutions = summary[summary["solution"] != "Total"]
    total = summary[summary["solution"] == "Total"].iloc[0]
    return {
        "problem": problem,
        "source": source,
        "solutions": {
            str(row.solution): {
                "frequency": int(row.frequency),
                "temperature_mean": float(row.mean_temperature),
                "temperature_standard_error": float(row.temperature_standard_error),
            }
            for row in solutions.itertuples(index=False)
        },
        "codelets": {
            "mean": float(total.mean_codelets_run),
            "standard_error": float(total.codelets_standard_error),
        },
        "id": problem_id,
    }


def reproduction_from_raw_results(raw_results: pd.DataFrame) -> dict[str, Any]:
    """Rebuild a summary JSON document from one raw result CSV."""
    required_columns = {
        "problem",
        "random_seed",
        "answer",
        "temperature",
        "codelets_run",
    }
    missing_columns = required_columns.difference(raw_results.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Raw results CSV is missing required columns: {missing}.")
    template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    reproduced_cases = []
    for case in template["results"]:
        problem_results = raw_results.loc[raw_results["problem"] == case["problem"]]
        if problem_results.empty:
            raise ValueError(f"Raw results CSV has no runs for {case['problem']!r}.")
        runs = [
            {
                "random_seed": row.random_seed,
                "solution": row.answer,
                "temperature": row.temperature,
                "codelets_run": row.codelets_run,
            }
            for row in problem_results.itertuples(index=False)
        ]
        reproduced_cases.append(
            result_case(
                case["problem"],
                summarize_runs(runs, case["problem"]),
                case["source"],
                case["id"],
            )
        )
    return {
        "schema_version": template["schema_version"],
        "source_work": template["source_work"],
        "basic_problems": template["basic_problems"],
        "results": reproduced_cases,
    }


def run_reproduction(
    model_name: str,
    gold_behaviour: dict[str, pd.DataFrame | list[dict]],
    iterations: int,
    output_file: str | Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Run Copycat and compare its summaries to the supplied published data."""
    observed = run_experiment(
        model_name, list(gold_behaviour), iterations, verbose=False
    ).summary
    rows = []
    for problem, behaviour in gold_behaviour.items():
        gold = (
            behaviour
            if isinstance(behaviour, pd.DataFrame)
            else pd.DataFrame(behaviour)
        )
        actual = observed[observed.problem == problem]
        actual_answers, gold_answers = (
            actual[actual.solution != "Total"],
            gold[gold.solution != "Total"],
        )
        tv = total_variation_distance(
            dict(zip(actual_answers.solution, actual_answers.frequency, strict=True)),
            dict(zip(gold_answers.solution, gold_answers.frequency, strict=True)),
        )
        actual_total, gold_total = (
            actual[actual.solution == "Total"].iloc[0],
            gold[gold.solution == "Total"].iloc[0],
        )
        rows.append(
            comparison_row(
                problem=problem,
                solution="Total",
                observed=actual_total,
                expected=gold_total,
                tv_distance=tv,
                codelets_z_stat=z_statistic(
                    actual_total.mean_codelets_run,
                    gold_total.mean_codelets_run,
                    actual_total.codelets_standard_error,
                    gold_total.codelets_standard_error,
                ),
            )
        )
    comparison = pd.DataFrame(rows)
    if output_file:
        comparison.to_csv(output_file, index=False)
    return comparison, reproduction_summary(comparison)
