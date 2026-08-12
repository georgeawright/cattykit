"""Panel application for browsing a Cattycam SQLite database.

Run with ``panel serve cattycam/app.py --show --args path/to/history.sqlite``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pandas as pd
import panel as pn

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
    from cattycam.database import table_documentation, table_names, table_rows

    database_path = Path(database)
    if not database_path.is_file():
        return pn.Column(
            "# Cattycam database browser",
            pn.pane.Alert(f"Database not found: {database_path}", alert_type="danger"),
        )

    tables = table_names(database_path)
    if "runs" not in tables:
        return pn.Column(
            "# Cattycam database browser",
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
        pages = {
            table: pn.pane.HTML(
                table_documentation(database_path, table, run_id=run_id),
                sizing_mode="stretch_width",
            )
            for table in tables
        }
        back = pn.widgets.Button(name="Back to runs", button_type="default")
        back.on_click(lambda _: setattr(active_run, "value", 0))
        content.objects = [
            pn.Row(back, pn.pane.Markdown(f"## Run {run_id}")),
            pn.Tabs(*pages.items(), dynamic=True, sizing_mode="stretch_width"),
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
        "# Cattycam database browser",
        pn.pane.Markdown(f"`{database_path}` — {len(tables)} tables"),
        content,
        BrowserHistoryBridge(),
        sizing_mode="stretch_width",
    )


database_argument = sys.argv[1] if len(sys.argv) > 1 else "cattycam.sqlite"
create_app(database_argument).servable(title="Cattycam")
