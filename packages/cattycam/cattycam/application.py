from __future__ import annotations

import html
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import pandas as pd
import panel as pn

from .canvases import BrowserHistoryBridge
from .charts import _run_overview
from .details import (
    _codelet_history,
    _coderack_badges,
    _slipnet_activation_list,
    _slipnet_canvas,
    _workspace_canvas,
)
from .views import _problem_overview, _run_group_table


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
        codelet_time = pn.widgets.EditableIntSlider(
            name="Codelets run",
            start=0,
            end=int(codelets_run or 0),
            value=int(codelets_run or 0),
            sizing_mode="stretch_width",
        )
        overview = _run_overview(
            run_overview_series(database_path, run_id), codelet_time
        )
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
        coderack_panel = pn.bind(
            _coderack_badges,
            database_path,
            run_id,
            codelet_time.param.value_throttled,
        )
        codelet_history_panel = pn.bind(
            _codelet_history,
            database_path,
            run_id,
            codelet_time.param.value_throttled,
        )
        workspace_panel = pn.bind(
            _workspace_canvas,
            database_path,
            run_id,
            codelet_time.param.value_throttled,
        )
        slipnet_panel = pn.bind(
            _slipnet_canvas,
            database_path,
            run_id,
            codelet_time.param.value_throttled,
        )
        slipnet_activations = pn.bind(
            _slipnet_activation_list,
            database_path,
            run_id,
            codelet_time.param.value_throttled,
        )
        detail_panels = pn.Row(
            pn.Column(
                "### Coderack",
                coderack_panel,
                "### Codelet history",
                codelet_history_panel,
                sizing_mode="stretch_width",
                styles={"flex": "1"},
            ),
            pn.Column(
                "### Workspace",
                workspace_panel,
                "### Slipnet",
                pn.Row(
                    slipnet_panel,
                    slipnet_activations,
                    sizing_mode="stretch_width",
                ),
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
            codelet_time,
            detail_panels,
            table_links,
            table_content,
        ]

    def show_runs(_: object | None = None) -> None:
        columns, rows = table_rows(database_path, "runs")
        runs = pd.DataFrame(rows, columns=columns)
        groups = []
        for (model, problem), grouped_runs in runs.groupby(
            ["model", "problem"], dropna=False, sort=True
        ):
            groups.extend(
                (
                    pn.pane.HTML(
                        "<h3>"
                        f"{html.escape(str(model))} — {html.escape(str(problem))}"
                        f" <a href=\"?{urlencode({'model': model, 'problem': problem})}\">Overview</a>"
                        "</h3>"
                    ),
                    _run_group_table(grouped_runs, columns),
                )
            )
        content.objects = [
            "## Runs",
            pn.pane.Markdown("Click a run ID to inspect that run."),
            *groups,
        ]

    def show_problem(model: str, problem: str) -> None:
        columns, rows = table_rows(database_path, "runs")
        runs = pd.DataFrame(rows, columns=columns)
        problem_runs = runs[(runs["model"] == model) & (runs["problem"] == problem)]
        if problem_runs.empty:
            content.objects = [
                pn.pane.Alert(
                    "No runs were found for this model and problem.",
                    alert_type="warning",
                )
            ]
            return
        content.objects = [
            pn.pane.HTML('<p><a href="?">← All runs</a></p>'),
            _problem_overview(model, problem, problem_runs),
        ]

    def update_view(event: Any | None = None) -> None:
        run_id = active_run.value if event is None else event.new
        if run_id:
            show_run(run_id)
        elif (
            pn.state.location
            and {"model", "problem"} <= pn.state.location.query_params.keys()
        ):
            show_problem(
                pn.state.location.query_params["model"],
                pn.state.location.query_params["problem"],
            )
        else:
            show_runs()

    active_run.param.watch(update_view, "value")
    update_view()
    return pn.Column(
        content,
        BrowserHistoryBridge(),
        sizing_mode="stretch_width",
    )
