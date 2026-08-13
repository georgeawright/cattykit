"""Read-only helpers for presenting Cattycam SQLite databases."""

from __future__ import annotations

import html
import json
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


def table_documentation(
    database: str | Path, table: str, *, run_id: int | None = None
) -> str:
    """Return an HTML fragment containing one database table's rows."""
    quoted_table = _quote_identifier(table)
    with sqlite3.connect(database) as connection:
        columns = connection.execute(f"PRAGMA table_info({quoted_table})").fetchall()
        query, parameters = _table_query(quoted_table, table, run_id)
        rows = connection.execute(query, parameters).fetchall()
    column_names = [column[1] for column in columns]
    return "\n".join(
        (
            f"<h2>{html.escape(table)}</h2>",
            f"<p>{len(rows)} row{'s' if len(rows) != 1 else ''}</p>",
            _html_table(column_names, rows),
        )
    )


def table_rows(
    database: str | Path, table: str, *, run_id: int | None = None
) -> tuple[list[str], list[tuple[object, ...]]]:
    """Return a table's columns and rows, optionally restricted to one run."""
    quoted_table = _quote_identifier(table)
    with sqlite3.connect(database) as connection:
        columns = connection.execute(f"PRAGMA table_info({quoted_table})").fetchall()
        query, parameters = _table_query(quoted_table, table, run_id)
        rows = connection.execute(query, parameters).fetchall()
    return [column[1] for column in columns], rows


def run_overview_series(database: str | Path, run_id: int) -> dict[str, list[tuple]]:
    """Return the selected run's coderack, temperature, and workspace series."""
    with sqlite3.connect(database) as connection:
        attributes = connection.execute(
            """SELECT time, object_id, attribute, value_json
               FROM attribute_values WHERE run_id = ? ORDER BY time, id""",
            (run_id,),
        ).fetchall()
        structures = connection.execute(
            """SELECT creation_time, destruction_time FROM letters WHERE run_id = ?
               UNION ALL SELECT creation_time, destruction_time FROM groups WHERE run_id = ?
               UNION ALL SELECT creation_time, destruction_time FROM bonds WHERE run_id = ?
               UNION ALL SELECT creation_time, destruction_time FROM correspondences WHERE run_id = ?
               UNION ALL SELECT creation_time, destruction_time FROM replacements WHERE run_id = ?
               UNION ALL SELECT creation_time, destruction_time FROM rules WHERE run_id = ?""",
            (run_id,) * 6,
        ).fetchall()
        objects = connection.execute(
            """SELECT creation_time, destruction_time FROM letters WHERE run_id = ?
               UNION ALL SELECT creation_time, destruction_time FROM groups WHERE run_id = ?""",
            (run_id, run_id),
        ).fetchall()

    coderack: list[tuple] = []
    temperature: list[tuple] = []
    times: set[int] = set()
    for time, object_id, attribute, value_json in attributes:
        value = json.loads(value_json)
        times.add(time)
        if object_id == "coderack" and attribute == "number_of_codelets_on_coderack":
            coderack.append((time, value))
        elif object_id == "temperature" and attribute == "value":
            temperature.append((time, value))
    for creation_time, destruction_time in structures:
        times.update(
            time for time in (creation_time, destruction_time) if time is not None
        )

    def live_count(rows: list[tuple], time: int) -> int:
        return sum(
            creation_time is not None
            and creation_time <= time
            and (destruction_time is None or destruction_time > time)
            for creation_time, destruction_time in rows
        )

    return {
        "coderack": coderack,
        "temperature": temperature,
        "workspace": [
            (time, live_count(objects, time) + live_count(structures, time))
            for time in sorted(times)
        ],
    }


def coderack_codelets(
    database: str | Path, run_id: int, time: int
) -> list[tuple[int, str]]:
    """Return codelets still on the coderack at a selected codelet time."""
    with sqlite3.connect(database) as connection:
        return connection.execute(
            """SELECT urgency_bin, codelet_type FROM codelets
               WHERE run_id = ? AND birth_time <= ?
               AND (removal_time IS NULL OR removal_time > ?)
               ORDER BY urgency_bin DESC, id""",
            (run_id, time, time),
        ).fetchall()


def _table_query(
    quoted_table: str, table: str, run_id: int | None
) -> tuple[str, tuple[object, ...]]:
    if run_id is None:
        return f"SELECT * FROM {quoted_table}", ()
    if table == "runs":
        return f"SELECT * FROM {quoted_table} WHERE id = ?", (run_id,)
    if table == "group_members":
        return (
            "SELECT group_members.* FROM group_members "
            "JOIN groups ON groups.id = group_members.group_id "
            "WHERE groups.run_id = ?",
            (run_id,),
        )
    if table == "group_bonds":
        return (
            "SELECT group_bonds.* FROM group_bonds "
            "JOIN groups ON groups.id = group_bonds.group_id "
            "WHERE groups.run_id = ?",
            (run_id,),
        )
    return f"SELECT * FROM {quoted_table} WHERE run_id = ?", (run_id,)


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
