"""Read-only helpers for presenting Cattycam SQLite databases."""

from __future__ import annotations

import html
import sqlite3
from collections.abc import Sequence
from pathlib import Path


def table_names(database: str | Path) -> list[str]:
    """Return application tables in alphabetical order."""
    with sqlite3.connect(database) as connection:
        return [
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]


def table_documentation(database: str | Path, table: str) -> str:
    """Return an HTML fragment containing one database table's rows."""
    quoted_table = _quote_identifier(table)
    with sqlite3.connect(database) as connection:
        columns = connection.execute(f"PRAGMA table_info({quoted_table})").fetchall()
        rows = connection.execute(f"SELECT * FROM {quoted_table}").fetchall()
    column_names = [column[1] for column in columns]
    return "\n".join(
        (
            f"<h2>{html.escape(table)}</h2>",
            f"<p>{len(rows)} row{'s' if len(rows) != 1 else ''}</p>",
            _html_table(column_names, rows),
        )
    )


def _html_table(headers: Sequence[object], rows: Sequence[Sequence[object]]) -> str:
    """Build a compact, escaped HTML table."""
    header_cells = "".join(f"<th>{html.escape(str(value))}</th>" for value in headers)
    body_rows = "".join(
        "<tr>"
        + "".join(
            f"<td>{html.escape('' if value is None else str(value))}</td>"
            for value in row
        )
        + "</tr>"
        for row in rows
    )
    empty_row = (
        f'<tr><td colspan="{len(headers)}"><em>No rows</em></td></tr>'
        if not rows
        else ""
    )
    return (
        "<table><thead><tr>"
        + header_cells
        + "</tr></thead><tbody>"
        + (body_rows or empty_row)
        + "</tbody></table>"
    )


def _quote_identifier(identifier: str) -> str:
    """Quote a SQLite identifier after checking it belongs to the database."""
    return '"' + identifier.replace('"', '""') + '"'
