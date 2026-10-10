"""Calibrate baseline answer TV distances against multinomial variation.

For each source problem, the published answer frequencies define a plug-in
multinomial distribution.  The analysis simulates two independent samples of
the published size, matching the published-versus-reproduction comparison,
and records the resulting total-variation-distance reference distribution.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from copycat_reproduction.paths import (
    CODERACK_REMOVAL_DATASETS,
    GOLD_PATH,
    QUANTIZATION_DATASETS,
    REPRODUCTION_DATASETS,
)

DEFAULT_RESAMPLES = 10_000
DEFAULT_SEED = 0


@dataclass(frozen=True)
class Study:
    """One implementation whose answer TV distances are being calibrated."""

    name: str
    comparison_path: Path
    output_path: Path


STUDIES = (
    Study(
        "standard reproduction",
        REPRODUCTION_DATASETS / "reproduction_comparison.csv",
        REPRODUCTION_DATASETS / "reproduction_tv_monte_carlo_baseline.csv",
    ),
    Study(
        "faithful original coderack removal",
        CODERACK_REMOVAL_DATASETS
        / "coderack_removal_faithful_original_removal_comparison.csv",
        CODERACK_REMOVAL_DATASETS
        / "coderack_removal_faithful_original_removal_tv_monte_carlo_baseline.csv",
    ),
    Study(
        "two-decimal quantisation",
        QUANTIZATION_DATASETS / "quantisation_two_decimal_quantisation_comparison.csv",
        QUANTIZATION_DATASETS
        / "quantisation_two_decimal_quantisation_tv_monte_carlo_baseline.csv",
    ),
)


def _published_probabilities(case: dict[str, Any]) -> tuple[np.ndarray, int]:
    """Return a problem's answer probabilities and reported number of runs."""
    frequencies = np.array(
        [solution["frequency"] for solution in case["solutions"].values()],
        dtype=np.int64,
    )
    if frequencies.size == 0 or (frequencies < 0).any():
        raise ValueError(
            f"Invalid published answer frequencies for {case['problem']!r}."
        )
    sample_size = int(frequencies.sum())
    if sample_size == 0:
        raise ValueError(
            f"Published answer frequencies sum to zero for {case['problem']!r}."
        )
    return frequencies / sample_size, sample_size


def _simulated_tv_distances(
    probabilities: np.ndarray,
    sample_size: int,
    resamples: int,
    generator: np.random.Generator,
) -> np.ndarray:
    """Simulate TV distances between independent samples from one distribution."""
    first = generator.multinomial(sample_size, probabilities, size=resamples)
    second = generator.multinomial(sample_size, probabilities, size=resamples)
    return np.abs(first - second).sum(axis=1) / (2 * sample_size)


def _comparison_distances(path: Path) -> pd.DataFrame:
    """Load one observed answer TV distance for every reproduced problem."""
    if not path.is_file():
        raise FileNotFoundError(f"Required comparison CSV is missing: {path}")
    comparison = pd.read_csv(path)
    required = {"id", "problem", "solution_total_variation_distance"}
    missing = required.difference(comparison.columns)
    if missing:
        raise ValueError(f"Comparison CSV is missing columns: {sorted(missing)}")
    if comparison["problem"].duplicated().any():
        raise ValueError("Comparison CSV must contain exactly one row per problem.")
    return comparison.set_index("problem")


def _reference_summary(
    original: dict[str, Any], resamples: int, seed: int
) -> pd.DataFrame:
    """Simulate the shared per-problem TV-distance reference distribution."""
    generator = np.random.default_rng(seed)
    rows = []
    for case in original["results"]:
        probabilities, sample_size = _published_probabilities(case)
        distances = _simulated_tv_distances(
            probabilities, sample_size, resamples, generator
        )
        rows.append(
            {
                "id": case["id"],
                "problem": case["problem"],
                "published_run_count": sample_size,
                "resamples": resamples,
                "reference_tv_distance_mean": float(distances.mean()),
                "reference_tv_distance_median": float(np.median(distances)),
                "reference_tv_distance_lower_95": float(np.quantile(distances, 0.025)),
                "reference_tv_distance_upper_95": float(np.quantile(distances, 0.975)),
                "seed": seed,
                "_reference_distances": distances,
            }
        )
    return pd.DataFrame(rows)


