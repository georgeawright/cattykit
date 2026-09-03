from __future__ import annotations

import math
from typing import Any

import pandas as pd
import panel as pn
from bokeh.models import (
    BoxAnnotation,
    ColumnDataSource,
    FactorRange,
    Label,
    LabelSet,
    Range1d,
    Span,
)
from bokeh.plotting import figure
from bokeh.transform import jitter


def _solution_metric_boxplot_chart(
    model: str,
    problem: str,
    solution_runs: pd.DataFrame,
    solutions: list[str],
    padding_factors: list[str],
    *,
    value_column: str,
    value_label: str,
    title_metric: str | None = None,
    empty_message: str | None = None,
) -> pn.viewable.Viewable:
    """Plot per-run values and boxplots for a numeric metric, grouped by solution."""
    if value_column not in solution_runs.columns:
        return pn.pane.Alert(
            f"No {value_label.lower()} data was logged.", alert_type="info"
        )

    value_key = "value"
    runs = solution_runs.assign(
        **{value_key: pd.to_numeric(solution_runs[value_column], errors="coerce")}
    ).dropna(subset=[value_key])

    if runs.empty:
        return pn.pane.Alert(
            empty_message or f"No {value_label.lower()} data was logged.",
            alert_type="info",
        )

    boxplot_rows = []
    for solution in solutions:
        values = runs.loc[runs["solution"] == solution, value_key]
        if values.empty:
            continue

        q1, median, q3 = values.quantile([0.25, 0.5, 0.75])
        iqr = q3 - q1
        lower = values[values >= q1 - 1.5 * iqr].min()
        upper = values[values <= q3 + 1.5 * iqr].max()
        standard_error = values.std() / math.sqrt(values.count())

        boxplot_rows.append(
            {
                "solution": solution,
                "q1": q1,
                "median": median,
                "q3": q3,
                "lower": lower,
                "upper": upper,
                "label_y": upper,
                "label": (
                    f"mean {values.mean():.2f}, std error "
                    f"{'—' if pd.isna(standard_error) else f'{standard_error:.2f}'}"
                ),
            }
        )

    if not boxplot_rows:
        return pn.pane.Alert(
            empty_message or f"No {value_label.lower()} data was logged.",
            alert_type="info",
        )

    boxes = ColumnDataSource(pd.DataFrame(boxplot_rows))

    maximum = max(runs[value_key].max(), max(boxes.data["upper"]))
    minimum = min(runs[value_key].min(), min(boxes.data["lower"]))
    padding = max((maximum - minimum) * 0.1, abs(maximum) * 0.05, 1.0)

    chart = figure(
        title=(
            f"{str(model).capitalize()} "
            f"{title_metric or value_label} by solution for problem {problem}"
        ),
        x_range=FactorRange(*solutions, *padding_factors),
        y_range=Range1d(min(0, minimum - padding), maximum + padding),
        x_axis_label="Solution",
        y_axis_label=value_label,
        height=360,
        sizing_mode="stretch_width",
        toolbar_location=None,
    )

    point_source = ColumnDataSource(
        {
            "solution": runs["solution"].astype(str).tolist(),
            value_key: runs[value_key].tolist(),
        }
    )

    chart.scatter(
        x=jitter("solution", width=0.36, range=chart.x_range),
        y=value_key,
        source=point_source,
        size=7,
        fill_color="#1E88E5",
        fill_alpha=0.65,
        line_color=None,
    )

    chart.segment(
        x0="solution",
        y0="lower",
        x1="solution",
        y1="upper",
        source=boxes,
        line_color="#374151",
    )

    chart.vbar(
        x="solution",
        bottom="q1",
        top="q3",
        width=0.48,
        source=boxes,
        fill_color="#c7d2fe",
        fill_alpha=0.65,
        line_color="#374151",
    )

    chart.scatter(
        x="solution",
        y="median",
        source=boxes,
        marker="dash",
        size=20,
        line_width=2,
        line_color="#111827",
    )

    chart.add_layout(
        LabelSet(
            x="solution",
            y="label_y",
            text="label",
            y_offset=8,
            text_align="center",
            text_baseline="bottom",
            text_font_size="9px",
            source=boxes,
        )
    )

    chart.xaxis.major_label_orientation = 0
    chart.background_fill_color = "white"
    chart.grid.grid_line_color = None
    return chart


