import sqlite3

from cattycam.database import (
    codelet_history,
    codelet_types,
    coderack_codelets,
    run_overview_series,
    table_documentation,
    table_names,
    table_rows,
    workspace_snapshot,
)


def test_table_documentation_shows_escaped_rows_without_schema(tmp_path) -> None:
    database = tmp_path / "history.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE runs (id INTEGER PRIMARY KEY, problem TEXT)")
        connection.execute("INSERT INTO runs (problem) VALUES (?)", ("a < b",))

    assert table_names(database) == ["runs"]

    documentation = table_documentation(database, "runs")

    assert "<h2>runs</h2>" in documentation
    assert "<th>problem</th>" in documentation
    assert "a &lt; b" in documentation
    assert "<h3>Columns</h3>" not in documentation


def test_table_rows_filters_tables_to_a_single_run(tmp_path) -> None:
    database = tmp_path / "history.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE runs (id INTEGER PRIMARY KEY, problem TEXT)")
        connection.execute("CREATE TABLE letters (run_id INTEGER, letter_id TEXT)")
        connection.executemany(
            "INSERT INTO runs (id, problem) VALUES (?, ?)",
            [(1, "first"), (2, "second")],
        )
        connection.executemany(
            "INSERT INTO letters (run_id, letter_id) VALUES (?, ?)",
            [(1, "a"), (2, "b")],
        )

    assert table_rows(database, "runs", run_id=2) == (
        ["id", "problem"],
        [(2, "second")],
    )
    assert table_rows(database, "letters", run_id=2) == (
        ["run_id", "letter_id"],
        [(2, "b")],
    )


def test_run_overview_series_uses_attribute_and_lifecycle_history(tmp_path) -> None:
    database = tmp_path / "history.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE attribute_values "
            "(id INTEGER PRIMARY KEY, run_id INTEGER, time INTEGER, object_id TEXT, "
            "attribute TEXT, value_json TEXT)"
        )
        for table in (
            "letters",
            "groups",
            "bonds",
            "correspondences",
            "replacements",
            "rules",
        ):
            connection.execute(
                f"CREATE TABLE {table} "
                "(run_id INTEGER, creation_time INTEGER, destruction_time INTEGER)"
            )
        connection.executemany(
            "INSERT INTO attribute_values "
            "(run_id, time, object_id, attribute, value_json) VALUES (?, ?, ?, ?, ?)",
            [
                (1, 1, "coderack", "number_of_codelets_on_coderack", "12"),
                (1, 2, "temperature", "value", "0.5"),
            ],
        )
        connection.execute("INSERT INTO letters VALUES (1, 0, NULL)")
        connection.execute("INSERT INTO bonds VALUES (1, 1, 2)")

    assert run_overview_series(database, 1) == {
        "coderack": [(1, 12)],
        "temperature": [(2, 0.5)],
        "workspace": [(0, 2), (1, 3), (2, 2)],
    }


def test_coderack_codelets_returns_only_active_codelets_by_urgency(tmp_path) -> None:
    database = tmp_path / "history.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE codelets "
            "(id INTEGER PRIMARY KEY, run_id INTEGER, codelet_id TEXT, codelet_type TEXT, "
            "urgency_bin INTEGER, birth_time INTEGER, removal_time INTEGER)"
        )
        connection.executemany(
            "INSERT INTO codelets "
            "(run_id, codelet_id, codelet_type, urgency_bin, birth_time, removal_time) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [
                (1, "codelet:1", "Low", 1, 0, None),
                (1, "codelet:2", "High", 4, 1, None),
                (1, "codelet:3", "Removed", 6, 0, 2),
                (2, "codelet:4", "Other run", 7, 0, None),
            ],
        )

    assert coderack_codelets(database, 1, time=2) == [
        (4, "High", "codelet:2"),
        (1, "Low", "codelet:1"),
    ]


def test_codelet_history_filters_by_time_and_orders_newest_first(tmp_path) -> None:
    database = tmp_path / "history.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE codelets "
            "(id INTEGER PRIMARY KEY, run_id INTEGER, codelet_id TEXT, "
            "parent_codelet_id TEXT, run_time INTEGER, codelet_type TEXT, "
            "urgency_bin INTEGER, result TEXT, fizzle_reason TEXT)"
        )
        connection.executemany(
            "INSERT INTO codelets "
            "(run_id, codelet_id, parent_codelet_id, run_time, codelet_type, "
            "urgency_bin, result, fizzle_reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (1, "codelet:1", None, 1, "Scout", 2, "fizzle", "no match"),
                (1, "codelet:2", "codelet:1", 3, "Builder", 4, "finish", None),
                (1, "codelet:3", None, 4, "Later", 6, "finish", None),
                (2, "codelet:4", None, 5, "Other run", 7, "finish", None),
            ],
        )

    assert codelet_history(database, 1, time=3) == [
        ("codelet:2", "codelet:1", 3, "Builder", 4, "finish", None),
        ("codelet:1", None, 1, "Scout", 2, "fizzle", "no match"),
    ]
    assert codelet_types(database, 1) == {
        "codelet:1": "Scout",
        "codelet:2": "Builder",
        "codelet:3": "Later",
    }


def test_workspace_snapshot_includes_built_and_proposed_entities(tmp_path) -> None:
    database = tmp_path / "history.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE letters "
            "(run_id INTEGER, letter_id TEXT, string_id TEXT, position INTEGER, "
            "letter_category TEXT, creation_time INTEGER, destruction_time INTEGER)"
        )
        for table, identifier in (
            ("groups", "group_id"),
            ("bonds", "bond_id"),
            ("correspondences", "correspondence_id"),
        ):
            columns = (
                "string_id TEXT, left_position INTEGER, right_position INTEGER"
                if table == "groups"
                else "source_id TEXT, target_id TEXT"
            )
            connection.execute(
                f"CREATE TABLE {table} "
                f"(run_id INTEGER, {identifier} TEXT, {columns}, proposal_time INTEGER, "
                "creation_time INTEGER, destruction_time INTEGER)"
            )
        connection.executemany(
            "INSERT INTO letters VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (1, "letter:1", "initial", 0, "a", 0, None),
                (1, "letter:2", "initial", 1, "b", 0, None),
            ],
        )
        connection.execute(
            "INSERT INTO groups VALUES (1, 'group:1', 'initial', 0, 1, 2, NULL, NULL)"
        )
        connection.execute(
            "INSERT INTO bonds VALUES (1, 'bond:1', 'letter:1', 'letter:2', 1, 2, NULL)"
        )
        connection.execute(
            "INSERT INTO correspondences VALUES (1, 'correspondence:1', 'letter:1', 'letter:2', 2, NULL, NULL)"
        )

    snapshot = workspace_snapshot(database, 1, 2)

    assert [letter["value"] for letter in snapshot["letters"]] == ["a", "b"]
    assert snapshot["groups"][0]["proposed"] is True
    assert snapshot["bonds"][0]["proposed"] is False
    assert snapshot["correspondences"][0]["proposed"] is True
