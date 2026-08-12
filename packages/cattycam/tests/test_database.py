import sqlite3

from cattycam.database import (
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
