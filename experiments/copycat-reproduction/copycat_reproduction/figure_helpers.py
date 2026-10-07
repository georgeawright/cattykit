"""Figure helpers for the Copycat reproduction."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

from .paths import FIGURES, TEMPLATE_PATH

PUBLICATION_FONT = "DejaVu Serif"
SOLUTION_LABEL_FONT = "DejaVu Sans Mono"


def _style_axis(axis: plt.Axes) -> None:
    """Apply the original restrained black-and-white chart style."""
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
    """Use the original fixed-width, aligned solution labels."""
    for label in axis.get_yticklabels():
        label.set_fontfamily(SOLUTION_LABEL_FONT)
        label.set_fontsize(4.5)
        label.set_horizontalalignment("right")


def _save_combined_figures(
    basic_runs_by_problem: list[tuple[str, str, list[dict[str, Any]]]],
    solution_label_width: int,
    filename_prefix: str,
) -> None:
    """Save the original compact, single-page figure for each statistic."""
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
        figure.savefig(FIGURES / f"{filename_prefix}{filename}", dpi=300)
        plt.close(figure)


def _save_problem_snag_count_figure(
    all_runs_by_problem: list[tuple[str, str, list[dict[str, Any]]]],
    filename_prefix: str,
) -> None:
    """Save the per-run snag distributions in the existing box-plot style."""
    problems = [problem for problem, _, _ in all_runs_by_problem]
    snag_counts = [
        [run["snag_count"] for run in runs]
        for _, _, runs in all_runs_by_problem
    ]
    positions = list(range(len(problems)))
    figure, axis = plt.subplots(figsize=(4.13, 5.84))
    figure.patch.set_facecolor("white")
    axis.boxplot(
        snag_counts,
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
    axis.set_yticks(positions, labels=problems)
    axis.set_ylim(len(problems) - 0.5, -0.5)
    axis.set(xlabel="Snags per run", ylabel="Problem")
    _style_axis(axis)
    figure.subplots_adjust(left=0.30, right=0.96, bottom=0.24, top=0.94)
    figure.savefig(
        FIGURES / f"{filename_prefix}all_problems-snag-count.png", dpi=300
    )
    plt.close(figure)


def save_basic_problem_figures(
    raw_results_path: Path, *, filename_prefix: str = ""
) -> None:
    """Regenerate the original figures from saved per-run results."""
    raw_results = pd.read_csv(raw_results_path)
    required_columns = {
        "problem",
        "random_seed",
        "answer",
        "temperature",
        "codelets_run",
        "snag_count",
    }
    missing_columns = required_columns.difference(raw_results.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Raw results CSV is missing required columns: {missing}.")

    template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    basic_runs_by_problem: list[tuple[str, str, list[dict[str, Any]]]] = []
    all_runs_by_problem: list[tuple[str, str, list[dict[str, Any]]]] = []
    basic_problems = set(template["basic_problems"])
    for case in template["results"]:
        problem = case["problem"]
        problem_results = raw_results.loc[raw_results["problem"] == problem]
        if problem_results.empty:
            raise ValueError(f"Raw results CSV has no runs for {problem!r}.")
        runs = [
            {
                "solution": row.answer,
                "temperature": row.temperature,
                "codelets_run": row.codelets_run,
                "snag_count": row.snag_count,
            }
            for row in problem_results.itertuples(index=False)
        ]
        all_runs_by_problem.append((problem, str(case["id"]), runs))
        if problem in basic_problems:
            basic_runs_by_problem.append((problem, str(case["id"]), runs))
    solution_label_width = max(
        len(str(run["solution"]))
        for _, _, basic_runs in basic_runs_by_problem
        for run in basic_runs
    )
    FIGURES.mkdir(parents=True, exist_ok=True)
    _save_combined_figures(basic_runs_by_problem, solution_label_width, filename_prefix)
    _save_problem_snag_count_figure(all_runs_by_problem, filename_prefix)
