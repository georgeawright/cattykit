import sys
from math import erfc, exp, inf, isfinite, lgamma, log, sqrt
from pathlib import Path
from shutil import get_terminal_size

import pandas as pd

from .logging import CattycamLogger, NullLogger
from .models import load_model


SUMMARY_COLUMNS = [
    "problem",
    "solution",
    "frequency",
    "mean_codelets_run",
    "codelets_standard_error",
    "mean_temperature",
    "temperature_standard_error",
]


def run_experiment(
    model_name: str,
    problems: list[str],
    iterations: int,
    logging_db: str | Path | None = None,
    verbose: bool = True,
) -> pd.DataFrame:
    """Run the model repeatedly on each problem.
    The iteration count is used as the random seed given to the model, so the
    same random seeds are used for each problem.
    Returns one results DataFrame containing one row per solution plus a
    totals row for each problem.
    """
    interactive = verbose and sys.stdout.isatty()
    result_frames: list[pd.DataFrame] = []
    logger = (
        CattycamLogger(logging_db, model_name)
        if logging_db is not None
        else NullLogger(model_name)
    )
    try:
        for problem_number, problem in enumerate(problems):
            if interactive:
                if problem_number:
                    print(_terminal_rule("="))
                print(problem)
                print(_terminal_rule("-"))
                display = RunningAnswerDisplay()
            runs: list[dict[str, str | float | int | None]] = []
            for seed in range(iterations):
                model = load_model(
                    model_name,
                    config={"seed": seed},
                    logger=logger,
                )
                try:
                    answer = model.solve(problem)
                    runs.append(
                        {
                            "solution": answer,
                            "codelets_run": model.coderack.number_of_codelets_run,
                            "temperature": model.temperature,
                        }
                    )
                    if interactive:
                        display.update(summarize_runs(runs, problem))
                finally:
                    model.close()
            result_frames.append(summarize_runs(runs, problem))
    finally:
        logger.close()
    if not result_frames:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)
    return pd.concat(result_frames, ignore_index=True)


