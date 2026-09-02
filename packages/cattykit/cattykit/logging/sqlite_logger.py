from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .event import ModelEvent


class SQLiteLogger:
    """Persist model events in a SQLite database that can be read by Cattycam."""

    def __init__(self, path: str | Path) -> None:
        self._connection = sqlite3.connect(path)
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._run_ids: dict[str, int] = {}
        self._create_schema()
        self._connection.commit()
        self._codelets_run = 0
        self._active_codelet_id: str | None = None

    def log(self, event: ModelEvent) -> None:
        """Record an event using the logger's current codelet-time cursor."""
        data = dict(event.data)
        self._update_codelet_time(event.kind, data)
        if data.get("time") is None:
            data["time"] = self._codelets_run
        if event.kind == "run_started":
            self._active_codelet_id = None
        elif event.kind != "codelet_selected" and self._active_codelet_id is not None:
            data.setdefault("parent_codelet_id", self._active_codelet_id)
        self._record_event(event, data)
        if event.kind == "codelet_selected":
            self._active_codelet_id = data.get("codelet_id")
        elif event.kind in {"codelet_finished", "run_finished"}:
            self._active_codelet_id = None
        self._connection.commit()

    @property
    def codelets_run(self) -> int:
        """Return the current codelet-time cursor for the active run."""
        return self._codelets_run

    def close(self) -> None:
        """Close the SQLite connection."""
        self._connection.close()

    def _create_schema(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY,
                model TEXT NOT NULL,
                run_time TEXT NOT NULL,
                problem TEXT,
                solution TEXT,
                final_temperature REAL,
                number_of_codelets_run INTEGER,
                number_of_snags INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS snags (
                id INTEGER PRIMARY KEY,
                run_id INTEGER NOT NULL REFERENCES runs(id),
                snag_start INTEGER NOT NULL,
                snag_end INTEGER
            );

            CREATE TABLE IF NOT EXISTS codelets (
                id INTEGER PRIMARY KEY,
                run_id INTEGER NOT NULL REFERENCES runs(id),
                codelet_id TEXT,
                parent_codelet_id TEXT,
                codelet_type TEXT NOT NULL,
                urgency_bin INTEGER,
                arguments_json TEXT,
                birth_time INTEGER,
                run_time INTEGER,
                removal_time INTEGER,
                result TEXT,
                fizzle_reason TEXT
            );

            CREATE TABLE IF NOT EXISTS strings (
                id INTEGER PRIMARY KEY,
                run_id INTEGER NOT NULL REFERENCES runs(id),
                string_id TEXT NOT NULL,
                role TEXT NOT NULL,
                value TEXT,
                UNIQUE(run_id, string_id)
            );

            CREATE TABLE IF NOT EXISTS letters (
                id INTEGER PRIMARY KEY,
                run_id INTEGER NOT NULL REFERENCES runs(id),
                letter_id TEXT NOT NULL,
                parent_codelet_id TEXT,
                string_id TEXT,
                position INTEGER,
                letter_category TEXT,
                proposal_time INTEGER,
                creation_time INTEGER,
                destruction_time INTEGER,
                UNIQUE(run_id, letter_id)
            );

            CREATE TABLE IF NOT EXISTS descriptions (
                id INTEGER PRIMARY KEY,
                run_id INTEGER NOT NULL REFERENCES runs(id),
                description_id TEXT NOT NULL,
                parent_codelet_id TEXT,
                object_id TEXT,
                facet TEXT,
                descriptor TEXT,
                proposal_time INTEGER,
                creation_time INTEGER,
                destruction_time INTEGER,
                UNIQUE(run_id, description_id)
            );

            CREATE TABLE IF NOT EXISTS bonds (
                id INTEGER PRIMARY KEY,
                run_id INTEGER NOT NULL REFERENCES runs(id),
                bond_id TEXT NOT NULL,
                parent_codelet_id TEXT,
                string_id TEXT,
                source_id TEXT,
                target_id TEXT,
                bond_category TEXT,
                direction_category TEXT,
                bond_facet TEXT,
                source_descriptor TEXT,
                target_descriptor TEXT,
                proposal_time INTEGER,
                creation_time INTEGER,
                destruction_time INTEGER,
                UNIQUE(run_id, bond_id)
            );

            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY,
                run_id INTEGER NOT NULL REFERENCES runs(id),
                group_id TEXT NOT NULL,
                parent_codelet_id TEXT,
                string_id TEXT,
                group_category TEXT,
                direction_category TEXT,
                bond_category TEXT,
                bond_facet TEXT,
                left_position INTEGER,
                right_position INTEGER,
                proposal_time INTEGER,
                creation_time INTEGER,
                destruction_time INTEGER,
                UNIQUE(run_id, group_id)
            );

            CREATE TABLE IF NOT EXISTS group_members (
                group_id INTEGER NOT NULL REFERENCES groups(id),
                object_id TEXT NOT NULL,
                member_order INTEGER NOT NULL,
                PRIMARY KEY (group_id, object_id)
            );

            CREATE TABLE IF NOT EXISTS group_bonds (
                group_id INTEGER NOT NULL REFERENCES groups(id),
                bond_id TEXT NOT NULL,
                bond_order INTEGER NOT NULL,
                PRIMARY KEY (group_id, bond_id)
            );

            CREATE TABLE IF NOT EXISTS correspondences (
                id INTEGER PRIMARY KEY,
                run_id INTEGER NOT NULL REFERENCES runs(id),
                correspondence_id TEXT NOT NULL,
                parent_codelet_id TEXT,
                source_id TEXT,
                target_id TEXT,
                proposal_time INTEGER,
                creation_time INTEGER,
                destruction_time INTEGER,
                UNIQUE(run_id, correspondence_id)
            );

            CREATE TABLE IF NOT EXISTS concept_mappings (
                id INTEGER PRIMARY KEY,
                run_id INTEGER NOT NULL REFERENCES runs(id),
                concept_mapping_id TEXT NOT NULL,
                correspondence_id TEXT,
                description_type_1 TEXT,
                description_type_2 TEXT,
                initial_descriptor TEXT,
                target_descriptor TEXT,
                label TEXT,
                UNIQUE(run_id, concept_mapping_id)
            );

            CREATE TABLE IF NOT EXISTS replacements (
                id INTEGER PRIMARY KEY,
                run_id INTEGER NOT NULL REFERENCES runs(id),
                replacement_id TEXT NOT NULL,
                parent_codelet_id TEXT,
                source_id TEXT,
                target_id TEXT,
                proposal_time INTEGER,
                creation_time INTEGER,
                destruction_time INTEGER,
                UNIQUE(run_id, replacement_id)
            );

            CREATE TABLE IF NOT EXISTS rules (
                id INTEGER PRIMARY KEY,
                run_id INTEGER NOT NULL REFERENCES runs(id),
                rule_id TEXT NOT NULL,
                parent_codelet_id TEXT,
                object_category_1 TEXT,
                descriptor_1_facet TEXT,
                descriptor_1 TEXT,
                object_category_2 TEXT,
                descriptor_2 TEXT,
                replaced_description_type TEXT,
                relation TEXT,
                proposal_time INTEGER,
                creation_time INTEGER,
                destruction_time INTEGER,
                UNIQUE(run_id, rule_id)
            );

            CREATE TABLE IF NOT EXISTS translated_rules (
                id INTEGER PRIMARY KEY,
                run_id INTEGER NOT NULL REFERENCES runs(id),
                rule_id TEXT NOT NULL,
                parent_codelet_id TEXT,
                object_category_1 TEXT,
                descriptor_1_facet TEXT,
                descriptor_1 TEXT,
                object_category_2 TEXT,
                descriptor_2 TEXT,
                replaced_description_type TEXT,
                relation TEXT,
                proposal_time INTEGER,
                creation_time INTEGER,
                destruction_time INTEGER,
                UNIQUE(run_id, rule_id)
            );

            CREATE TABLE IF NOT EXISTS slipnodes (
                id INTEGER PRIMARY KEY,
                run_id INTEGER NOT NULL REFERENCES runs(id),
                name TEXT NOT NULL,
                conceptual_depth REAL,
                depth_factor REAL,
                intrinsic_link_length REAL,
                shrunk_link_length REAL,
                category_links_json TEXT NOT NULL DEFAULT '[]',
                instance_links_json TEXT NOT NULL DEFAULT '[]',
                has_property_links_json TEXT NOT NULL DEFAULT '[]',
                lateral_sliplinks_json TEXT NOT NULL DEFAULT '[]',
                lateral_non_sliplinks_json TEXT NOT NULL DEFAULT '[]',
                incoming_links_json TEXT NOT NULL DEFAULT '[]',
                UNIQUE(run_id, name)
            );

            CREATE TABLE IF NOT EXISTS sliplinks (
                id INTEGER PRIMARY KEY,
                run_id INTEGER NOT NULL REFERENCES runs(id),
                source TEXT NOT NULL,
                target TEXT NOT NULL,
                label TEXT,
                fixed_length REAL,
                is_category_link INTEGER NOT NULL DEFAULT 0,
                is_instance_link INTEGER NOT NULL DEFAULT 0,
                is_has_property_link INTEGER NOT NULL DEFAULT 0,
                is_lateral_sliplink INTEGER NOT NULL DEFAULT 0,
                is_lateral_non_sliplink INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS attribute_values (
                id INTEGER PRIMARY KEY,
                run_id INTEGER NOT NULL REFERENCES runs(id),
                time INTEGER NOT NULL,
                object_id TEXT NOT NULL,
                attribute TEXT NOT NULL,
                value_json TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS codelets_by_run_time
                ON codelets(run_id, run_time);
            CREATE INDEX IF NOT EXISTS attributes_by_run_time
                ON attribute_values(run_id, time);
            CREATE INDEX IF NOT EXISTS bonds_by_run_id ON bonds(run_id, bond_id);
            CREATE INDEX IF NOT EXISTS groups_by_run_id ON groups(run_id, group_id);
            CREATE INDEX IF NOT EXISTS correspondences_by_run_id
                ON correspondences(run_id, correspondence_id);
            """
        )
        self._ensure_column("codelets", "removal_time", "INTEGER")

    def _ensure_column(self, table: str, column: str, definition: str) -> None:
        """Add a schema column when opening a history database from an older logger."""
        columns = {
            row[1] for row in self._connection.execute(f"PRAGMA table_info({table})")
        }
        if column not in columns:
            self._connection.execute(
                f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
            )

    @staticmethod
    def _json(value: Any) -> str:
        """Encode arbitrary model values without losing the logging event."""
        return json.dumps(value, sort_keys=True, default=str)

    def _run_id(self, event: ModelEvent) -> int | None:
        return self._run_ids.get(event.model)

    def _update_codelet_time(self, kind: str, data: Mapping[str, Any]) -> None:
        """Synchronize the logger's codelet-time cursor with an incoming event."""
        if kind == "run_started":
            self._codelets_run = int(data.get("time", 0))
        elif data.get("time") is not None:
            self._codelets_run = int(data["time"])
        elif kind == "codelet_selected":
            self._codelets_run += 1

    def _record_event(self, event: ModelEvent, data: Mapping[str, Any]) -> None:
        if event.kind == "run_started":
            cursor = self._connection.execute(
                "INSERT INTO runs (model, run_time, problem) VALUES (?, ?, ?)",
                (event.model, event.timestamp.isoformat(), data.get("problem")),
            )
            if cursor.lastrowid is None:
                raise RuntimeError("SQLite did not return the new run identifier")
            self._run_ids[event.model] = cursor.lastrowid
            return

        run_id = self._run_id(event)
        if run_id is None:
            return
        if event.kind == "run_finished":
            self._connection.execute(
                """UPDATE runs SET number_of_codelets_run = ?,
                   final_temperature = COALESCE(?, final_temperature)
                   WHERE id = ?""",
                (
                    data.get("codelets_run", data.get("time")),
                    data.get("temperature"),
                    run_id,
                ),
            )
            self._run_ids.pop(event.model, None)
        elif event.kind == "answer_found":
            self._connection.execute(
                "UPDATE runs SET solution = ? WHERE id = ?",
                (data.get("answer"), run_id),
            )
        elif event.kind == "snag_encountered":
            self._connection.execute(
                "UPDATE runs SET number_of_snags = number_of_snags + 1 WHERE id = ?",
                (run_id,),
            )
            self._connection.execute(
                "INSERT INTO snags (run_id, snag_start) VALUES (?, ?)",
                (run_id, data.get("time")),
            )
        elif event.kind == "snag_ended":
            self._connection.execute(
                "UPDATE snags SET snag_end = ? WHERE run_id = ? AND snag_end IS NULL",
                (data.get("time"), run_id),
            )
        elif event.kind in {"codelet_selected", "codelet_started"}:
            cursor = self._connection.execute(
                """UPDATE codelets SET
                   parent_codelet_id = COALESCE(?, parent_codelet_id),
                   codelet_type = COALESCE(?, codelet_type),
                   urgency_bin = COALESCE(?, urgency_bin),
                   birth_time = COALESCE(?, birth_time), run_time = ?, removal_time = ?
                   WHERE run_id = ? AND codelet_id = ?""",
                (
                    data.get("parent_codelet_id"),
                    data.get("codelet_type", data.get("codelet", "unknown")),
                    data.get("urgency_bin"),
                    data.get("birth_time"),
                    data.get("time"),
                    data.get("time"),
                    run_id,
                    data.get("codelet_id"),
                ),
            )
            if cursor.rowcount == 0:
                self._connection.execute(
                    """INSERT INTO codelets
                (run_id, codelet_id, parent_codelet_id, codelet_type, urgency_bin,
                 arguments_json, birth_time, run_time, removal_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        run_id,
                        data.get("codelet_id"),
                        data.get("parent_codelet_id"),
                        data.get("codelet_type", data.get("codelet", "unknown")),
                        data.get("urgency_bin"),
                        self._json(data.get("arguments", {})),
                        data.get("birth_time"),
                        data.get("time"),
                        data.get("time"),
                    ),
                )
        elif event.kind == "codelet_posted":
            self._post_codelet(run_id, data)
        elif event.kind == "codelet_removed":
            self._connection.execute(
                """UPDATE codelets SET removal_time = ?
                   WHERE run_id = ? AND codelet_id = ? AND removal_time IS NULL""",
                (data["time"], run_id, data.get("codelet_id")),
            )
        elif event.kind == "codelet_finished":
            self._finish_codelet(run_id, data)
        elif event.kind in {"string_created", "string_initialized"}:
            self._upsert_string(run_id, data)
        elif event.kind in {
            "letter_proposed",
            "letter_created",
            "letter_destroyed",
        }:
            self._upsert_lifecycle_entity("letters", "letter", run_id, event.kind, data)
        elif event.kind in {
            "description_proposed",
            "description_created",
            "description_destroyed",
        }:
            self._upsert_lifecycle_entity(
                "descriptions", "description", run_id, event.kind, data
            )
        elif event.kind in {"bond_proposed", "bond_created", "bond_destroyed"}:
            self._upsert_lifecycle_entity("bonds", "bond", run_id, event.kind, data)
        elif event.kind in {"group_proposed", "group_created", "group_destroyed"}:
            group_row_id = self._upsert_lifecycle_entity(
                "groups", "group", run_id, event.kind, data
            )
            if group_row_id is not None and "members" in data:
                self._replace_group_members(group_row_id, data["members"])
            if group_row_id is not None and "bonds" in data:
                self._replace_group_bonds(group_row_id, data["bonds"])
        elif event.kind in {
            "correspondence_proposed",
            "correspondence_created",
            "correspondence_destroyed",
        }:
            self._upsert_lifecycle_entity(
                "correspondences", "correspondence", run_id, event.kind, data
            )
        elif event.kind in {
            "replacement_proposed",
            "replacement_created",
            "replacement_destroyed",
        }:
            self._upsert_lifecycle_entity(
                "replacements", "replacement", run_id, event.kind, data
            )
        elif event.kind in {"rule_proposed", "rule_created", "rule_destroyed"}:
            self._upsert_lifecycle_entity("rules", "rule", run_id, event.kind, data)
        elif event.kind in {
            "translated_rule_proposed",
            "translated_rule_created",
            "translated_rule_destroyed",
        }:
            self._upsert_lifecycle_entity(
                "translated_rules", "rule", run_id, event.kind, data
            )
        elif event.kind in {"concept_mapping_created", "concept_mapping_updated"}:
            self._upsert_concept_mapping(run_id, data)
        elif event.kind in {"slipnode_created", "slipnode_initialized"}:
            self._upsert_slipnode(run_id, data)
        elif event.kind in {"sliplink_created", "sliplink_initialized"}:
            self._insert_sliplink(run_id, data)
        elif event.kind in {"attribute_value", "attribute_updated"}:
            self._connection.execute(
                """INSERT INTO attribute_values
                   (run_id, time, object_id, attribute, value_json)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    run_id,
                    data.get("time", 0),
                    data["object_id"],
                    data["attribute"],
                    self._json(data.get("value")),
                ),
            )

    def _post_codelet(self, run_id: int, data: Mapping[str, Any]) -> None:
        """Record a codelet when it enters the coderack.

        Selection later updates this row with the codelet's run time, preserving
        the interval between posting and execution.
        """
        self._connection.execute(
            """INSERT INTO codelets
               (run_id, codelet_id, parent_codelet_id, codelet_type, urgency_bin,
                arguments_json, birth_time)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                run_id,
                data.get("codelet_id"),
                self._active_codelet_id,
                data.get("codelet_type", data.get("codelet", "unknown")),
                data.get("urgency_bin"),
                self._json(data.get("arguments", data.get("argument"))),
                data.get("birth_time", data.get("time")),
            ),
        )

    def _finish_codelet(self, run_id: int, data: Mapping[str, Any]) -> None:
        cursor = self._connection.execute(
            """UPDATE codelets SET result = ?, fizzle_reason = ?, run_time = ?
               WHERE id = (SELECT id FROM codelets WHERE run_id = ?
               AND codelet_id = ? AND result IS NULL ORDER BY id DESC LIMIT 1)""",
            (
                data.get("outcome", data.get("result")),
                data.get("reason", data.get("fizzle_reason")),
                data.get("time"),
                run_id,
                data.get("codelet_id"),
            ),
        )
        if cursor.rowcount == 0:
            self._connection.execute(
                """INSERT INTO codelets (run_id, codelet_id, codelet_type, urgency_bin,
                   arguments_json, run_time, result, fizzle_reason)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    run_id,
                    data.get("codelet_id"),
                    data.get("codelet_type", data.get("codelet", "unknown")),
                    data.get("urgency_bin"),
                    self._json(data.get("arguments", {})),
                    data.get("time"),
                    data.get("outcome", data.get("result")),
                    data.get("reason", data.get("fizzle_reason")),
                ),
            )

    def _upsert_string(self, run_id: int, data: Mapping[str, Any]) -> None:
        string_id = str(data.get("string_id", data.get("role")))
        self._connection.execute(
            """INSERT INTO strings (run_id, string_id, role, value) VALUES (?, ?, ?, ?)
               ON CONFLICT(run_id, string_id) DO UPDATE SET value = excluded.value""",
            (
                run_id,
                string_id,
                data.get("role", string_id),
                data.get("value", data.get("string")),
            ),
        )

    def _upsert_lifecycle_entity(
        self,
        table: str,
        entity: str,
        run_id: int,
        kind: str,
        data: Mapping[str, Any],
    ) -> int | None:
        """Upsert one typed workspace entity and its lifecycle timestamp."""
        entity_id = str(data[f"{entity}_id"])
        time_column = {
            "proposed": "proposal_time",
            "created": "creation_time",
            "destroyed": "destruction_time",
        }[kind.rsplit("_", maxsplit=1)[1]]
        columns_by_table = {
            "letters": (
                "parent_codelet_id",
                "string_id",
                "position",
                "letter_category",
            ),
            "descriptions": (
                "parent_codelet_id",
                "object_id",
                "facet",
                "descriptor",
            ),
            "bonds": (
                "parent_codelet_id",
                "string_id",
                "source_id",
                "target_id",
                "bond_category",
                "direction_category",
                "bond_facet",
                "source_descriptor",
                "target_descriptor",
            ),
            "groups": (
                "parent_codelet_id",
                "string_id",
                "group_category",
                "direction_category",
                "bond_category",
                "bond_facet",
                "left_position",
                "right_position",
            ),
            "correspondences": ("parent_codelet_id", "source_id", "target_id"),
            "replacements": (
                "parent_codelet_id",
                "source_id",
                "target_id",
            ),
            "rules": (
                "parent_codelet_id",
                "object_category_1",
                "descriptor_1_facet",
                "descriptor_1",
                "object_category_2",
                "descriptor_2",
                "replaced_description_type",
                "relation",
            ),
            "translated_rules": (
                "parent_codelet_id",
                "object_category_1",
                "descriptor_1_facet",
                "descriptor_1",
                "object_category_2",
                "descriptor_2",
                "replaced_description_type",
                "relation",
            ),
        }
        detail_columns = columns_by_table[table]
        id_column = f"{entity}_id"
        columns = ("run_id", id_column, *detail_columns, time_column)
        values = [
            run_id,
            entity_id,
            *(data.get(column) for column in detail_columns),
            data.get("time"),
        ]
        assignments = ", ".join(
            f"{column} = excluded.{column}" for column in (*detail_columns, time_column)
        )
        placeholders = ", ".join("?" for _ in values)
        self._connection.execute(
            f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders}) "
            f"ON CONFLICT(run_id, {id_column}) DO UPDATE SET {assignments}",
            values,
        )
        row = self._connection.execute(
            f"SELECT id FROM {table} WHERE run_id = ? AND {id_column} = ?",
            (run_id, entity_id),
        ).fetchone()
        return None if row is None else int(row[0])

    def _replace_group_members(self, group_id: int, members: Any) -> None:
        self._connection.execute(
            "DELETE FROM group_members WHERE group_id = ?", (group_id,)
        )
        self._connection.executemany(
            "INSERT INTO group_members "
            "(group_id, object_id, member_order) VALUES (?, ?, ?)",
            ((group_id, str(member), index) for index, member in enumerate(members)),
        )

    def _replace_group_bonds(self, group_id: int, bonds: Any) -> None:
        self._connection.execute(
            "DELETE FROM group_bonds WHERE group_id = ?", (group_id,)
        )
        self._connection.executemany(
            "INSERT INTO group_bonds (group_id, bond_id, bond_order) VALUES (?, ?, ?)",
            ((group_id, str(bond), index) for index, bond in enumerate(bonds)),
        )

    def _upsert_concept_mapping(self, run_id: int, data: Mapping[str, Any]) -> None:
        self._connection.execute(
            """INSERT INTO concept_mappings
               (run_id, concept_mapping_id, correspondence_id,
                description_type_1, description_type_2,
                initial_descriptor, target_descriptor, label)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(run_id, concept_mapping_id) DO UPDATE SET
               correspondence_id = excluded.correspondence_id,
               description_type_1 = excluded.description_type_1,
               description_type_2 = excluded.description_type_2,
               initial_descriptor = excluded.initial_descriptor,
               target_descriptor = excluded.target_descriptor,
               label = excluded.label""",
            (
                run_id,
                str(data["concept_mapping_id"]),
                data.get("correspondence_id"),
                data.get("description_type_1"),
                data.get("description_type_2"),
                data.get("initial_descriptor"),
                data.get("target_descriptor"),
                data.get("label"),
            ),
        )

    def _upsert_slipnode(self, run_id: int, data: Mapping[str, Any]) -> None:
        column_names = (
            "name",
            "conceptual_depth",
            "depth_factor",
            "intrinsic_link_length",
            "shrunk_link_length",
            "category_links_json",
            "instance_links_json",
            "has_property_links_json",
            "lateral_sliplinks_json",
            "lateral_non_sliplinks_json",
            "incoming_links_json",
        )
        columns = ", ".join(column_names)
        values = [
            data["name"],
            data.get("conceptual_depth"),
            data.get("depth_factor"),
            data.get("intrinsic_link_length"),
            data.get("shrunk_link_length"),
        ]
        values.extend(
            self._json(data.get(key, []))
            for key in (
                "category_links",
                "instance_links",
                "has_property_links",
                "lateral_sliplinks",
                "lateral_non_sliplinks",
                "incoming_links",
            )
        )
        placeholders = ", ".join("?" for _ in range(len(values) + 1))
        self._connection.execute(
            f"INSERT INTO slipnodes (run_id, {columns}) VALUES ({placeholders}) "
            "ON CONFLICT(run_id, name) DO UPDATE SET "
            + ", ".join(f"{column} = excluded.{column}" for column in column_names[1:]),
            [run_id, *values],
        )

    def _insert_sliplink(self, run_id: int, data: Mapping[str, Any]) -> None:
        self._connection.execute(
            """INSERT INTO sliplinks (run_id, source, target, label, fixed_length,
               is_category_link, is_instance_link, is_has_property_link,
               is_lateral_sliplink, is_lateral_non_sliplink)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run_id,
                data["source"],
                data["target"],
                data.get("label"),
                data.get("fixed_length"),
                int(bool(data.get("is_category_link"))),
                int(bool(data.get("is_instance_link"))),
                int(bool(data.get("is_has_property_link"))),
                int(bool(data.get("is_lateral_sliplink"))),
                int(bool(data.get("is_lateral_non_sliplink"))),
            ),
        )
