from __future__ import annotations

import argparse
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
from cattykit.experiments import summarize_runs, total_variation_distance
from cattykit.models import load_model

ROOT = Path(__file__).resolve().parents[2]
DATASETS = ROOT / "datasets" / "copycat"
FIGURES = ROOT / "papers" / "copycat-reproduction" / "figures"
TEMPLATE_PATH = DATASETS / "original_copycat_results.template.json"
DEFAULT_GOLD_PATH = DATASETS / "original_copycat_results.json"
RESULTS_PATH = DATASETS / "reproduction_copycat_results.json"
RAW_RESULTS_PATH = DATASETS / "reproduction_raw_results.csv"
COMPARISON_CSV_PATH = DATASETS / "reproduction_comparison.csv"
ERROR_SUMMARY_CSV_PATH = DATASETS / "reproduction_comparison_error_summary.csv"
COMPARISON_MARKDOWN_PATH = FIGURES / "reproduction_comparison.md"
SOLUTION_SUMMARY_MARKDOWN_PATH = FIGURES / "reproduction_solution_summary.md"
PUBLICATION_FONT = "DejaVu Serif"
SOLUTION_LABEL_FONT = "DejaVu Sans Mono"
MIN_ORIGINAL_SOLUTION_FREQUENCY = 10


def _runs_for_problem(problem: str, iterations: int) -> list[dict[str, Any]]:
    """Return the individual runs required for distribution plots.

    This mirrors ``cattykit.experiments.run_experiment`` so seeds and reported
    metrics stay consistent with normal Cattykit experiments.
    """
    runs: list[dict[str, Any]] = []
    for seed in range(iterations):
        model = load_model("copycat", config={"seed": seed})
        try:
            runs.append(
                {
                    "random_seed": seed,
                    "solution": model.solve(problem),
                    "codelets_run": model.coderack.number_of_codelets_run,
                    "temperature": model.temperature,
                }
            )
        finally:
            model.close()
    return runs


def _save_figures_from_raw_results(raw_results_path: Path) -> None:
    """Regenerate the combined figures from per-run results without solving."""
    raw_results = pd.read_csv(raw_results_path)
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
    problem_number_by_problem = {
        case["problem"]: number
        for number, case in enumerate(template["results"], start=1)
    }
    basic_runs_by_problem: list[tuple[str, int, list[dict[str, Any]]]] = []
    for problem in template["basic_problems"]:
        problem_results = raw_results.loc[raw_results["problem"] == problem]
        if problem_results.empty:
            raise ValueError(f"Raw results CSV has no runs for {problem!r}.")
        runs = [
            {
                "solution": row.answer,
                "temperature": row.temperature,
                "codelets_run": row.codelets_run,
            }
            for row in problem_results.itertuples(index=False)
        ]
        basic_runs_by_problem.append(
            (problem, problem_number_by_problem[problem], runs)
        )
    solution_label_width = max(
        len(str(run["solution"]))
        for _, _, basic_runs in basic_runs_by_problem
        for run in basic_runs
    )
    _save_combined_figures(basic_runs_by_problem, solution_label_width)