def _study_summary(
    study: Study, reference: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Attach one implementation's observed distances to shared references."""
    comparison = _comparison_distances(study.comparison_path)
    observed = reference.drop(columns="_reference_distances").merge(
        comparison[["solution_total_variation_distance"]],
        left_on="problem",
        right_index=True,
        how="left",
        validate="one_to_one",
    )
    if observed["solution_total_variation_distance"].isna().any():
        missing = observed.loc[
            observed["solution_total_variation_distance"].isna(), "problem"
        ].tolist()
        raise ValueError(f"Comparison CSV has no results for: {missing}")
    observed = observed.rename(
        columns={"solution_total_variation_distance": "observed_tv_distance"}
    )
    reference_distances = reference["_reference_distances"].tolist()
    observed["observed_tv_distance_percentile"] = [
        float((distances <= distance).mean())
        for distances, distance in zip(
            reference_distances, observed["observed_tv_distance"], strict=True
        )
    ]
    observed["reference_distances_at_least_observed"] = [
        float((distances >= distance).mean())
        for distances, distance in zip(
            reference_distances, observed["observed_tv_distance"], strict=True
        )
    ]
    outside = observed.loc[
        ~observed["observed_tv_distance"].between(
            observed["reference_tv_distance_lower_95"],
            observed["reference_tv_distance_upper_95"],
        )
    ]
    return observed, outside


def _print_study_summary(
    study: Study, summary: pd.DataFrame, outside: pd.DataFrame
) -> None:
    """Print a compact aggregate result and any out-of-range problems."""
    print(
        f"{study.name}: {len(summary) - len(outside)}/{len(summary)} observed TV "
        "distances fall within the 95% reference range."
    )
    print(
        "  mean observed/reference TV distance: "
        f"{summary['observed_tv_distance'].mean():.4f}/"
        f"{summary['reference_tv_distance_mean'].mean():.4f}"
    )
    if outside.empty:
        return
    print("  Outside the 95% reference range:")
    for row in outside.itertuples(index=False):
        print(
            f"    {row.id} {row.problem}: observed {row.observed_tv_distance:.4f}; "
            f"reference {row.reference_tv_distance_lower_95:.4f}"
            f"–{row.reference_tv_distance_upper_95:.4f}; "
            f"percentile {row.observed_tv_distance_percentile:.3f}"
        )


def main(
    gold_path: Path = GOLD_PATH,
    resamples: int = DEFAULT_RESAMPLES,
    seed: int = DEFAULT_SEED,
) -> None:
    """Write per-problem Monte Carlo TV-distance reference summaries."""
    if resamples < 1:
        raise ValueError("resamples must be at least 1")
    if not gold_path.is_file():
        raise FileNotFoundError(f"Missing original result data: {gold_path}")

    original = json.loads(gold_path.read_text(encoding="utf-8"))
    reference = _reference_summary(original, resamples, seed)
    for study in STUDIES:
        summary, outside = _study_summary(study, reference)
        study.output_path.parent.mkdir(parents=True, exist_ok=True)
        summary.to_csv(study.output_path, index=False)
        print(f"Wrote {len(summary)} problem summaries to {study.output_path}")
        _print_study_summary(study, summary, outside)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold-path", type=Path, default=GOLD_PATH)
    parser.add_argument("--resamples", type=int, default=DEFAULT_RESAMPLES)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    arguments = parser.parse_args()
    main(arguments.gold_path, arguments.resamples, arguments.seed)
