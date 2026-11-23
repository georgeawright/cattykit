"""Publication figures comparing the replication with published results."""

from __future__ import annotations

import json
from math import sqrt

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .figure_helpers import _format_problem_label, _style_axis, _style_problem_labels
from .paths import FIGURES, GOLD_PATH, REPLICATION_DATASETS


def save_comparison_figures() -> None:
    """Plot benchmark comparisons from saved results and seeded simulations."""
    original = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
    comparison = pd.read_csv(REPLICATION_DATASETS / "reproduction_comparison.csv")
    reference = pd.read_csv(
        REPLICATION_DATASETS / "reproduction_tv_monte_carlo_baseline.csv"
    )
    cases = original["results"]
    comparison = comparison.set_index("problem").loc[[c["problem"] for c in cases]]
    reference = reference.set_index("problem").loc[comparison.index]
    if reference["seed"].nunique() != 1 or reference["resamples"].nunique() != 1:
        raise ValueError("TV reference simulations must use one seed and sample count.")
    generator = np.random.default_rng(int(reference["seed"].iloc[0]))
    distances = []
    for case in cases:
        counts = np.array([v["frequency"] for v in case["solutions"].values()])
        n = int(counts.sum())
        simulations = int(reference.loc[case["problem"], "resamples"])
        first = generator.multinomial(n, counts / n, size=simulations)
        second = generator.multinomial(n, counts / n, size=simulations)
        distances.append(np.abs(first - second).sum(axis=1) / (2 * n))
    quantiles = np.array([np.quantile(values, [0.025, 0.975]) for values in distances])
    expected = reference[
        ["reference_tv_distance_lower_95", "reference_tv_distance_upper_95"]
    ].to_numpy()
    if not np.allclose(quantiles, expected):
        raise ValueError(
            "TV simulations do not match saved reference ranges; rerun stage 15."
        )
    positions = np.arange(len(cases))
    labels = [_format_problem_label(c["problem"]) for c in cases]
    fig, ax = plt.subplots(figsize=(4.13, 5.84))
    violin = ax.violinplot(
        distances,
        positions=positions,
        orientation="horizontal",
        widths=0.75,
        showextrema=False,
    )
    for body in violin["bodies"]:
        body.set_facecolor("0.8")
        body.set_edgecolor("none")
        body.set_alpha(0.8)
    ax.hlines(
        positions,
        reference["reference_tv_distance_lower_95"],
        reference["reference_tv_distance_upper_95"],
        color="black",
        linewidth=0.6,
        label="95% simulated range",
    )
    ax.scatter(
        comparison["solution_total_variation_distance"],
        positions,
        color="black",
        marker="D",
        s=5,
        zorder=3,
        label="Observed",
    )
    mean_tv = comparison["solution_total_variation_distance"].mean()
    ax.axvline(
        mean_tv,
        color="black",
        linestyle=":",
        linewidth=0.7,
        label=f"Mean observed: {mean_tv:.3f}",
    )
    ax.set_yticks(positions, labels=labels)
    ax.set_ylim(len(cases) - 0.5, -0.5)
    ax.set(xlabel="TV distance", ylabel="Problem")
    _style_axis(ax)
    _style_problem_labels(ax)
    ax.legend(frameon=False, fontsize=6, loc="lower right")
    fig.subplots_adjust(left=0.34, right=0.97, bottom=0.06, top=0.98)
    fig.savefig(
        FIGURES / "all_problems-tv-reference.png",
        dpi=300,
        bbox_inches="tight",
        pad_inches=0.02,
    )
    plt.close(fig)

    for name, error, score, error_label, score_label in (
        (
            "temperature",
            comparison["temperature_run_frequency_weighted_mean_absolute_error"],
            [
                sqrt(total / count) if count else np.nan
                for total, count in zip(
                    comparison["temperature_z_chi_square"],
                    comparison["temperature_z_count"],
                    strict=True,
                )
            ],
            "Frequency-weighted mean absolute temperature error",
            "Temperature RMS z",
        ),
        (
            "codelets",
            comparison["codelets_relative_error"],
            comparison["codelets_z_stat"],
            "Relative error in mean codelets run",
            "Signed z-score",
        ),
    ):
        fig, ax = plt.subplots(figsize=(4.13, 5.84))
        ax.scatter(error, positions, color="black", s=10)
        mean_error = error.mean()
        ax.axvline(
            mean_error,
            color="0.35",
            linestyle="--",
            linewidth=0.8,
            label=f"Mean across problems: {mean_error:.3f}",
        )
        ax.set_xlim(0, max(error.max() * 1.08, mean_error * 1.1))
        ax.set_yticks(positions, labels=labels)
        ax.tick_params(axis="y", labelleft=True)
        ax.set_ylim(len(cases) - 0.5, -0.5)
        ax.set(xlabel=error_label, ylabel="Problem")
        _style_axis(ax)
        _style_problem_labels(ax)
        for position, value in zip(positions, score, strict=True):
            label = (
                "n/a"
                if not np.isfinite(value)
                else f"{value:+.2f}"
                if name == "codelets"
                else f"{value:.2f}"
            )
            ax.text(
                1.04,
                position,
                label,
                transform=ax.get_yaxis_transform(),
                ha="left",
                va="center",
                fontsize=5,
                fontfamily="DejaVu Serif",
            )
        ax.text(
            1.04,
            1.01,
            score_label,
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=5,
            fontfamily="DejaVu Serif",
        )
        ax.legend(frameon=False, fontsize=5, loc="lower right")
        fig.subplots_adjust(left=0.34, right=0.85, bottom=0.06, top=0.97)
        fig.savefig(
            FIGURES / f"all_problems-{name}-comparison.png",
            dpi=300,
            bbox_inches="tight",
            pad_inches=0.02,
        )
        plt.close(fig)
