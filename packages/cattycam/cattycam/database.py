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
) -> list[tuple[int, str, str]]:
    """Return codelets still on the coderack at a selected codelet time."""
    with sqlite3.connect(database) as connection:
        return connection.execute(
            """SELECT urgency_bin, codelet_type, codelet_id FROM codelets
               WHERE run_id = ? AND birth_time <= ?
               AND (removal_time IS NULL OR removal_time > ?)
               ORDER BY urgency_bin DESC, id""",
            (run_id, time, time),
        ).fetchall()


def codelet_history(
    database: str | Path, run_id: int, time: int
) -> list[tuple[str, str | None, int, str, int | None, str | None, str | None]]:
    """Return completed codelets up to a selected time, newest first."""
    with sqlite3.connect(database) as connection:
        return connection.execute(
            """SELECT codelet_id, parent_codelet_id, run_time, codelet_type,
                      urgency_bin, result, fizzle_reason
               FROM codelets WHERE run_id = ?
               AND run_time IS NOT NULL AND run_time <= ?
               ORDER BY run_time DESC, id DESC""",
            (run_id, time),
        ).fetchall()


def codelet_types(database: str | Path, run_id: int) -> dict[str, str]:
    """Return codelet types keyed by their logged identifiers for one run."""
    with sqlite3.connect(database) as connection:
        return dict(
            connection.execute(
                "SELECT codelet_id, codelet_type FROM codelets WHERE run_id = ?",
                (run_id,),
            ).fetchall()
        )


