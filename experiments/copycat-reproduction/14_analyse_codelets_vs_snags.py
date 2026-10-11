"""Estimate codelet-run/snag associations from baseline runs.

Per-cell rows condition on both the input problem and answer. The final rows
pool those cells with a Fisher-z DerSimonian--Laird random-effects
meta-analysis; fixed-effect estimates are retained as a sensitivity measure.
"""

from __future__ import annotations

import math
from statistics import NormalDist

import pandas as pd

from copycat_reproduction.paths import REPRODUCTION_DATASETS, SNAGS_DATASETS

RAW_RESULTS_PATH = REPRODUCTION_DATASETS / "reproduction_raw_results.csv"
OUTPUT_PATH = SNAGS_DATASETS / "codelets_snags_correlations.csv"
REGRESSION_OUTPUT_PATH = SNAGS_DATASETS / "codelets_per_snag_regressions.csv"
MINIMUM_EXAMPLES = 100
CONFIDENCE_LEVEL = 0.95


def _two_sided_p_value(z_score: float) -> float:
    return 2 * NormalDist().cdf(-abs(z_score))


def _critical_value() -> float:
    """Return the normal critical value used for large-sample intervals."""
    return NormalDist().inv_cdf(1 - (1 - CONFIDENCE_LEVEL) / 2)


def _correlation_and_p_value(
    first: pd.Series, second: pd.Series, count: int
) -> tuple[float | None, float | None]:
    """Return an undefined correlation as null when either variable is constant."""
    if first.nunique() < 2 or second.nunique() < 2:
        return None, None
    correlation = float(first.corr(second))
    if not math.isfinite(correlation) or abs(correlation) >= 1:
        return correlation, None
    z_score = correlation * math.sqrt((count - 2) / (1 - correlation**2))
    return correlation, _two_sided_p_value(z_score)


def _fisher_confidence_interval(
    correlation: float | None, count: int
) -> tuple[float | None, float | None]:
    """Return a two-sided Fisher-z confidence interval for Pearson's r."""
    if correlation is None or count <= 3 or abs(correlation) >= 1:
        return None, None
    standard_error = 1 / math.sqrt(count - 3)
    fisher_z = math.atanh(correlation)
    critical_value = _critical_value()
    return (
        math.tanh(fisher_z - critical_value * standard_error),
        math.tanh(fisher_z + critical_value * standard_error),
    )


def _correlation_row(problem: str, answer: str, runs: pd.DataFrame) -> dict[str, object]:
    """Return the linear correlation for one problem/answer cell."""
    count = len(runs)
    pearson, pearson_p_value = _correlation_and_p_value(
        runs["codelets_run"], runs["snag_count"], count
    )
    pearson_ci_low, pearson_ci_high = _fisher_confidence_interval(pearson, count)
    return {
        "problem": problem,
        "answer": answer,
        "examples": count,
        "pearson_correlation": pearson,
        "pearson_p_value": pearson_p_value,
        "pearson_confidence_interval_low": pearson_ci_low,
        "pearson_confidence_interval_high": pearson_ci_high,
    }


