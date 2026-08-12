"""Panel application for browsing a Cattycam SQLite database.

Run with ``panel serve cattycam/app.py --show --args path/to/history.sqlite``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pandas as pd
import panel as pn
from bokeh.plotting import figure

# Panel executes a served file as a script, rather than as a package module.
# Add the source-package root so this works with ``panel serve cattycam/app.py``.
PACKAGE_ROOT = Path(__file__).resolve().parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

pn.extension("tabulator")


class BrowserHistoryBridge(pn.reactive.ReactiveHTML):
    """Reload the standalone app after browser Back or Forward navigation."""

    _template = "<div></div>"
    _scripts = {
        "render": """
            if (!state.popstate_listener) {
                state.popstate_listener = () => window.location.reload()
                window.addEventListener("popstate", state.popstate_listener)
            }
        """
    }


def create_app(database: str | Path) -> pn.Column:
    """Create a run picker which opens a tabbed, run-specific database view."""
    from cattycam.database import (
        run_overview_series,
        table_documentation,
        table_names,
        table_rows,
    )

    database_path = Path(database)
    if not database_path.is_file():
        return pn.Column(
            "# Cattycam",
            pn.pane.Alert(f"Database not found: {database_path}", alert_type="danger"),
        )

    tables = table_names(database_path)
    if "runs" not in tables:
        return pn.Column(
            "# Cattycam",
            pn.pane.Alert(
                "This database has no Cattycam runs table. Generate a new history "
                "database with the current SQLiteLogger.",
                alert_type="warning",
            ),
        )
    content = pn.Column(sizing_mode="stretch_width")
    active_run = pn.widgets.IntInput(value=0, visible=False)
    if pn.state.location:
        # This is a standalone Panel application. Reloading after a URL change
        # gives browser Back/Forward a fresh session whose selected run is read
        # from the query string.
        pn.state.location.reload = True
        pn.state.location.sync(active_run, {"value": "run_id"})

    def show_run(run_id: int) -> None:
        columns, rows = table_rows(database_path, "runs", run_id=run_id)
        if not rows:
            content.objects = [
                pn.pane.Alert(f"Run {run_id} was not found.", alert_type="warning")
            ]
            return
        run = dict(zip(columns, rows[0], strict=True))
        model = run["model"]
        problem = run["problem"]
        solution = run["solution"]
        codelets_run = run["number_of_codelets_run"]
        final_temperature = run["final_temperature"]
        overview = _run_overview(run_overview_series(database_path, run_id))
        visible_tables = [table for table in tables if table != "attribute_values"]
        table_content = pn.Column(sizing_mode="stretch_width")
        table_links = pn.Row(sizing_mode="stretch_width")

        def show_table(table: str) -> None:
            table_content.objects = [
                pn.pane.HTML(
                    table_documentation(database_path, table, run_id=run_id),
                    sizing_mode="stretch_width",
                )
            ]

        for table in visible_tables:
            link = pn.widgets.Button(name=table, button_type="light")
            link.on_click(lambda _, table=table: show_table(table))
            table_links.append(link)
        detail_panels = pn.Row(
            pn.Column(
                "### Coderack",
                pn.Spacer(height=120),
                "### Codelet history",
                pn.Spacer(height=120),
                sizing_mode="stretch_width",
                styles={"flex": "1"},
            ),
            pn.Column(
                "### Workspace",
                pn.Spacer(height=120),
                "### Slipnet",
                pn.Spacer(height=120),
                sizing_mode="stretch_width",
                styles={"flex": "2"},
            ),
            sizing_mode="stretch_width",
        )
        problem_and_solution = (
            problem if solution is None else str(problem).replace("?", str(solution))
        )
        content.objects = [
            pn.Row(
                pn.pane.Markdown(
                    f"## Run {run_id} of {model} {problem_and_solution}"
                    f" Codelets run: {codelets_run}"
                    f" final temperature: {final_temperature}"
                )
            ),
            overview,
            detail_panels,
            table_links,
            table_content,
        ]

    def show_runs(_: object | None = None) -> None:
        columns, rows = table_rows(database_path, "runs")
        runs = pd.DataFrame(rows, columns=columns)
        grid = pn.widgets.Tabulator(
            runs,
            selectable=1,
            show_index=False,
            sizing_mode="stretch_width",
        )

        def open_run(event: Any) -> None:
            row_index = event.row
            active_run.value = int(runs.iloc[row_index]["id"])

        grid.on_click(open_run)
        content.objects = [
            "## Runs",
            pn.pane.Markdown("Click a row to inspect that run."),
            grid,
        ]

    def update_view(event: Any | None = None) -> None:
        run_id = active_run.value if event is None else event.new
        if run_id:
            show_run(run_id)
        else:
            show_runs()

    active_run.param.watch(update_view, "value")
    update_view()
    return pn.Column(
        "# Cattycam",
        content,
        BrowserHistoryBridge(),
        sizing_mode="stretch_width",
    )


def _run_overview(series: dict[str, list[tuple]]) -> pn.Column:
    """Build charts summarizing the selected run."""
    return pn.Column(
        pn.Row(
            _line_chart(
                "Codelets on coderack",
                series["coderack"],
                "Number of codelets on coderack",
            ),
            _line_chart("Temperature", series["temperature"], "Temperature"),
            _workspace_chart(series["workspace"]),
            sizing_mode="stretch_width",
        ),
        sizing_mode="stretch_width",
    )


def _line_chart(
    title: str, values: list[tuple], y_axis_label: str
) -> pn.viewable.Viewable:
    if not values:
        return pn.pane.Alert(f"No {title.lower()} data was logged.", alert_type="info")
    chart = figure(
        title=title,
        x_axis_label="Codelets run",
        y_axis_label=y_axis_label,
        height=260,
        width=380,
    )
    chart.line(*zip(*values), line_width=2)
    return chart


def _workspace_chart(values: list[tuple]) -> pn.viewable.Viewable:
    if not values:
        return pn.pane.Alert("No workspace data was logged.", alert_type="info")
    times, totals = zip(*values)
    chart = figure(
        title="Workspace objects and structures",
        x_axis_label="Codelets run",
        y_axis_label="Total count",
        height=260,
        width=380,
    )
    chart.line(times, totals, line_width=2, color="#1f77b4")
    return chart


database_argument = sys.argv[1] if len(sys.argv) > 1 else "cattycam.sqlite"
create_app(database_argument).servable(title="Cattycam")
