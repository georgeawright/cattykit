"""Shared, non-executing helpers for the Copycat reproduction pipeline."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd
from cattykit.experiments import summarize_runs

from .paths import TEMPLATE_PATH


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