def _pooled_row(cells: pd.DataFrame) -> dict[str, object]:
    """Pool cell correlations using DerSimonian--Laird random effects."""
    valid_cells = cells.dropna(subset=["pearson_correlation"])
    correlations = valid_cells["pearson_correlation"].clip(
        lower=-0.999999, upper=0.999999
    )
    fisher_z = correlations.map(math.atanh)
    variances = 1 / (valid_cells["examples"] - 3)
    fixed_weights = 1 / variances
    fixed_z = (fixed_weights * fisher_z).sum() / fixed_weights.sum()
    heterogeneity_q = (fixed_weights * (fisher_z - fixed_z) ** 2).sum()
    degrees_of_freedom = len(valid_cells) - 1
    c_value = fixed_weights.sum() - (fixed_weights**2).sum() / fixed_weights.sum()
    tau_squared = max(0.0, (heterogeneity_q - degrees_of_freedom) / c_value)
    random_weights = 1 / (variances + tau_squared)
    random_z = (random_weights * fisher_z).sum() / random_weights.sum()
    random_standard_error = math.sqrt(1 / random_weights.sum())
    correlation = math.tanh(random_z)
    return {
        "problem": "",
        "answer": "",
        "examples": int(valid_cells["examples"].sum()),
        "pearson_correlation": correlation,
        "pearson_p_value": _two_sided_p_value(random_z / random_standard_error),
        "pearson_confidence_interval_low": math.tanh(
            random_z - _critical_value() * random_standard_error
        ),
        "pearson_confidence_interval_high": math.tanh(
            random_z + _critical_value() * random_standard_error
        ),
        "cells_pooled": len(valid_cells),
        "fixed_effect_correlation": math.tanh(fixed_z),
        "heterogeneity_q": heterogeneity_q,
        "heterogeneity_df": degrees_of_freedom,
        "between_cell_variance_tau_squared": tau_squared,
    }


def _regression_row(problem: str, runs: pd.DataFrame) -> dict[str, object]:
    """Estimate the mean additional codelets associated with one extra snag.

    Each row uses all runs for one input problem, rather than conditioning on
    the final answer. The slope is descriptive: snag count and run length can
    affect each other during a run, so it is not a causal estimate.
    """
    snag_count = runs["snag_count"].astype(float)
    codelets_run = runs["codelets_run"].astype(float)
    examples = len(runs)
    centered_snags = snag_count - snag_count.mean()
    sum_squared_snags = float((centered_snags**2).sum())
    if sum_squared_snags == 0:
        raise ValueError(f"Problem {problem!r} has no variation in snag count.")

    slope = float((centered_snags * (codelets_run - codelets_run.mean())).sum())
    slope /= sum_squared_snags
    intercept = float(codelets_run.mean() - slope * snag_count.mean())
    residuals = codelets_run - (intercept + slope * snag_count)
    residual_sum_squares = float((residuals**2).sum())
    total_sum_squares = float(((codelets_run - codelets_run.mean()) ** 2).sum())
    residual_standard_error = math.sqrt(residual_sum_squares / (examples - 2))
    slope_standard_error = residual_standard_error / math.sqrt(sum_squared_snags)
    slope_t_statistic = slope / slope_standard_error
    critical_value = _critical_value()
    return {
        "problem": problem,
        "examples": examples,
        "snag_count_minimum": int(snag_count.min()),
        "snag_count_maximum": int(snag_count.max()),
        "mean_snag_count": float(snag_count.mean()),
        "intercept_codelets": intercept,
        "additional_codelets_per_snag": slope,
        "slope_standard_error": slope_standard_error,
        "slope_confidence_interval_low": slope - critical_value * slope_standard_error,
        "slope_confidence_interval_high": slope + critical_value * slope_standard_error,
        "slope_p_value": _two_sided_p_value(slope_t_statistic),
        "r_squared": 1 - residual_sum_squares / total_sum_squares,
        "residual_standard_error": residual_standard_error,
    }


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    raw_runs = pd.read_csv(RAW_RESULTS_PATH)
    required = {"problem", "answer", "codelets_run", "snag_count"}
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

    pooled = _pooled_row(cells)
    pd.concat([cells, pd.DataFrame([pooled])], ignore_index=True).to_csv(
        OUTPUT_PATH, index=False
    )
    snaggable_problems = [
        (problem, runs)
        for problem, runs in raw_runs.groupby("problem")
        if runs["snag_count"].sum() > 0 and runs["snag_count"].nunique() > 1
    ]
    regressions = pd.DataFrame(
        [_regression_row(problem, runs) for problem, runs in snaggable_problems]
    ).sort_values("problem")
    regressions.to_csv(REGRESSION_OUTPUT_PATH, index=False)
    print(f"Wrote {len(cells)} cell rows and one pooled row to {OUTPUT_PATH}")
    print(
        f"Wrote {len(regressions)} per-problem regression rows to "
        f"{REGRESSION_OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
