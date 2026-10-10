"""Estimate within-answer temperature/codelet correlations from baseline runs.

Per-cell rows condition on both the input problem and answer. The final rows
pool those cells with a Fisher-z DerSimonian--Laird random-effects
meta-analysis; fixed-effect estimates are retained as a sensitivity measure.
"""

from __future__ import annotations

import math
from statistics import NormalDist

import pandas as pd

from copycat_reproduction.paths import REPRODUCTION_DATASETS

RAW_RESULTS_PATH = REPRODUCTION_DATASETS / "reproduction_raw_results.csv"
OUTPUT_PATH = REPRODUCTION_DATASETS / "temperature_codelets_correlations.csv"
MINIMUM_EXAMPLES = 100


def _two_sided_p_value(z_score: float) -> float:
    return 2 * NormalDist().cdf(-abs(z_score))


def _correlation_row(problem: str, answer: str, runs: pd.DataFrame) -> dict[str, object]:
    """Return linear and rank correlations for one problem/answer cell."""
    count = len(runs)
    pearson = float(runs["temperature"].corr(runs["codelets_run"]))
    spearman = float(runs["temperature"].rank().corr(runs["codelets_run"].rank()))
    return {
        "row_type": "problem_answer",
        "problem": problem,
        "answer": answer,
        "examples": count,
        "pearson_correlation": pearson,
        "spearman_correlation": spearman,
        "pearson_p_value": _two_sided_p_value(
            pearson * math.sqrt((count - 2) / (1 - pearson**2))
        ),
        "spearman_p_value": _two_sided_p_value(
            spearman * math.sqrt((count - 2) / (1 - spearman**2))
        ),
    }


def _pooled_row(cells: pd.DataFrame, column: str) -> dict[str, object]:
    """Pool cell correlations using DerSimonian--Laird random effects."""
    correlations = cells[column].clip(lower=-0.999999, upper=0.999999)
    fisher_z = correlations.map(math.atanh)
    variances = 1 / (cells["examples"] - 3)
    fixed_weights = 1 / variances
    fixed_z = (fixed_weights * fisher_z).sum() / fixed_weights.sum()
    heterogeneity_q = (fixed_weights * (fisher_z - fixed_z) ** 2).sum()
    degrees_of_freedom = len(cells) - 1
    c_value = fixed_weights.sum() - (fixed_weights**2).sum() / fixed_weights.sum()
    tau_squared = max(0.0, (heterogeneity_q - degrees_of_freedom) / c_value)
    random_weights = 1 / (variances + tau_squared)
    random_z = (random_weights * fisher_z).sum() / random_weights.sum()
    random_standard_error = math.sqrt(1 / random_weights.sum())
    correlation = math.tanh(random_z)
    return {
        "row_type": "pooled_random_effects",
        "problem": "",
        "answer": "",
        "examples": int(cells["examples"].sum()),
        "pearson_correlation": correlation if column == "pearson_correlation" else None,
        "spearman_correlation": correlation if column == "spearman_correlation" else None,
        "pearson_p_value": (
            _two_sided_p_value(random_z / random_standard_error)
            if column == "pearson_correlation"
            else None
        ),
        "spearman_p_value": (
            _two_sided_p_value(random_z / random_standard_error)
            if column == "spearman_correlation"
            else None
        ),
        "correlation_type": column.removesuffix("_correlation"),
        "cells_pooled": len(cells),
        "fixed_effect_correlation": math.tanh(fixed_z),
        "heterogeneity_q": heterogeneity_q,
        "heterogeneity_df": degrees_of_freedom,
        "between_cell_variance_tau_squared": tau_squared,
    }


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    raw_runs = pd.read_csv(RAW_RESULTS_PATH)
    required = {"problem", "answer", "temperature", "codelets_run"}
    missing = required.difference(raw_runs.columns)
    if missing:
        raise ValueError(f"Raw results CSV is missing columns: {sorted(missing)}")

    rows = [
        _correlation_row(problem, answer, runs)
        for (problem, answer), runs in raw_runs.groupby(["problem", "answer"])
        if len(runs) >= MINIMUM_EXAMPLES
    ]
    cells = pd.DataFrame(rows).sort_values(["problem", "answer"])
    if cells.empty:
        raise ValueError(f"No problem/answer cells have {MINIMUM_EXAMPLES} examples.")

    pooled = [
        _pooled_row(cells, column)
        for column in ("pearson_correlation", "spearman_correlation")
    ]
    pd.concat([cells, pd.DataFrame(pooled)], ignore_index=True).to_csv(
        OUTPUT_PATH, index=False
    )
    print(f"Wrote {len(cells)} cell rows and {len(pooled)} pooled rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