def run_reproduction(
    model_name: str,
    gold_behaviour: dict[str, pd.DataFrame | list[dict]],
    iterations: int,
    verbose: bool = True,
    output_file: str | None = None,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Compare current model behaviour with previously published behaviour.
    ``gold_behaviour`` maps each problem to a summary table with the same
    columns produced by ``summarize_runs``, except for ``problem``.
    The returned table has paired observed and expected columns for every
    expected solution and totals row. Differences are observed minus expected.
    """
    problems = list(gold_behaviour.keys())
    observed = run_experiment(
        model_name,
        problems,
        iterations,
        verbose=False,
    )
    gold = _gold_behaviour_dataframe(gold_behaviour)
    comparison_rows: list[dict[str, str | int | float | None]] = []
    for problem in problems:
        observed_problem = observed[observed["problem"] == problem]
        gold_problem = gold[gold["problem"] == problem]
        observed_solutions = observed_problem[observed_problem["solution"] != "Total"]
        gold_solutions = gold_problem[gold_problem["solution"] != "Total"]
        observed_distribution = dict(
            zip(
                observed_solutions["solution"],
                observed_solutions["frequency"],
            )
        )
        gold_distribution = dict(
            zip(
                gold_solutions["solution"],
                gold_solutions["frequency"],
            )
        )
        tv_distance = total_variation_distance(
            observed_distribution,
            gold_distribution,
        )
        observed_total = _total_row(
            observed_problem,
            problem,
            "observed",
        )
        gold_total = _total_row(
            gold_problem,
            problem,
            "gold",
        )
        codelets_z = z_statistic(
            observed_mean=observed_total["mean_codelets_run"],
            expected_mean=gold_total["mean_codelets_run"],
            observed_standard_error=observed_total["codelets_standard_error"],
            expected_standard_error=gold_total["codelets_standard_error"],
        )
        comparison_rows.append(
            _comparison_row(
                problem=problem,
                solution="Total",
                observed=observed_total,
                expected=gold_total,
                tv_distance=tv_distance,
                codelets_z_stat=codelets_z,
            )
        )
        for gold_row in gold_solutions.itertuples(index=False):
            observed_match = observed_solutions[
                observed_solutions["solution"] == gold_row.solution
            ]
            if observed_match.empty:
                observed_row = None
                temperature_z = None
            else:
                observed_row = observed_match.iloc[0]
                temperature_z = z_statistic(
                    observed_mean=observed_row["mean_temperature"],
                    expected_mean=gold_row.mean_temperature,
                    observed_standard_error=observed_row["temperature_standard_error"],
                    expected_standard_error=(gold_row.temperature_standard_error),
                )
            comparison_rows.append(
                _comparison_row(
                    problem=problem,
                    solution=gold_row.solution,
                    observed=observed_row,
                    expected=gold_row._asdict(),
                    temperature_z_stat=temperature_z,
                )
            )
    comparison = pd.DataFrame(
        comparison_rows,
        columns=[
            "problem",
            "solution",
            "observed_frequency",
            "expected_frequency",
            "frequency_difference",
            "observed_mean_codelets_run",
            "expected_mean_codelets_run",
            "mean_codelets_run_difference",
            "codelets_relative_error_magnitude",
            "observed_codelets_standard_error",
            "expected_codelets_standard_error",
            "codelets_standard_error_difference",
            "observed_mean_temperature",
            "expected_mean_temperature",
            "mean_temperature_difference",
            "observed_temperature_standard_error",
            "expected_temperature_standard_error",
            "temperature_standard_error_difference",
            "tv_distance",
            "codelets_z_stat",
            "temperature_z_stat",
        ],
    )
    summary = _reproduction_summary(comparison)
    if verbose:
        print(
            comparison.to_string(
                index=False,
                na_rep="-",
                formatters={
                    "tv_distance": lambda x: f"{x:.4f}",
                    "codelets_z_stat": lambda x: f"{x:.2f}",
                    "codelets_relative_error_magnitude": lambda x: f"{x:.1%}",
                    "temperature_z_stat": lambda x: f"{x:.2f}",
                },
            )
        )
        for key, value in summary.items():
            print(f"{key}: {value}")
    if output_file:
        comparison.to_csv(output_file, index=False)
    return comparison, summary


def _comparison_row(
    *,
    problem: str,
    solution: str,
    observed: pd.Series | dict[str, object] | None,
    expected: pd.Series | dict[str, object] | None,
    tv_distance: float | None = None,
    codelets_z_stat: float | None = None,
    temperature_z_stat: float | None = None,
) -> dict[str, str | float | int | None]:
    """Build one observed-versus-expected comparison row."""
    row: dict[str, str | float | int | None] = {
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
        observed_value = _row_value(observed, field)
        expected_value = _row_value(expected, field)
        row[f"observed_{field}"] = observed_value
        row[f"expected_{field}"] = expected_value
        row[f"{field}_difference"] = _difference(
            observed_value,
            expected_value,
        )
    row["codelets_relative_error_magnitude"] = _relative_error_magnitude(
        row["observed_mean_codelets_run"],
        row["expected_mean_codelets_run"],
    )
    return row


def _row_value(
    row: pd.Series | dict[str, object] | None,
    field: str,
) -> float | int | None:
    if row is None:
        return 0 if field == "frequency" else None
    value = row.get(field)
    return None if pd.isna(value) else value


def _difference(
    observed: float | int | None,
    expected: float | int | None,
) -> float | int | None:
    if observed is None or expected is None:
        return None
    return observed - expected


def _relative_error_magnitude(
    observed: float | int | None,
    expected: float | int | None,
) -> float | None:
    """Return the magnitude of error relative to the expected value."""
    if observed is None or expected is None or expected == 0:
        return None
    return abs(observed - expected) / expected


def _gold_behaviour_dataframe(
    gold_behaviour: dict[str, pd.DataFrame | list[dict]],
) -> pd.DataFrame:
    """Combine per-problem gold summaries into one DataFrame."""
    frames: list[pd.DataFrame] = []
    for problem, behaviour in gold_behaviour.items():
        frame = (
            behaviour.copy()
            if isinstance(behaviour, pd.DataFrame)
            else pd.DataFrame(behaviour)
        )
        frame.insert(0, "problem", problem)
        frames.append(frame)
    if not frames:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)
    return pd.concat(frames, ignore_index=True)


def _total_row(
    results: pd.DataFrame,
    problem: str,
    description: str,
) -> pd.Series:
    """Return the single totals row for a problem."""
    total = results[results["solution"] == "Total"]
    if len(total) != 1:
        raise ValueError(
            f"Expected exactly one Total row for {description} behaviour "
            f"of {problem!r}, found {len(total)}."
        )
    return total.iloc[0]


def _reproduction_summary(comparison: pd.DataFrame) -> dict[str, object]:
    """Calculate aggregate reproduction statistics from a comparison table."""
    tv_distances = comparison["tv_distance"].dropna().tolist()
    codelets_z_scores = comparison["codelets_z_stat"].dropna().tolist()
    codelets_relative_error_magnitudes = comparison[
        "codelets_relative_error_magnitude"
    ].dropna().tolist()
    temperature_z_scores = comparison.loc[
        comparison["expected_frequency"] >= 10,
        "temperature_z_stat",
    ].dropna().tolist()
    temperature_absolute_error_magnitudes = comparison.loc[
        comparison["expected_frequency"] >= 10,
        "mean_temperature_difference",
    ].dropna().abs().tolist()
    return {
        "mean_total_variation_distance": _mean(tv_distances),
        "max_total_variation_distance": max(tv_distances, default=0.0),
        "mean_codelets_relative_error_magnitude": _mean(
            codelets_relative_error_magnitudes,
        ),
        "max_codelets_relative_error_magnitude": max(
            codelets_relative_error_magnitudes,
            default=0.0,
        ),
        "codelets_relative_error_magnitude_quantiles": _deciles(
            codelets_relative_error_magnitudes,
        ),
        "mean_temperature_absolute_error_magnitude": _mean(
            temperature_absolute_error_magnitudes,
        ),
        "max_temperature_absolute_error_magnitude": max(
            temperature_absolute_error_magnitudes,
            default=0.0,
        ),
        "temperature_absolute_error_magnitude_quantiles": _deciles(
            temperature_absolute_error_magnitudes,
        ),
        **_z_score_summary("codelets", codelets_z_scores),
        **_z_score_summary("temperature", temperature_z_scores),
    }


def _z_score_summary(prefix: str, z_scores: list[float]) -> dict[str, float]:
    """Return chi-square and descriptive statistics for independent z scores."""
    statistic = sum(z_score**2 for z_score in z_scores)
    return {
        f"{prefix}_chi_square_statistic": statistic,
        f"{prefix}_chi_square_p_value": chi_square_survival_function(
            statistic,
            degrees_of_freedom=len(z_scores),
        ),
        f"{prefix}_rms_z_score": sqrt(statistic / len(z_scores)) if z_scores else 0.0,
        f"{prefix}_max_absolute_z_score": max(
            (abs(z_score) for z_score in z_scores),
            default=0.0,
        ),
    }


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _deciles(values: list[float]) -> dict[int, float]:
    """Return the 10th through 100th percentiles, keyed by percentile."""
    if not values:
        return {percentile: 0.0 for percentile in range(10, 101, 10)}
    ordered = sorted(values)
    result = {}
    for percentile in range(10, 101, 10):
        position = (len(ordered) - 1) * percentile / 100
        lower = int(position)
        upper = min(lower + 1, len(ordered) - 1)
        fraction = position - lower
        result[percentile] = ordered[lower] + fraction * (
            ordered[upper] - ordered[lower]
        )
    return result


def chi_square_survival_function(
    statistic: float,
    degrees_of_freedom: int,
) -> float:
    """Return ``P(X >= statistic)`` for a chi-square random variable.

    This is the regularized upper incomplete gamma function evaluated at
    ``statistic / 2`` and avoids making SciPy a runtime dependency.
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


def _terminal_rule(character: str) -> str:
    """Return a full-width terminal separator."""
    return character * get_terminal_size(fallback=(80, 24)).columns


class RunningAnswerDisplay:
    def __init__(self):
        self.lines_printed = 0

    def update(self, results: pd.DataFrame) -> None:
        table = (
            results.drop(columns="problem")
            .rename(
                columns={
                    "solution": "Solution",
                    "frequency": "Runs",
                    "mean_codelets_run": "Mean codelets",
                    "codelets_standard_error": "Codelets SE",
                    "mean_temperature": "Mean temp",
                    "temperature_standard_error": "Temp SE",
                }
            )
            .to_string(
                index=False,
                formatters={
                    "Mean codelets": "{:.0f}".format,
                    "Codelets SE": "{:.1f}".format,
                    "Mean temp": "{:.2f}".format,
                    "Temp SE": "{:.4f}".format,
                },
            )
        )
        if self.lines_printed:
            print(
                f"\033[{self.lines_printed}A",
                end="",
            )
            for _ in range(self.lines_printed):
                print("\033[2K")
            print(
                f"\033[{self.lines_printed}A",
                end="",
            )
        lines = table.splitlines()
        for line in lines:
            print(f"\033[2K{line}")
        terminal_width = get_terminal_size(fallback=(80, 24)).columns
        self.lines_printed = sum(
            max(
                1,
                (len(line) + terminal_width - 1) // terminal_width,
            )
            for line in lines
        )


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
