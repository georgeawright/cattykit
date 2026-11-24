"""Figure helpers for the Copycat reproduction."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import LogFormatterMathtext, LogLocator

from .paths import FIGURES, TEMPLATE_PATH

PUBLICATION_FONT = "DejaVu Serif"
SOLUTION_LABEL_FONT = "DejaVu Sans Mono"


def _format_problem_label(problem: str) -> str:
    """Use compact arrows for the analogy notation."""
    return problem.replace(" ==> ", " ⇒ ").replace(" -> ", " → ")


def _style_problem_labels(axis: plt.Axes) -> None:
    for label in axis.get_yticklabels():
        label.set_fontfamily(SOLUTION_LABEL_FONT)


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
    figure, axes = plt.subplots(
        1,
        3,
        figsize=(4.13, 5.84),
        sharey=True,
        gridspec_kw={"width_ratios": [1, 1, 1.2]},
    )
    for axis, column, x_label in zip(
        axes,
        ("frequency", "temperature", "codelets_run"),
        ("Frequency", "Final temperature", "Codelets run (log scale)"),
        strict=True,
    ):
        if column == "frequency":
            bars = axis.barh(positions, [row[column] for row in rows], color="black")
            maximum = max(row[column] for row in rows)
            axis.set_xlim(0, maximum * 1.18)
            for bar in bars:
                count = int(bar.get_width())
                axis.annotate(
                    str(count),
                    (count, bar.get_y() + bar.get_height() / 2),
                    xytext=(2, 0),
                    textcoords="offset points",
                    ha="left",
                    va="center",
                    color="black",
                    fontsize=3.5,
                    fontfamily=PUBLICATION_FONT,
                )
        else:
            axis.boxplot(
                [row[column] for row in rows],
                positions=positions,
                orientation="horizontal",
                patch_artist=True,
                boxprops={"facecolor": "0.85", "edgecolor": "black", "linewidth": 0.5},
                medianprops={"color": "black", "linewidth": 0.7},
                whiskerprops={"color": "black", "linewidth": 0.5},
                capprops={"color": "black", "linewidth": 0.5},
                flierprops={
                    "marker": ".",
                    "markersize": 1.5,
                    "markeredgecolor": "black",
                },
            )
            if column == "temperature":
                axis.set_xlim(0, 1)
            else:
                minimum = min(min(row[column]) for row in rows)
                if minimum <= 0:
                    raise ValueError("Codelet counts must be positive for a log scale.")
                axis.set_xscale("log")
                axis.set_xlim(minimum * 0.8, codelets_axis_maximum * 1.05)
                axis.xaxis.set_major_locator(LogLocator(base=10, numticks=10))
                axis.xaxis.set_major_formatter(LogFormatterMathtext(base=10))
        axis.set_ylim(len(rows) - 0.5, -0.5)
        axis.set_xlabel(x_label)
        _style_axis(axis)
        for boundary in boundaries:
            axis.axhline(boundary, color="0.5", linewidth=0.4)
    for axis in axes[1:]:
        axis.tick_params(axis="y", left=False, labelleft=False)
    axes[0].set_yticks(positions, labels=solution_labels)
    axes[0].set_ylabel("Answer")
    _style_solution_labels(axes[0])
    for centre, label in problem_labels:
        source, target = label.split(" ==> ", maxsplit=1)
        formatted_label = (
            source.replace(" -> ", " → ")
            + "\n⇒ "
            + target.removesuffix("?").replace(" -> ", " → ").rstrip()
        )
        axes[0].text(
            -0.48,
            centre,
            formatted_label,
            transform=axes[0].get_yaxis_transform(),
            ha="right",
            va="center",
            fontfamily=SOLUTION_LABEL_FONT,
            fontsize=4.5,
        )
    figure.subplots_adjust(left=0.22, right=0.98, bottom=0.05, top=0.98, wspace=0.28)
    figure.savefig(
        FIGURES / f"{filename_prefix}target_problems-combined.png",
        dpi=300,
        bbox_inches="tight",
        pad_inches=0.02,
    )
    plt.close(figure)


def _save_problem_snag_count_figure(
    all_runs_by_problem: list[tuple[str, str, list[dict[str, Any]]]],
    filename_prefix: str,
) -> None:
    """Save the per-run snag distributions in the existing box-plot style."""
    problems = [_format_problem_label(problem) for problem, _, _ in all_runs_by_problem]
    snag_counts = [
        [run["snag_count"] for run in runs] for _, _, runs in all_runs_by_problem
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
    _style_problem_labels(axis)
    figure.subplots_adjust(left=0.34, right=0.97, bottom=0.06, top=0.98)
    figure.savefig(
        FIGURES / f"{filename_prefix}all_problems-snag-count.png",
        dpi=300,
        bbox_inches="tight",
        pad_inches=0.02,
    )
    plt.close(figure)


def save_problem_5_xyd_scatter(raw_results_path: Path) -> None:
    """Plot codelets against snags for the ``xyd`` runs of template problem 5."""
    raw_results = pd.read_csv(raw_results_path)
    template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    problem = next(
        case["problem"] for case in template["results"] if str(case["id"]) == "5"
    )
    runs = raw_results.loc[
        (raw_results["problem"] == problem) & (raw_results["answer"] == "xyd")
    ]
    if runs.empty:
        raise ValueError(f"Raw results contain no xyd runs for problem 5: {problem!r}.")

    figure, axis = plt.subplots(figsize=(4.13, 3.0))
    figure.patch.set_facecolor("white")
    axis.scatter(
        runs["codelets_run"],
        runs["snag_count"],
        s=8,
        facecolors="white",
        edgecolors="black",
        linewidths=0.35,
    )
    axis.set(xlabel="Codelets run", ylabel="Snags encountered")
    axis.set_xlim(left=0)
    axis.set_ylim(bottom=0)
    axis.margins(x=0.04, y=0.08)
    _style_axis(axis)
    figure.subplots_adjust(left=0.18, right=0.96, bottom=0.18, top=0.96)
    figure.savefig(FIGURES / "problem_5_xyd-codelets-vs-snags.png", dpi=300)
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
