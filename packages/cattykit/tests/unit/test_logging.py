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


def test_sqlite_logger_creates_the_cattycam_schema(tmp_path) -> None:
    database = tmp_path / "cattycam.sqlite"
    logger = SQLiteLogger(database)
    logger.close()

    with sqlite3.connect(database) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

    assert tables >= {
        "runs",
        "codelets",
        "strings",
        "letters",
        "descriptions",
        "bonds",
        "groups",
        "group_members",
        "group_bonds",
        "correspondences",
        "concept_mappings",
        "replacements",
        "rules",
        "slipnodes",
        "sliplinks",
        "attribute_values",
    }


def test_sqlite_logger_populates_cattycam_run_history(tmp_path) -> None:
    database = tmp_path / "cattycam.sqlite"
    logger = SQLiteLogger(database)

    logger.log(
        ModelEvent.create("copycat", "run_started", problem="abc -> abd ==> ijk -> ?")
    )
    logger.log(
        ModelEvent.create(
            "copycat",
            "string_initialized",
            string_id="initial",
            role="initial",
            value="abc",
        )
    )
    logger.log(
        ModelEvent.create(
            "copycat",
            "codelet_selected",
            codelet_id="c-1",
            codelet_type="BottomUpBondScout",
            urgency_bin=2,
            birth_time=0,
            time=1,
        )
    )
    logger.log(
        ModelEvent.create(
            "copycat",
            "codelet_finished",
            codelet_id="c-1",
            outcome="fizzle",
            reason="no_bond",
            time=1,
        )
    )
    logger.log(ModelEvent.create("copycat", "snag_encountered", time=2))
    logger.log(ModelEvent.create("copycat", "answer_found", answer="ijl", time=3))
    logger.log(
        ModelEvent.create(
            "copycat", "run_finished", codelets_run=3, temperature=0.25, time=3
        )
    )
    logger.close()

    with sqlite3.connect(database) as connection:
        run = connection.execute(
            "SELECT problem, solution, final_temperature, "
            "number_of_codelets_run, number_of_snags FROM runs"
        ).fetchone()
        string = connection.execute(
            "SELECT string_id, role, value FROM strings"
        ).fetchone()
        codelet = connection.execute(
            "SELECT codelet_id, codelet_type, urgency_bin, birth_time, run_time, "
            "result, fizzle_reason FROM codelets"
        ).fetchone()

    assert run == ("abc -> abd ==> ijk -> ?", "ijl", 0.25, 3, 1)
    assert string == ("initial", "initial", "abc")
    assert codelet == ("c-1", "BottomUpBondScout", 2, 0, 1, "fizzle", "no_bond")


def test_sqlite_logger_attaches_its_codelet_time_to_untimed_events(tmp_path) -> None:
    database = tmp_path / "cattycam.sqlite"
    logger = SQLiteLogger(database)

    logger.log(ModelEvent.create("copycat", "run_started", problem="abc -> abd"))
    logger.log(
        ModelEvent.create(
            "copycat",
            "attribute_updated",
            object_id="temperature",
            attribute="value",
            value=100.0,
        )
    )
    logger.log(
        ModelEvent.create(
            "copycat",
            "codelet_selected",
            codelet_id="c-1",
            codelet_type="BottomUpBondScout",
        )
    )
    logger.log(
        ModelEvent.create(
            "copycat",
            "attribute_updated",
            object_id="temperature",
            attribute="value",
            value=90.0,
        )
    )
    logger.close()

    with sqlite3.connect(database) as connection:
        attribute_times = connection.execute(
            "SELECT time FROM attribute_values ORDER BY id"
        ).fetchall()
        codelet_time = connection.execute("SELECT run_time FROM codelets").fetchone()

    assert attribute_times == [(0,), (1,)]
    assert codelet_time == (1,)
    assert logger.codelets_run == 1


