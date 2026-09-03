from __future__ import annotations

import html
import math

import pandas as pd
import panel as pn
from bokeh.models import ColumnDataSource, FactorRange, FixedTicker, LabelSet, Range1d
from bokeh.plotting import figure

from .charts import _solution_codelets_chart, _solution_temperature_chart


def _run_group_table(
    runs: pd.DataFrame, columns: list[str], *, collapsed: bool = True
) -> pn.pane.HTML:
    """Render one model/problem run group, optionally in a details element."""
    headers = "<th>View</th>" + "".join(
        f"<th>{html.escape(column)}</th>" for column in columns
    )
    body = "".join(
        "<tr>"
        + f'<td><a href="?run_id={int(row[columns.index("id")])}">View</a></td>'
        + "".join(
            (
                f'<td><a href="?run_id={int(value)}">{int(value)}</a></td>'
                if column == "id"
                else f"<td>{html.escape('' if value is None else str(value))}</td>"
            )
            for column, value in zip(columns, row, strict=True)
        )
        + "</tr>"
        for row in runs.itertuples(index=False, name=None)
    )
    count = len(runs)
    table = f"<table><thead><tr>{headers}</tr></thead><tbody>{body}</tbody></table>"
    content = (
        "<details>"
        f"<summary>Show {count} run{'s' if count != 1 else ''}</summary>"
        f"{table}</details>"
        if collapsed
        else table
    )
    return pn.pane.HTML(
        content,
        sizing_mode="stretch_width",
    )


def _problem_overview(model: str, problem: str, runs: pd.DataFrame) -> pn.Column:
    """Build the aggregate view for one model/problem pair."""
    codelets = pd.to_numeric(runs["number_of_codelets_run"], errors="coerce")
    codelets_mean = codelets.mean()
    codelets_stderr = codelets.std() / math.sqrt(len(codelets))
    temperatures = pd.to_numeric(runs["final_temperature"], errors="coerce")
    temperatures_mean = temperatures.mean()
    temperatures_stderr = temperatures.std() / math.sqrt(len(temperatures))
    solution_runs = runs.assign(solution=runs["solution"].fillna("—")).copy()
    solution_summary = (
        solution_runs.groupby("solution", sort=True)
        .agg(
            frequency=("solution", "size"),
            mean_temperature=("final_temperature", "mean"),
            mean_codelets=("number_of_codelets_run", "mean"),
        )
        .reset_index()
        .sort_values(["frequency", "solution"], ascending=[False, True])
    )
    most_common_solution = solution_summary.loc[
        solution_summary["frequency"].idxmax(), "solution"
    ]
    measured_temperatures = temperatures.dropna()
    lowest_temperature_solution = (
        solution_runs.loc[measured_temperatures.idxmin(), "solution"]
        if not measured_temperatures.empty
        else "—"
    )
    snags = pd.to_numeric(runs["number_of_snags"], errors="coerce")
    snags_mean = snags.mean()
    snags_stderr = snags.std() / math.sqrt(len(snags))

    def statistic(value: float) -> str:
        return "—" if pd.isna(value) else f"{value:.2f}"

    statistics = pn.pane.HTML(
        "<ul>"
        f"<li>Number of runs: {len(runs)}</li>"
        f"<li>Codelets run: mean {statistic(codelets_mean)}, standard error {statistic(codelets_stderr)}</li>"
        f"<li>Final temperature: mean {statistic(temperatures_mean)}, stdev {statistic(temperatures_stderr)}</li>"
        f"<li>Most common solution: {html.escape(str(most_common_solution))}</li>"
        f"<li>Solution with lowest temperature: {html.escape(str(lowest_temperature_solution))}</li>"
        f"<li>Snags: mean {statistic(snags_mean)}, stdev {statistic(snags_stderr)}</li>"
        "</ul>"
    )
    source = ColumnDataSource(
        {
            "solution": solution_summary["solution"].astype(str).tolist(),
            "frequency": solution_summary["frequency"].tolist(),
            "label": [str(frequency) for frequency in solution_summary["frequency"]],
        }
    )
    solution_count = len(solution_summary)
    total_frequency = sum(source.data["frequency"])
    padding_factors = ["\u00a0" * (index + 1) for index in range(10 - solution_count)]
    chart = figure(
        title=f"{str(model).capitalize()} Solution frequency for problem {problem}",
        x_range=FactorRange(*source.data["solution"], *padding_factors),
        y_range=Range1d(0, total_frequency * 1.08),
        x_axis_label="Solution",
        y_axis_label="Runs",
        height=360,
        sizing_mode="stretch_width",
        toolbar_location=None,
    )
    chart.vbar(x="solution", top="frequency", width=0.8, source=source, color="#5b7db1")
    chart.add_layout(
        LabelSet(
            x="solution",
            y="frequency",
            text="label",
            y_offset=8,
            text_align="center",
            text_baseline="bottom",
            text_font_size="9px",
            source=source,
        )
    )
    target_y_tick_step = total_frequency / 4
    magnitude = 10 ** math.floor(math.log10(target_y_tick_step))
    normalized_step = target_y_tick_step / magnitude
    y_tick_step = max(
        1,
        int(
            next(
                multiplier * magnitude
                for multiplier in (1, 2, 5, 10)
                if normalized_step <= multiplier
            )
        ),
    )
    y_ticks = list(range(0, total_frequency + 1, y_tick_step))
    if y_ticks[-1] != total_frequency:
        y_ticks.append(total_frequency)
    chart.yaxis.ticker = FixedTicker(ticks=y_ticks)
    chart.xaxis.major_label_orientation = 0
    chart.background_fill_color = "white"
    chart.grid.grid_line_color = None
    codelet_chart = _solution_codelets_chart(
        model, problem, solution_runs, source.data["solution"], padding_factors
    )
    temperature_chart = _solution_temperature_chart(
        model, problem, solution_runs, source.data["solution"], padding_factors
    )
    return pn.Column(
        f"## Runs of {model} on problem {problem}",
        statistics,
        chart,
        codelet_chart,
        temperature_chart,
        "### Runs",
        _run_group_table(runs, list(runs.columns), collapsed=False),
        sizing_mode="stretch_width",
    )
