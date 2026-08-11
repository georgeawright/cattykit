from __future__ import annotations

import json
import sqlite3
from io import StringIO

from cattykit.logging import ModelEvent, NullLogger, PrintLogger, SQLiteLogger


def test_null_logger_discards_events() -> None:
    logger = NullLogger()

    logger.log(ModelEvent.create("test", "started"))
    logger.close()


def test_print_logger_writes_json_to_its_stream() -> None:
    stream = StringIO()
    logger = PrintLogger(stream)

    logger.log(ModelEvent.create("test", "started", seed=1234))

    event = json.loads(stream.getvalue())

    assert event["data"] == {"seed": 1234}
    assert event["kind"] == "started"
    assert event["model"] == "test"
    assert event["timestamp"].endswith("+00:00")


def test_sqlite_logger_persists_events(tmp_path) -> None:
    database = tmp_path / "events.sqlite"
    logger = SQLiteLogger(database)

    logger.log(ModelEvent.create("test", "started", seed=1234))
    logger.close()

    with sqlite3.connect(database) as connection:
        row = connection.execute(
            "SELECT model, kind, data_json FROM events"
        ).fetchone()

    assert row == ("test", "started", '{"seed": 1234}')