def _reproduction_from_raw_results(raw_results_path: Path) -> dict[str, Any]:
    """Rebuild the summary-results JSON from a per-run results CSV."""
    raw_results = pd.read_csv(raw_results_path)
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
        problem = case["problem"]
        problem_results = raw_results.loc[raw_results["problem"] == problem]
        if problem_results.empty:
            raise ValueError(f"Raw results CSV has no runs for {problem!r}.")
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
            _result_case(
                problem,
                summarize_runs(runs, problem),
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


def _style_axis(axis: plt.Axes) -> None:
    """Apply a restrained black-and-white, publication-ready chart style."""
    axis.set_facecolor("white")
    axis.grid(axis="x", color="0.8", linewidth=0.25)
    axis.set_axisbelow(True)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.spines["left"].set_color("black")
    axis.spines["bottom"].set_color("black")
    axis.spines["left"].set_linewidth(0.4)
    axis.spines["bottom"].set_linewidth(0.4)
    axis.tick_params(colors="black", width=0.4, length=3)
    axis.title.set_fontfamily(PUBLICATION_FONT)
    axis.title.set_fontsize(5.5)
    axis.title.set_fontweight("normal")
    axis.xaxis.label.set_fontfamily(PUBLICATION_FONT)
    axis.yaxis.label.set_fontfamily(PUBLICATION_FONT)
    axis.xaxis.label.set_fontsize(5)
    axis.yaxis.label.set_fontsize(5)
    for label in [*axis.get_xticklabels(), *axis.get_yticklabels()]:
        label.set_fontfamily(PUBLICATION_FONT)
        label.set_fontsize(4.5)


def _style_solution_labels(axis: plt.Axes) -> None:
    """Use a fixed-width face for aligned analogy-solution labels."""
    for label in axis.get_yticklabels():
        label.set_fontfamily(SOLUTION_LABEL_FONT)
        label.set_fontsize(4.5)
        label.set_horizontalalignment("right")


def _save_combined_figures(
    basic_runs_by_problem: list[tuple[str, int, list[dict[str, Any]]]],
    solution_label_width: int,
) -> None:
    """Save one compact, single-page figure for each statistic."""
    rows: list[dict[str, Any]] = []
    boundaries: list[int] = []
    problem_labels: list[tuple[float, str]] = []
    for problem, _problem_number, runs in basic_runs_by_problem:
        frame = pd.DataFrame(runs)
        solution_order = frame["solution"].value_counts(sort=True).index.tolist()
        start = len(rows)
        for solution in solution_order:
            solution_runs = frame.loc[frame["solution"] == solution]
            rows.append(
                {
                    "solution": str(solution),
                    "frequency": len(solution_runs),
                    "temperature": solution_runs["temperature"].to_numpy(),
                    "codelets_run": solution_runs["codelets_run"].to_numpy(),
                }
            )
        if start:
            boundaries.append(start - 0.5)
        problem_labels.append(((start + len(rows) - 1) / 2, problem))

    positions = list(range(len(rows)))
    solution_labels = [f"{row['solution']:>{solution_label_width}}" for row in rows]
    codelets_axis_maximum = max(
        10_000,
        ((max(max(row["codelets_run"]) for row in rows) + 999) // 1_000) * 1_000,
    )
    for column, x_label, filename, xlim in (
        ("frequency", "Frequency", "target_problems-solution-frequency.png", None),
        (
            "temperature",
            "Final temperature",
            "target_problems-temperature-by-solution.png",
            (0.0, 1.0),
        ),
        (
            "codelets_run",
            "Codelets run",
            "target_problems-codelets-run-by-solution.png",
            (0.0, float(codelets_axis_maximum)),
        ),
    ):
        figure, axis = plt.subplots(figsize=(4.13, 5.84))
        figure.patch.set_facecolor("white")
        if column == "frequency":
            bars = axis.barh(
                positions,
                [row[column] for row in rows],
                color="black",
                edgecolor="black",
                linewidth=0.35,
            )
            for text in axis.bar_label(bars, padding=1, fmt="%d"):
                text.set_fontfamily(PUBLICATION_FONT)
                text.set_fontsize(3.5)
            axis.margins(x=0.08)
        else:
            axis.boxplot(
                [row[column] for row in rows],
                positions=positions,
                orientation="horizontal",
                patch_artist=True,
                boxprops={"facecolor": "0.85", "edgecolor": "black", "linewidth": 0.45},
                medianprops={"color": "black", "linewidth": 0.6},
                whiskerprops={"color": "black", "linewidth": 0.45},
                capprops={"color": "black", "linewidth": 0.45},
                flierprops={
                    "marker": "o",
                    "markerfacecolor": "white",
                    "markeredgecolor": "black",
                    "markeredgewidth": 0.4,
                    "markersize": 2,
                },
            )
            axis.set_xlim(xlim)
        axis.set_ylim(len(rows) - 0.5, -0.5)
        axis.set_yticks(positions, labels=solution_labels)
        axis.set(xlabel=x_label, ylabel="Answer")
        _style_axis(axis)
        _style_solution_labels(axis)
        for label in axis.get_yticklabels():
            label.set_fontsize(3.5)
        for boundary in boundaries:
            axis.axhline(boundary, color="black", linewidth=0.35)
        for centre, label in problem_labels:
            axis.text(
                -0.38,
                centre,
                label,
                transform=axis.get_yaxis_transform(),
                ha="left",
                va="center",
                fontfamily=SOLUTION_LABEL_FONT,
                fontsize=3.5,
                clip_on=False,
            )
        figure.subplots_adjust(left=0.30, right=0.96, bottom=0.07, top=0.98)
        figure.savefig(FIGURES / filename, dpi=300)
        plt.close(figure)


def _result_case(
    problem: str,
    summary: pd.DataFrame,
    source: dict[str, Any],
    problem_id: str,
) -> dict[str, Any]:
    """Convert a Cattykit summary into the published Copycat JSON schema."""
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


def _absolute_error_statistics(
    observed: Iterable[float], expected: Iterable[float]
) -> dict[str, float]:
    """Return absolute-error summary statistics."""
    pairs = list(zip(observed, expected, strict=True))
    absolute = [abs(actual - reference) for actual, reference in pairs]
    return {
        "mean_absolute_error": sum(absolute) / len(absolute) if absolute else 0.0,
        "max_absolute_error": max(absolute, default=0.0),
        **_error_quantiles(absolute, "absolute_error"),
    }


def _relative_error(observed: float, expected: float) -> float:
    """Return the relative error for one problem-wide measurement."""
    return abs(observed - expected) / abs(expected) if expected else 0.0


def _error_quantiles(values: list[float], suffix: str) -> dict[str, float]:
    """Return every decile of one problem's error distribution."""
    series = pd.Series(values, dtype=float)
    return {
        f"quantile_{percentile}_{suffix}": (
            float(series.quantile(percentile / 100)) if not series.empty else 0.0
        )
        for percentile in range(10, 101, 10)
    }


def _comparison_table(
    reproduction: dict[str, Any], original: dict[str, Any]
) -> pd.DataFrame:
    """Compare solution frequencies, temperatures, and total codelets by problem."""
    original_cases = {case["problem"]: case for case in original["results"]}
    rows: list[dict[str, Any]] = []
    for reproduced in reproduction["results"]:
        problem = reproduced["problem"]
        gold = original_cases.get(problem)
        if gold is None:
            raise ValueError(f"Original dataset has no result for {problem!r}.")
        gold_solutions = gold["solutions"]
        if not gold_solutions or gold["codelets"]["mean"] is None:
            raise ValueError(
                f"Original dataset has incomplete numerical data for {problem!r}."
            )
        observed_solutions = reproduced["solutions"]
        most_frequent_answer, most_frequent_result = max(
            observed_solutions.items(), key=lambda item: item[1]["frequency"]
        )
        lowest_temperature_solution, lowest_temperature_result = min(
            observed_solutions.items(),
            key=lambda item: item[1]["temperature_mean"],
        )
        temperature_pairs = [
            (
                observed_solutions[solution]["temperature_mean"],
                values["temperature_mean"],
            )
            for solution, values in gold_solutions.items()
            if (
                solution in observed_solutions
                and values["frequency"] >= MIN_ORIGINAL_SOLUTION_FREQUENCY
            )
        ]
        if temperature_pairs:
            observed_temperatures, expected_temperatures = zip(
                *temperature_pairs, strict=True
            )
            # Temperature is bounded on [0, 1], so absolute error is directly
            # interpretable in the model's fixed, meaningful scale.
            temperature = _absolute_error_statistics(
                observed_temperatures, expected_temperatures
            )
        else:
            temperature = _absolute_error_statistics([], [])
        # Codelets run has no natural upper limit, so relative error is the
        # meaningful comparison across problems with different run lengths.
        # There is one problem-wide codelets mean, hence one relative error.
        codelets_relative_error = _relative_error(
            reproduced["codelets"]["mean"], gold["codelets"]["mean"]
        )
        rows.append(
            {
                "id": gold["id"],
                "problem": problem,
                "most_frequent_answer": most_frequent_answer,
                "most_frequent_answer_frequency": most_frequent_result["frequency"],
                "most_frequent_answer_temperature_mean": (
                    most_frequent_result["temperature_mean"]
                ),
                "most_frequent_answer_temperature_standard_error": (
                    most_frequent_result["temperature_standard_error"]
                ),
                "lowest_temperature_solution": lowest_temperature_solution,
                "lowest_temperature_solution_frequency": (
                    lowest_temperature_result["frequency"]
                ),
                "lowest_temperature_solution_temperature_mean": (
                    lowest_temperature_result["temperature_mean"]
                ),
                "lowest_temperature_solution_temperature_standard_error": (
                    lowest_temperature_result["temperature_standard_error"]
                ),
                "mean_codelets_run": reproduced["codelets"]["mean"],
                "codelets_run_standard_error": reproduced["codelets"]["standard_error"],
                "solution_total_variation_distance": total_variation_distance(
                    {
                        key: value["frequency"]
                        for key, value in observed_solutions.items()
                    },
                    {key: value["frequency"] for key, value in gold_solutions.items()},
                ),
                **{f"temperature_{key}": value for key, value in temperature.items()},
                "codelets_relative_error": codelets_relative_error,
            }
        )
    comparison = pd.DataFrame(rows)
    comparison["_id_sort_key"] = comparison["id"].map(_id_sort_key)
    return comparison.sort_values("_id_sort_key", kind="stable").drop(
        columns="_id_sort_key"
    )


def _id_sort_key(problem_id: str) -> tuple[int, ...]:
    """Sort integer and decimal Copycat IDs in their numeric hierarchy."""
    return tuple(int(part) for part in problem_id.split("."))


def _grouped_markdown(table: pd.DataFrame) -> str:
    """Render one table with indented variations and family divider rows."""
    display = table.copy()
    display["id"] = display["id"].map(
        lambda problem_id: (
            f"&nbsp;&nbsp;{problem_id}" if "." in problem_id else problem_id
        )
    )
    display = _format_markdown_numbers(display).rename(
        columns={column: _markdown_column_title(column) for column in display.columns}
    )
    headings = list(display.columns)
    right_aligned = {
        number
        for number, column in enumerate(table.columns)
        if pd.api.types.is_numeric_dtype(table[column])
    }
    lines = [_markdown_row(headings), _markdown_separator(headings, right_aligned)]
    for row_number, row in enumerate(display.itertuples(index=False, name=None)):
        if "." not in table.iloc[row_number]["id"] and row_number:
            lines.append(_markdown_row([""] * len(headings)))
        lines.append(_markdown_row([str(value) for value in row]))
    return "\n".join(lines) + "\n"


def _solution_summary_markdown(comparison: pd.DataFrame) -> str:
    """Render the per-problem and per-solution summary table for the paper."""
    headings = [
        "ID",
        "Problem",
        "Mean Codelets",
        "Codelets SE",
        "Modal Answer",
        "Freq.",
        "Mean Temp.",
        "Temp. SE",
    ]
    rows = [_solution_summary_row(row) for row in comparison.itertuples(index=False)]
    right_aligned = {2, 3, 5, 6, 7}
    lines = [
        _markdown_row(headings),
        _markdown_separator(headings, right_aligned),
        *(_markdown_row(row) for row in rows),
    ]
    return "# Solution Summary\n\n" + "\n".join(lines) + "\n"


def _solution_summary_row(row: Any) -> list[str]:
    """Return one solution-summary table row with duplicated run-level metrics."""
    problem_id = f"&nbsp;&nbsp;{row.id}" if "." in row.id else row.id
    codelets_mean = _format_markdown_zero_decimal(row.mean_codelets_run)
    codelets_error = _format_markdown_one_decimal(row.codelets_run_standard_error)
    return [
        problem_id,
        row.problem,
        codelets_mean,
        codelets_error,
        row.most_frequent_answer,
        _format_markdown_integer(row.most_frequent_answer_frequency),
        _format_markdown_number(row.most_frequent_answer_temperature_mean),
        _format_markdown_number(row.most_frequent_answer_temperature_standard_error),
    ]


def _markdown_row(values: list[str]) -> str:
    """Return one safely escaped GitHub-flavored Markdown table row."""
    return "| " + " | ".join(value.replace("|", "\\|") for value in values) + " |"


def _markdown_separator(values: list[str], right_aligned: set[int]) -> str:
    """Return a Markdown table separator with numeric columns right aligned."""
    return _markdown_row(
        ["---:" if number in right_aligned else ":---" for number in range(len(values))]
    )


def _markdown_column_title(column: str) -> str:
    """Use readable title-case headings in generic Markdown tables."""
    titles = {
        "id": "ID",
        "solution_total_variation_distance": "Answer TV Distance",
        "temperature_mean_absolute_error": "Temp. mean absolute error",
        "temperature_max_absolute_error": "Temp. max absolute error",
        "codelets_relative_error": "Codelets-Run Relative Error",
    }
    return titles.get(column, column.replace("_", " ").title())


def _comparison_statistics_markdown(
    comparison: pd.DataFrame, error_summary: pd.DataFrame
) -> str:
    """Render per-problem similarity statistics plus one aggregate row."""
    columns = [
        "id",
        "problem",
        "solution_total_variation_distance",
        "temperature_mean_absolute_error",
        "temperature_max_absolute_error",
        "codelets_relative_error",
    ]
    display = comparison[columns].copy()
    summary = error_summary.set_index("error_metric")
    display.loc[len(display)] = {
        "id": "Summary",
        "problem": "Across problems",
        # TV distance is averaged unweighted: each target problem contributes
        # equally, rather than problems with more distinct answers dominating.
        "solution_total_variation_distance": comparison[
            "solution_total_variation_distance"
        ].mean(),
        "temperature_mean_absolute_error": comparison[
            "temperature_mean_absolute_error"
        ].mean(),
        # This is the largest retained-answer discrepancy in the entire
        # reproduction, rather than the mean of the per-problem maxima.
        "temperature_max_absolute_error": comparison[
            "temperature_max_absolute_error"
        ].max(),
        "codelets_relative_error": summary.loc[
            "Codelets-run relative error", "mean_error"
        ],
    }
    return "# Comparison statistics\n\n" + _grouped_markdown(display)


def _error_summary(comparison: pd.DataFrame) -> pd.DataFrame:
    """Summarize the scale-appropriate error from every target problem."""
    metrics = {
        "Temperature mean absolute error": comparison[
            "temperature_mean_absolute_error"
        ],
        "Temperature max absolute error": comparison[
            "temperature_max_absolute_error"
        ],
        "Codelets-run relative error": comparison["codelets_relative_error"],
    }
    rows = []
    for metric, values in metrics.items():
        rows.append(
            {
                "error_metric": metric,
                "mean_error": values.mean(),
                "max_error": values.max(),
                **{
                    f"quantile_{percentile}": values.quantile(percentile / 100)
                    for percentile in range(10, 101, 10)
                },
            }
        )
    return pd.DataFrame(rows)


def _format_markdown_numbers(table: pd.DataFrame) -> pd.DataFrame:
    """Return a display copy with all numeric values at three decimal places."""
    display = table.copy()
    for column in display.select_dtypes(include="number"):
        display[column] = display[column].map(_format_markdown_number)
    return display


def _format_markdown_number(value: float | int) -> str:
    """Format a numeric paper-table value with three decimal places."""
    return "" if pd.isna(value) else f"{value:.3f}"


def _format_markdown_integer(value: float | int) -> str:
    """Format an exact frequency count without decimal places."""
    return "" if pd.isna(value) else str(int(value))


def _format_markdown_one_decimal(value: float | int) -> str:
    """Format codelets-run standard errors to one decimal place."""
    return "" if pd.isna(value) else f"{value:.1f}"


def _format_markdown_zero_decimal(value: float | int) -> str:
    """Round a measured value to zero decimal places."""
    return "" if pd.isna(value) else f"{value:.0f}"


def main(
    iterations: int = 1000,
    gold_path: Path = DEFAULT_GOLD_PATH,
    raw_results_path: Path | None = None,
) -> None:
    """Run experiments, or reuse results, then write reproducibility artifacts."""
    if iterations < 1:
        raise ValueError("iterations must be at least 1")
    DATASETS.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    if raw_results_path is not None:
        print(f"Rebuilding results from raw runs in {raw_results_path}")
        reproduction = _reproduction_from_raw_results(raw_results_path)
        _save_figures_from_raw_results(raw_results_path)
        RESULTS_PATH.write_text(
            json.dumps(reproduction, indent=2) + "\n", encoding="utf-8"
        )
    else:
        template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
        basic_problems = template["basic_problems"]
        basic_problem_set = set(basic_problems)
        case_by_problem = {case["problem"]: case for case in template["results"]}
        problem_number_by_problem = {
            case["problem"]: number
            for number, case in enumerate(template["results"], start=1)
        }

        reproduced_cases = []
        raw_result_rows: list[dict[str, Any]] = []
        basic_runs_by_problem: list[tuple[str, int, list[dict[str, Any]]]] = []
        for i, problem in enumerate(
            (case["problem"] for case in template["results"])
        ):
            print(f"Running {i} {problem} ({iterations} seeds)")
            runs = _runs_for_problem(problem, iterations)
            raw_result_rows.extend(
                {
                    "problem": problem,
                    "random_seed": run["random_seed"],
                    "answer": run["solution"],
                    "temperature": run["temperature"],
                    "codelets_run": run["codelets_run"],
                }
                for run in runs
            )
            summary = summarize_runs(runs, problem)
            reproduced_cases.append(
                _result_case(
                    problem,
                    summary,
                    case_by_problem[problem]["source"],
                    case_by_problem[problem]["id"],
                )
            )
            if problem in basic_problem_set:
                basic_runs_by_problem.append(
                    (problem, problem_number_by_problem[problem], runs)
                )
                if len(basic_runs_by_problem) == len(basic_problems):
                    solution_label_width = max(
                        len(str(run["solution"]))
                        for _, _, basic_runs in basic_runs_by_problem
                        for run in basic_runs
                    )
                    _save_combined_figures(
                        basic_runs_by_problem, solution_label_width
                    )

        reproduction = {
            "schema_version": template["schema_version"],
            "source_work": template["source_work"],
            "basic_problems": basic_problems,
            "results": reproduced_cases,
        }
        RESULTS_PATH.write_text(
            json.dumps(reproduction, indent=2) + "\n", encoding="utf-8"
        )
        pd.DataFrame(
            raw_result_rows,
            columns=[
                "problem",
                "random_seed",
                "answer",
                "temperature",
                "codelets_run",
            ],
        ).to_csv(RAW_RESULTS_PATH, index=False)
    if gold_path.is_file():
        original = json.loads(gold_path.read_text(encoding="utf-8"))
        comparison = _comparison_table(reproduction, original)
        error_summary = _error_summary(comparison)
        comparison.to_csv(COMPARISON_CSV_PATH, index=False)
        error_summary.to_csv(ERROR_SUMMARY_CSV_PATH, index=False)
        COMPARISON_MARKDOWN_PATH.write_text(
            _comparison_statistics_markdown(comparison, error_summary),
            encoding="utf-8",
        )
        SOLUTION_SUMMARY_MARKDOWN_PATH.write_text(
            _solution_summary_markdown(comparison), encoding="utf-8"
        )
    else:
        print(f"No original dataset at {gold_path}; skipped comparison table.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=1000)
    parser.add_argument("--gold-path", type=Path, default=DEFAULT_GOLD_PATH)
    parser.add_argument(
        "--raw-results-path",
        type=Path,
        help="Rebuild all artifacts from this per-run CSV without solving.",
    )
    arguments = parser.parse_args()
    main(
        arguments.iterations,
        arguments.gold_path,
        arguments.raw_results_path,
    )