def _solution_codelets_chart(
    model: str,
    problem: str,
    solution_runs: pd.DataFrame,
    solutions: list[str],
    padding_factors: list[str],
) -> pn.viewable.Viewable:
    """Plot codelets run by solution using the generic metric boxplot."""
    return _solution_metric_boxplot_chart(
        model,
        problem,
        solution_runs,
        solutions,
        padding_factors,
        value_column="number_of_codelets_run",
        value_label="Codelets run",
        empty_message="No codelet-run data was logged.",
    )


def _solution_temperature_chart(
    model: str,
    problem: str,
    solution_runs: pd.DataFrame,
    solutions: list[str],
    padding_factors: list[str],
) -> pn.viewable.Viewable:
    """Plot final temperature by solution using the generic metric boxplot."""
    return _solution_metric_boxplot_chart(
        model,
        problem,
        solution_runs,
        solutions,
        padding_factors,
        value_column="final_temperature",
        value_label="Final temperature",
        title_metric="final temperature",
        empty_message="No final-temperature data was logged.",
    )


def _run_overview(
    series: dict[str, list[tuple]], codelet_time: pn.widgets.EditableIntSlider
) -> pn.Column:
    """Build charts summarizing the selected run."""
    return pn.Column(
        pn.Row(
            _line_chart(
                "Codelets on coderack",
                series["coderack"],
                "Number of codelets on coderack",
                codelet_time,
                series["snags"],
            ),
            _line_chart(
                "Temperature",
                series["temperature"],
                "Temperature",
                codelet_time,
                series["snags"],
                value_formatter=lambda value: f"{float(value):.2f}",
            ),
            _workspace_chart(series["workspace"], codelet_time, series["snags"]),
            sizing_mode="stretch_width",
        ),
        sizing_mode="stretch_width",
    )


def _line_chart(
    title: str,
    values: list[tuple],
    y_axis_label: str,
    codelet_time: pn.widgets.EditableIntSlider,
    snags: list[tuple[int, int]],
    value_formatter=str,
) -> pn.viewable.Viewable:
    if not values:
        return pn.pane.Alert(f"No {title.lower()} data was logged.", alert_type="info")
    chart = figure(
        title=title,
        x_axis_label="Codelets run",
        y_axis_label=y_axis_label,
        height=260,
        width=380,
        toolbar_location=None,
    )
    chart.line(*zip(*values), line_width=2)
    _add_snag_bands(chart, snags)
    _add_time_marker(chart, codelet_time, values, value_formatter)
    return chart


def _workspace_chart(
    values: list[tuple],
    codelet_time: pn.widgets.EditableIntSlider,
    snags: list[tuple[int, int]],
) -> pn.viewable.Viewable:
    if not values:
        return pn.pane.Alert("No workspace data was logged.", alert_type="info")
    times, totals = zip(*values)
    chart = figure(
        title="Workspace objects and structures",
        x_axis_label="Codelets run",
        y_axis_label="Total count",
        height=260,
        width=380,
        toolbar_location=None,
    )
    chart.line(times, totals, line_width=2, color="#1f77b4")
    _add_snag_bands(chart, snags)
    _add_time_marker(chart, codelet_time, values, str)
    return chart


def _add_snag_bands(chart, snags: list[tuple[int, int]]) -> None:
    """Shade time intervals during which Copycat was in a snag condition."""
    for start, end in snags:
        chart.add_layout(
            BoxAnnotation(
                left=start,
                right=end,
                fill_color="#9ca3af",
                fill_alpha=0.22,
                level="underlay",
            )
        )


def _add_time_marker(
    chart,
    codelet_time: pn.widgets.EditableIntSlider,
    values: list[tuple],
    value_formatter,
) -> None:
    """Add a vertical marker and value label that follow the selected time."""
    value = _value_at_time(values, codelet_time.value_throttled)
    marker = Span(
        location=codelet_time.value_throttled,
        dimension="height",
        line_color="red",
        line_width=2,
    )
    chart.add_layout(marker)
    label = Label(
        x=codelet_time.value_throttled,
        # The plot frame is shorter than the figure because of its title and axes.
        # Keep the screen-positioned label inside that frame.
        y=175,
        y_units="screen",
        text=value_formatter(value),
        background_fill_color="white",
        background_fill_alpha=0.9,
        border_line_color="black",
        padding=6,
        text_color="black",
    )
    chart.add_layout(label)

    def update_marker(event: Any) -> None:
        marker.location = event.new
        label.x = event.new
        label.text = value_formatter(_value_at_time(values, event.new))

    codelet_time.param.watch(update_marker, "value_throttled")


def _value_at_time(values: list[tuple], time: int) -> object:
    """Return the latest series value known at a selected codelet time."""
    return next(
        (value for value_time, value in reversed(values) if value_time <= time),
        values[0][1],
    )