def workspace_snapshot(database: str | Path, run_id: int, time: int) -> dict:
    """Return workspace entities visible at a selected codelet time."""
    with sqlite3.connect(database) as connection:
        letters = connection.execute(
            """SELECT letter_id, string_id, position, letter_category
               FROM letters WHERE run_id = ? AND creation_time <= ?
               AND (destruction_time IS NULL OR destruction_time > ?)
               ORDER BY string_id, position""",
            (run_id, time, time),
        ).fetchall()
        groups = connection.execute(
            """SELECT group_id, string_id, left_position, right_position,
                      proposal_time, creation_time
               FROM groups WHERE run_id = ? AND (proposal_time <= ? OR creation_time <= ?)
               AND (destruction_time IS NULL OR destruction_time > ?)
               AND (creation_time IS NULL OR creation_time > ? OR creation_time <= ?)""",
            (run_id, time, time, time, time, time),
        ).fetchall()
        bonds = connection.execute(
            """SELECT bond_id, source_id, target_id, bond_facet, bond_category,
                      direction_category,
                      proposal_time, creation_time
               FROM bonds WHERE run_id = ? AND (proposal_time <= ? OR creation_time <= ?)
               AND (destruction_time IS NULL OR destruction_time > ?)
               AND (creation_time IS NULL OR creation_time > ? OR creation_time <= ?)""",
            (run_id, time, time, time, time, time),
        ).fetchall()
        correspondences = connection.execute(
            """SELECT correspondence_id, source_id, target_id, proposal_time,
                      creation_time FROM correspondences
               WHERE run_id = ? AND (proposal_time <= ? OR creation_time <= ?)
               AND (destruction_time IS NULL OR destruction_time > ?)
               AND (creation_time IS NULL OR creation_time > ? OR creation_time <= ?)""",
            (run_id, time, time, time, time, time),
        ).fetchall()
        replacements = connection.execute(
            """SELECT replacement_id, source_id, target_id, proposal_time, creation_time
               FROM replacements WHERE run_id = ?
               AND (proposal_time <= ? OR creation_time <= ?)
               AND (destruction_time IS NULL OR destruction_time > ?)""",
            (run_id, time, time, time),
        ).fetchall()
        descriptions = connection.execute(
            """SELECT object_id, facet, descriptor FROM descriptions WHERE run_id = ?
               AND (proposal_time <= ? OR creation_time <= ?)
               AND (destruction_time IS NULL OR destruction_time > ?)
               ORDER BY rowid""",
            (run_id, time, time, time),
        ).fetchall()
        mappings = connection.execute(
            """SELECT correspondence_id, description_type_1, description_type_2,
                      initial_descriptor, target_descriptor, label
               FROM concept_mappings WHERE run_id = ? ORDER BY id""",
            (run_id,),
        ).fetchall()
        rules = connection.execute(
            """SELECT rule_id, object_category_1, descriptor_1,
                      replaced_description_type, descriptor_2, relation
               FROM rules WHERE run_id = ?
               AND (proposal_time <= ? OR creation_time <= ?)
               AND (destruction_time IS NULL OR destruction_time > ?)
               ORDER BY COALESCE(creation_time, proposal_time) DESC, id DESC""",
            (run_id, time, time, time),
        ).fetchall()
        translated_rules = connection.execute(
            """SELECT rule_id, object_category_1, descriptor_1,
                      replaced_description_type, descriptor_2, relation
               FROM translated_rules WHERE run_id = ?
               AND creation_time <= ?
               AND (destruction_time IS NULL OR destruction_time > ?)
               ORDER BY creation_time DESC, id DESC""",
            (run_id, time, time),
        ).fetchall()

    rule = rules[0] if rules else None
    translated_rule = translated_rules[0] if translated_rules else None

    return {
        "letters": [
            {"id": letter_id, "string": string_id, "position": position, "value": value}
            for letter_id, string_id, position, value in letters
        ],
        "groups": [
            {
                "id": group_id,
                "string": string_id,
                "left": left,
                "right": right,
                "proposed": creation is None,
            }
            for group_id, string_id, left, right, _, creation in groups
        ],
        "bonds": [
            {
                "id": bond_id,
                "source": source,
                "target": target,
                "facet": facet,
                "category": category,
                "direction": direction,
                "proposed": creation is None,
            }
            for bond_id, source, target, facet, category, direction, _, creation in bonds
        ],
        "correspondences": [
            {
                "id": correspondence_id,
                "source": source,
                "target": target,
                "proposed": creation is None,
                "mappings": [
                    {
                        "source": initial_descriptor,
                        "target": target_descriptor,
                        "label": label,
                        "source_type": description_type_1,
                        "target_type": description_type_2,
                    }
                    for mapping_correspondence_id, description_type_1, description_type_2,
                    initial_descriptor, target_descriptor, label in mappings
                    if mapping_correspondence_id == correspondence_id
                ],
            }
            for correspondence_id, source, target, _, creation in correspondences
        ],
        "replacements": [
            {
                "id": replacement_id,
                "source": source,
                "target": target,
                "proposed": creation is None,
            }
            for replacement_id, source, target, _, creation in replacements
        ],
        "descriptions": {
            object_id: [
                {"facet": facet, "descriptor": descriptor}
                for description_object_id, facet, descriptor in descriptions
                if description_object_id == object_id
            ]
            for object_id in {object_id for object_id, _, _ in descriptions}
        },
        "rule": (
            {
                "id": rule[0],
                "object_category": rule[1],
                "descriptor": rule[2],
                "replaced_description_type": rule[3],
                "descriptor_2": rule[4],
                "relation": rule[5],
            }
            if rules
            else None
        ),
        "translated_rule": (
            {
                "id": translated_rule[0],
                "object_category": translated_rule[1],
                "descriptor": translated_rule[2],
                "replaced_description_type": translated_rule[3],
                "descriptor_2": translated_rule[4],
                "relation": translated_rule[5],
            }
            if translated_rule
            else None
        ),
    }


def slipnet_snapshot(database: str | Path, run_id: int, time: int) -> dict:
    """Return Slipnet nodes, links, and activations at a selected codelet time."""
    with sqlite3.connect(database) as connection:
        nodes = connection.execute(
            "SELECT name FROM slipnodes WHERE run_id = ? ORDER BY name", (run_id,)
        ).fetchall()
        links = connection.execute(
            """SELECT source, target, label, fixed_length FROM sliplinks
               WHERE run_id = ? ORDER BY id""",
            (run_id,),
        ).fetchall()
        activation_changes = connection.execute(
            """SELECT object_id, value_json FROM attribute_values
               WHERE run_id = ? AND time <= ? AND attribute = 'activation'
               AND object_id LIKE 'slipnode:%' ORDER BY time, id""",
            (run_id, time),
        ).fetchall()

    activations: dict[str, float] = {}
    for object_id, value_json in activation_changes:
        try:
            activations[object_id.removeprefix("slipnode:")] = float(
                json.loads(value_json)
            )
        except (TypeError, ValueError, json.JSONDecodeError):
            continue
    return {
        "nodes": [
            {"name": name, "activation": activations.get(name, 0.0)}
            for (name,) in nodes
        ],
        "links": [
            {
                "source": source,
                "target": target,
                "label": label or "",
                "fixed_length": fixed_length,
            }
            for source, target, label, fixed_length in links
        ],
    }


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
