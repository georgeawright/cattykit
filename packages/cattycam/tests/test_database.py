import sqlite3

from cattycam.database import (
    codelet_history,
    coderack_codelets,
    run_overview_series,
    table_documentation,
    table_names,
    table_rows,
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
            "(id INTEGER PRIMARY KEY, run_id INTEGER, codelet_type TEXT, "
            "urgency_bin INTEGER, birth_time INTEGER, removal_time INTEGER)"
        )
        connection.executemany(
            "INSERT INTO codelets "
            "(run_id, codelet_type, urgency_bin, birth_time, removal_time) "
            "VALUES (?, ?, ?, ?, ?)",
            [
                (1, "Low", 1, 0, None),
                (1, "High", 4, 1, None),
                (1, "Removed", 6, 0, 2),
                (2, "Other run", 7, 0, None),
            ],
        )

    assert coderack_codelets(database, 1, time=2) == [(4, "High"), (1, "Low")]


def test_codelet_history_filters_by_time_and_orders_newest_first(tmp_path) -> None:
    database = tmp_path / "history.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE codelets "
            "(id INTEGER PRIMARY KEY, run_id INTEGER, run_time INTEGER, "
            "codelet_type TEXT, urgency_bin INTEGER, result TEXT, fizzle_reason TEXT)"
        )
        connection.executemany(
            "INSERT INTO codelets "
            "(run_id, run_time, codelet_type, urgency_bin, result, fizzle_reason) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [
                (1, 1, "Scout", 2, "fizzle", "no match"),
                (1, 3, "Builder", 4, "finish", None),
                (1, 4, "Later", 6, "finish", None),
                (2, 5, "Other run", 7, "finish", None),
            ],
        )

    assert codelet_history(database, 1, time=3) == [
        (3, "Builder", 4, "finish", None),
        (1, "Scout", 2, "fizzle", "no match"),
    ]
