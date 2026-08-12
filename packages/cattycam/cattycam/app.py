"""Panel application for browsing a Cattycam SQLite database.

Run with ``panel serve cattycam/app.py --show --args path/to/history.sqlite``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import panel as pn

# Panel executes a served file as a script, rather than as a package module.
# Add the source-package root so this works with ``panel serve cattycam/app.py``.
PACKAGE_ROOT = Path(__file__).resolve().parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

pn.extension()


def create_app(database: str | Path) -> pn.Column:
    """Create a Panel view with one HTML documentation page per table."""
    from cattycam.database import table_documentation, table_names

    database_path = Path(database)
    if not database_path.is_file():
        return pn.Column(
            "# Cattycam database browser",
            pn.pane.Alert(f"Database not found: {database_path}", alert_type="danger"),
        )

    tables = table_names(database_path)
    pages = {
        table: pn.pane.HTML(
            table_documentation(database_path, table), sizing_mode="stretch_width"
        )
        for table in tables
    }
    return pn.Column(
        "# Cattycam database browser",
        pn.pane.Markdown(f"`{database_path}` — {len(tables)} tables"),
        pn.Tabs(*pages.items(), dynamic=True, sizing_mode="stretch_width"),
        sizing_mode="stretch_width",
    )


database_argument = sys.argv[1] if len(sys.argv) > 1 else "cattycam.sqlite"
create_app(database_argument).servable(title="Cattycam")
