from collections.abc import Iterable
from math import erfc, exp, inf, isfinite, lgamma, log, sqrt

import pandas as pd

SUMMARY_COLUMNS = [
    "problem",
    "solution",
    "frequency",
    "mean_codelets_run",
    "codelets_standard_error",
    "mean_temperature",
    "temperature_standard_error",
]


def mean_absolute_error(
    observed: Iterable[float],
    expected: Iterable[float],
) -> float:
    """Return the mean absolute difference between equal-length measurements."""
    pairs = list(zip(observed, expected, strict=True))
    return (
        sum(abs(actual - reference) for actual, reference in pairs) / len(pairs)
        if pairs
        else 0.0
    )


def chi_square_survival_function(statistic: float, degrees_of_freedom: int) -> float:
    """Return the chi-square survival probability without a SciPy dependency.

    This evaluates the regularized upper incomplete gamma function at
    ``statistic / 2``.
    """
    if degrees_of_freedom < 1:
        return 1.0
    if statistic <= 0:
        return 1.0
    if not isfinite(statistic):
        return 0.0 if statistic == inf else float("nan")
    return _regularized_gamma_q(degrees_of_freedom / 2, statistic / 2)


def _regularized_gamma_q(shape: float, value: float) -> float:
    """Evaluate the regularized upper incomplete gamma function."""
    epsilon = 1e-14
    minimum = 1e-300
    if value < shape + 1:
        term = 1 / shape
        total = term
        for index in range(1, 10_000):
            term *= value / (shape + index)
            total += term
            if abs(term) <= abs(total) * epsilon:
                break
        return 1 - total * exp(-value + shape * log(value) - lgamma(shape))

    denominator = value + 1 - shape
    continued_fraction = 1 / minimum
    reciprocal = 1 / denominator
    result = reciprocal
    for index in range(1, 10_000):
        numerator = -index * (index - shape)
        denominator += 2
        reciprocal = numerator * reciprocal + denominator
        if abs(reciprocal) < minimum:
            reciprocal = minimum
        continued_fraction = denominator + numerator / continued_fraction
        if abs(continued_fraction) < minimum:
            continued_fraction = minimum
        reciprocal = 1 / reciprocal
        delta = reciprocal * continued_fraction
        result *= delta
        if abs(delta - 1) <= epsilon:
            break
    return exp(-value + shape * log(value) - lgamma(shape)) * result


def total_variation_distance(
    observed: dict[str, int],
    expected: dict[str, int],
) -> float:
    """Return total variation distance between two discrete distributions."""
    observed_total = sum(observed.values())
    expected_total = sum(expected.values())
    if observed_total == 0 or expected_total == 0:
        raise ValueError("Distributions must contain at least one observation.")
    answers = observed.keys() | expected.keys()
    return 0.5 * sum(
        abs(
            observed.get(answer, 0) / observed_total
            - expected.get(answer, 0) / expected_total
        )
        for answer in answers
    )


def z_statistic(
    observed_mean: float,
    expected_mean: float,
    observed_standard_error: float,
    expected_standard_error: float,
) -> float:
    """Return the z statistic for two means with independent errors."""
    standard_error = sqrt(observed_standard_error**2 + expected_standard_error**2)
    difference = observed_mean - expected_mean
    if standard_error == 0:
        if difference == 0:
            return 0.0
        return float("inf") if difference > 0 else float("-inf")
    return difference / standard_error


def two_sided_p_value(z_score: float) -> float:
    """Return the two-sided normal-distribution p value for a z statistic."""
    return erfc(abs(z_score) / sqrt(2))


def summarize_runs(
    runs: list[dict[str, str | float | int | None]],
    problem: str,
) -> pd.DataFrame:
    """Summarize individual runs, including an overall totals row."""
    data = pd.DataFrame(runs)
    if data.empty:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)
    grouped = data.groupby(
        "solution",
        sort=False,
    )
    summary = grouped.agg(
        frequency=("solution", "size"),
        mean_codelets_run=("codelets_run", "mean"),
        codelets_standard_error=("codelets_run", "sem"),
        mean_temperature=("temperature", "mean"),
        temperature_standard_error=("temperature", "sem"),
    ).reset_index()
    summary = summary.sort_values(
        "frequency",
        ascending=False,
        kind="stable",
    )
    error_columns = [
        "codelets_standard_error",
        "temperature_standard_error",
    ]
    summary[error_columns] = summary[error_columns].fillna(0.0)
    totals = pd.DataFrame(
        [
            {
                "solution": "Total",
                "frequency": len(data),
                "mean_codelets_run": (data["codelets_run"].mean()),
                "codelets_standard_error": (data["codelets_run"].sem()),
                "mean_temperature": (data["temperature"].mean()),
                "temperature_standard_error": (data["temperature"].sem()),
            }
        ]
    )
    totals[error_columns] = totals[error_columns].fillna(0.0)
    summary = pd.concat(
        [summary, totals],
        ignore_index=True,
    )
    summary.insert(
        0,
        "problem",
        problem,
    )
    return summary[SUMMARY_COLUMNS]