def test_sqlite_logger_updates_a_posted_codelet_when_selected(tmp_path) -> None:
    database = tmp_path / "cattycam.sqlite"
    logger = SQLiteLogger(database)
    logger.log(ModelEvent.create("copycat", "run_started", problem="abc -> abd"))
    logger.log(
        ModelEvent.create(
            "copycat",
            "codelet_posted",
            codelet_id="codelet:1",
            codelet_type="BottomUpBondScout",
            urgency_bin=2,
            birth_time=0,
        )
    )
    logger.log(
        ModelEvent.create(
            "copycat",
            "codelet_selected",
            codelet_id="codelet:1",
            codelet_type="BottomUpBondScout",
            urgency_bin=2,
            birth_time=0,
            time=4,
        )
    )
    logger.close()

    with sqlite3.connect(database) as connection:
        codelets = connection.execute(
            "SELECT codelet_id, birth_time, run_time FROM codelets"
        ).fetchall()

    assert codelets == [("codelet:1", 0, 4)]


def test_sqlite_logger_assigns_selected_codelet_as_parent_of_new_posts(
    tmp_path,
) -> None:
    database = tmp_path / "cattycam.sqlite"
    logger = SQLiteLogger(database)
    logger.log(ModelEvent.create("copycat", "run_started", problem="abc -> abd"))
    logger.log(
        ModelEvent.create(
            "copycat",
            "codelet_posted",
            codelet_id="codelet:parent",
            codelet_type="BondScout",
            urgency_bin=2,
        )
    )
    logger.log(
        ModelEvent.create(
            "copycat",
            "codelet_selected",
            codelet_id="codelet:parent",
            codelet_type="BondScout",
            urgency_bin=2,
            time=1,
        )
    )
    logger.log(
        ModelEvent.create(
            "copycat",
            "codelet_posted",
            codelet_id="codelet:child",
            codelet_type="BondStrengthTester",
            urgency_bin=3,
            parent_codelet_id="codelet:incorrect-parent",
        )
    )
    logger.close()

    with sqlite3.connect(database) as connection:
        parent_id = connection.execute(
            "SELECT parent_codelet_id FROM codelets WHERE codelet_id = 'codelet:child'"
        ).fetchone()

    assert parent_id == ("codelet:parent",)


def test_sqlite_logger_populates_typed_workspace_tables(tmp_path) -> None:
    database = tmp_path / "cattycam.sqlite"
    logger = SQLiteLogger(database)
    logger.log(ModelEvent.create("copycat", "run_started", problem="abc -> abd"))
    logger.log(
        ModelEvent.create(
            "copycat",
            "letter_created",
            letter_id="initial-0",
            string_id="initial",
            position=0,
            letter_category="a",
            time=0,
        )
    )
    logger.log(
        ModelEvent.create(
            "copycat",
            "bond_created",
            bond_id="bond-1",
            string_id="initial",
            source_id="initial-0",
            target_id="initial-1",
            bond_category="successor",
            direction_category="right",
            time=1,
        )
    )
    logger.log(
        ModelEvent.create(
            "copycat",
            "group_created",
            group_id="group-1",
            string_id="initial",
            group_category="successor_group",
            members=["initial-0", "initial-1"],
            time=2,
        )
    )
    logger.log(
        ModelEvent.create(
            "copycat",
            "correspondence_created",
            correspondence_id="correspondence-1",
            source_id="initial-0",
            target_id="modified-0",
            time=3,
        )
    )
    logger.log(
        ModelEvent.create(
            "copycat",
            "concept_mapping_created",
            concept_mapping_id="mapping-1",
            correspondence_id="correspondence-1",
            description_type_1="letter_category",
            description_type_2="letter_category",
            initial_descriptor="a",
            target_descriptor="b",
            label="successor",
        )
    )
    logger.close()

    with sqlite3.connect(database) as connection:
        letter = connection.execute(
            "SELECT letter_id, string_id, position, letter_category FROM letters"
        ).fetchone()
        bond = connection.execute(
            "SELECT source_id, target_id, bond_category, direction_category FROM bonds"
        ).fetchone()
        members = connection.execute(
            "SELECT object_id, member_order FROM group_members ORDER BY member_order"
        ).fetchall()
        mapping = connection.execute(
            "SELECT correspondence_id, initial_descriptor, target_descriptor, label "
            "FROM concept_mappings"
        ).fetchone()

    assert letter == ("initial-0", "initial", 0, "a")
    assert bond == ("initial-0", "initial-1", "successor", "right")
    assert members == [("initial-0", 0), ("initial-1", 1)]
    assert mapping == ("correspondence-1", "a", "b", "successor")
