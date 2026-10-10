"""Assess how printed historical-result precision affects z diagnostics."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from math import inf, sqrt
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from copycat_reproduction.paths import GOLD_PATH, REPRODUCTION_DATASETS
from copycat_reproduction.table_helpers import MIN_ORIGINAL_SOLUTION_FREQUENCY

DEFAULT_RESAMPLES = 10_000
DEFAULT_SEED = 0
TEMPERATURE_MEAN_HALF_WIDTH = 0.005
TEMPERATURE_STANDARD_ERROR_HALF_WIDTH = 0.0005
CODELETS_MEAN_HALF_WIDTH = 0.5
CODELETS_STANDARD_ERROR_HALF_WIDTH = 0.05
REPRODUCTION_PATH = REPRODUCTION_DATASETS / "reproduction_copycat_results.json"
INTERVAL_PATH = REPRODUCTION_DATASETS / "transcription_precision_intervals.csv"
SUMMARY_PATH = REPRODUCTION_DATASETS / "transcription_precision_sensitivity.csv"


@dataclass(frozen=True)
class Comparison:
    """One observed-versus-published rounded result."""

    metric: str
    problem_id: str
    problem: str
    solution: str | None
    observed_mean: float
    observed_standard_error: float
    published_mean: float
    published_standard_error: float
    mean_half_width: float
    standard_error_half_width: float


def _z_magnitude(
    difference: float, observed_standard_error: float, published_standard_error: float
) -> float:
    denominator = sqrt(observed_standard_error**2 + published_standard_error**2)
    if denominator == 0:
        return 0.0 if difference == 0 else inf
    return abs(difference) / denominator


def _interval(value: float, half_width: float, lower_bound: float | None) -> tuple[float, float]:
    """Return the interval implied by round-to-nearest at displayed precision."""
    lower = value - half_width
    if lower_bound is not None:
        lower = max(lower_bound, lower)
    return lower, value + half_width


def _distance_to_interval(value: float, lower: float, upper: float) -> float:
    """Return the smallest distance from value to a closed interval."""
    return max(lower - value, 0.0, value - upper)


def _temperature_comparisons(
    reproduction: dict[str, Any], original: dict[str, Any]
) -> list[Comparison]:
    original_cases = {case["problem"]: case for case in original["results"]}
    comparisons = []
    for reproduced in reproduction["results"]:
        published = original_cases[reproduced["problem"]]
        for solution, expected in published["solutions"].items():
            observed = reproduced["solutions"].get(solution)
            if observed is None or expected["frequency"] < MIN_ORIGINAL_SOLUTION_FREQUENCY:
                continue
            comparisons.append(
                Comparison(
                    metric="Temperature",
                    problem_id=published["id"],
                    problem=published["problem"],
                    solution=solution,
                    observed_mean=float(observed["temperature_mean"]),
                    observed_standard_error=float(observed["temperature_standard_error"]),
                    published_mean=float(expected["temperature_mean"]),
                    published_standard_error=float(expected["temperature_standard_error"]),
                    mean_half_width=TEMPERATURE_MEAN_HALF_WIDTH,
                    standard_error_half_width=TEMPERATURE_STANDARD_ERROR_HALF_WIDTH,
                )
            )
    return comparisons


def _codelets_comparisons(
    reproduction: dict[str, Any], original: dict[str, Any]
) -> list[Comparison]:
    original_cases = {case["problem"]: case for case in original["results"]}
    return [
        Comparison(
            metric="Codelets-run",
            problem_id=published["id"],
            problem=published["problem"],
            solution=None,
            observed_mean=float(reproduced["codelets"]["mean"]),
            observed_standard_error=float(reproduced["codelets"]["standard_error"]),
            published_mean=float(published["codelets"]["mean"]),
            published_standard_error=float(published["codelets"]["standard_error"]),
            mean_half_width=CODELETS_MEAN_HALF_WIDTH,
            standard_error_half_width=CODELETS_STANDARD_ERROR_HALF_WIDTH,
        )
        for reproduced in reproduction["results"]
        for published in [original_cases[reproduced["problem"]]]
    ]


def interval_table(comparisons: list[Comparison]) -> pd.DataFrame:
    """Return nominal and endpoint absolute-z values for every comparison."""
    rows = []
    for item in comparisons:
        mean_lower, mean_upper = _interval(
            item.published_mean, item.mean_half_width, 0.0
        )
        se_lower, se_upper = _interval(
            item.published_standard_error, item.standard_error_half_width, 0.0
        )
        nominal = _z_magnitude(
            item.observed_mean - item.published_mean,
            item.observed_standard_error,
            item.published_standard_error,
        )
        minimum = _z_magnitude(
            _distance_to_interval(item.observed_mean, mean_lower, mean_upper),
            item.observed_standard_error,
            se_upper,
        )
        maximum = _z_magnitude(
            max(
                abs(item.observed_mean - mean_lower),
                abs(item.observed_mean - mean_upper),
            ),
            item.observed_standard_error,
            se_lower,
        )
        rows.append(
            {
                "metric": item.metric,
                "id": item.problem_id,
                "problem": item.problem,
                "solution": item.solution,
                "observed_mean": item.observed_mean,
                "published_mean": item.published_mean,
                "published_mean_lower": mean_lower,
                "published_mean_upper": mean_upper,
                "observed_standard_error": item.observed_standard_error,
                "published_standard_error": item.published_standard_error,
                "published_standard_error_lower": se_lower,
                "published_standard_error_upper": se_upper,
                "nominal_absolute_z": nominal,
                "minimum_absolute_z": minimum,
                "maximum_absolute_z": maximum,
            }
        )
    return pd.DataFrame(rows).sort_values(["metric", "id", "solution"])


def _metric_sensitivity_summary(
    metric: str,
    comparisons: list[Comparison],
    resamples: int,
    generator: np.random.Generator,
) -> pd.DataFrame:
    """Sample intervals for one metric and summarize aggregate z diagnostics."""
    observed_mean = np.array([item.observed_mean for item in comparisons])
    observed_se = np.array([item.observed_standard_error for item in comparisons])
    published_mean = np.array([item.published_mean for item in comparisons])
    published_se = np.array([item.published_standard_error for item in comparisons])
    mean_half_width = np.array([item.mean_half_width for item in comparisons])
    se_half_width = np.array(
        [item.standard_error_half_width for item in comparisons]
    )
    nominal_z = np.abs(observed_mean - published_mean) / np.hypot(
        observed_se, published_se
    )
    sampled_means = generator.uniform(
        np.maximum(0.0, published_mean - mean_half_width),
        published_mean + mean_half_width,
        size=(resamples, len(comparisons)),
    )
    sampled_ses = generator.uniform(
        np.maximum(0.0, published_se - se_half_width),
        published_se + se_half_width,
        size=(resamples, len(comparisons)),
    )
    sampled_z = np.abs(observed_mean - sampled_means) / np.hypot(
        observed_se, sampled_ses
    )
    statistics = {
        f"{metric} RMS |z|": np.sqrt(np.mean(sampled_z**2, axis=1)),
        f"{metric} max |z|": np.max(sampled_z, axis=1),
        f"{metric} z chi-square": np.sum(sampled_z**2, axis=1),
        f"{metric} comparisons with |z| > 2": np.sum(sampled_z > 2, axis=1),
    }
    nominal_statistics = {
        f"{metric} RMS |z|": sqrt(float(np.mean(nominal_z**2))),
        f"{metric} max |z|": float(np.max(nominal_z)),
        f"{metric} z chi-square": float(np.sum(nominal_z**2)),
        f"{metric} comparisons with |z| > 2": int(np.sum(nominal_z > 2)),
    }
    return pd.DataFrame(
        {
            "metric": name,
            "nominal": nominal_statistics[name],
            "sensitivity_2_5_percent": float(np.quantile(values, 0.025)),
            "sensitivity_median": float(np.median(values)),
            "sensitivity_97_5_percent": float(np.quantile(values, 0.975)),
        }
        for name, values in statistics.items()
    )


def sensitivity_summary(
    comparisons: list[Comparison], resamples: int, seed: int
) -> pd.DataFrame:
    """Return reproducible interval-sampling summaries for each result metric."""
    if resamples < 1:
        raise ValueError("resamples must be positive.")
    generator = np.random.default_rng(seed)
    summaries = []
    for metric in ("Temperature", "Codelets-run"):
        metric_comparisons = [item for item in comparisons if item.metric == metric]
        if not metric_comparisons:
            raise ValueError(f"No {metric.lower()} comparisons.")
        summaries.append(
            _metric_sensitivity_summary(
                metric, metric_comparisons, resamples, generator
            )
        )
    summary = pd.concat(summaries, ignore_index=True)
    summary["resamples"] = resamples
    summary["seed"] = seed
    return summary


def main(
    reproduction_path: Path = REPRODUCTION_PATH,
    gold_path: Path = GOLD_PATH,
    resamples: int = DEFAULT_RESAMPLES,
    seed: int = DEFAULT_SEED,
) -> None:
    """Write interval and aggregate transcription-precision sensitivity CSVs."""
    for path, description in (
        (reproduction_path, "reproduction"),
        (gold_path, "original result"),
    ):
        if not path.is_file():
            raise FileNotFoundError(f"Missing {description} data: {path}")
    reproduction = json.loads(reproduction_path.read_text(encoding="utf-8"))
    original = json.loads(gold_path.read_text(encoding="utf-8"))
    comparisons = _temperature_comparisons(reproduction, original)
    comparisons.extend(_codelets_comparisons(reproduction, original))
    intervals = interval_table(comparisons)
    summary = sensitivity_summary(comparisons, resamples, seed)
    REPRODUCTION_DATASETS.mkdir(parents=True, exist_ok=True)
    intervals.to_csv(INTERVAL_PATH, index=False)
    summary.to_csv(SUMMARY_PATH, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reproduction-path", type=Path, default=REPRODUCTION_PATH)
    parser.add_argument("--gold-path", type=Path, default=GOLD_PATH)
    parser.add_argument("--resamples", type=int, default=DEFAULT_RESAMPLES)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    main(**vars(parser.parse_args()))
