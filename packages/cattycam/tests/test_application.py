from cattycam.application import _database_revision


def test_database_revision_includes_sqlite_wal_changes(tmp_path) -> None:
    database = tmp_path / "history.sqlite"
    database.write_text("database")
    original = _database_revision(database)

    wal = tmp_path / "history.sqlite-wal"
    wal.write_text("first transaction")

    assert _database_revision(database) != original
