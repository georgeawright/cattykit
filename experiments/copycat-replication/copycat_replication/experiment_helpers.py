"""Shared helpers for the Copycat reproduction pipeline."""

from __future__ import annotations

from typing import Any

import pandas as pd


def result_case(problem: str, summary: pd.DataFrame, problem_id: str) -> dict[str, Any]:
    """Convert a Cattykit run summary into the Copycat result-data schema."""
    solutions = summary[summary["solution"] != "Total"]
    total = summary[summary["solution"] == "Total"].iloc[0]
    return {
        "problem": problem,
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
