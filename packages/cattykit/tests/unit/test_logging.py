from __future__ import annotations

import json
import sqlite3
from types import SimpleNamespace
from io import StringIO

from cattykit.logging import NullLogger, PrintLogger, SQLiteLogger


def test_logger_assigns_serial_identifiers_to_domain_objects() -> None:
    class Codelet:
        hash_id = 7

    class Letter:
        hash_id = 3
        value = 1

    class Slipnode:
        name = "letter_category"

    logger = NullLogger("copycat")

    assert logger.codelet_id(Codelet()) == "codelet:7"
    assert logger.object_id(Letter()) == "letter:3"
    assert logger.entity_id("slipnode", Slipnode()) == "slipnode:letter_category"


def test_null_logger_discards_events() -> None:
    logger = NullLogger("copycat")

    logger.log("started")
    logger.close()


def test_print_logger_writes_json_to_its_stream() -> None:
    stream = StringIO()
    logger = PrintLogger("test", stream)

    logger.log("started", seed=1234)

    event = json.loads(stream.getvalue())

    assert event["data"] == {"seed": 1234}
    assert event["kind"] == "started"
    assert event["model"] == "test"
    assert event["timestamp"].endswith("+00:00")


def test_print_logger_serializes_domain_objects() -> None:
    class Letter:
        hash_id = 3
        value = 1

    stream = StringIO()
    logger = PrintLogger("test", stream)

    logger.log("attribute_updated", object=Letter(), attribute="value")

    assert json.loads(stream.getvalue())["data"]["object_id"] == "letter:3"


def test_print_logger_serializes_object_attribute_values() -> None:
    class Rule:
        hash_id = 4

    class Codelet:
        hash_id = 3
        proposed_rule = Rule()

    stream = StringIO()
    logger = PrintLogger("test", stream)

    logger.log("attribute_updated", object=Codelet(), attribute="proposed_rule")

    assert json.loads(stream.getvalue())["data"]["value"] == "rule:4"


def test_print_logger_serializes_codelet_steps() -> None:
    class Letter:
        hash_id = 4

    class Codelet:
        hash_id = 3
        source = Letter()

    stream = StringIO()
    logger = PrintLogger("test", stream)

    logger.log("codelet_step", codelet=Codelet(), attribute="source")

    assert json.loads(stream.getvalue())["data"] == {
        "attribute": "source",
        "codelet_id": "codelet:3",
        "value": "letter:4",
    }


def test_sqlite_logger_creates_the_cattycam_schema(tmp_path) -> None:
    database = tmp_path / "cattycam.sqlite"
    logger = SQLiteLogger(database, "copycat")
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
        "translated_rules",
        "slipnodes",
        "slipnode_link_arguments",
        "sliplinks",
        "attribute_values",
        "codelet_arguments",
        "codelet_steps",
    }


def test_sqlite_logger_populates_cattycam_run_history(tmp_path, monkeypatch) -> None:
    database = tmp_path / "cattycam.sqlite"
    logger = SQLiteLogger(database, "copycat")
    monkeypatch.setattr(
        "cattykit.logging.sqlite_logger.perf_counter_ns", lambda: 10_000_000_000
    )

    logger.log("run_started", problem="abc -> abd ==> ijk -> ?", seed=1234)
    logger.log("string_initialized", string_id="initial", role="initial", value="abc")
    logger.log("codelet_selected", codelet_id="c-1", codelet_type="BottomUpBondScout", urgency_bin=2, birth_time=0, time=1)
    monkeypatch.setattr(
        "cattykit.logging.sqlite_logger.perf_counter_ns", lambda: 10_125_000_000
    )
    logger.log("codelet_finished", codelet_id="c-1", outcome="fizzle", reason="no_bond", time=1)
    logger.log("snag_encountered", time=2)
    logger.log("answer_found", answer="ijl", time=3)
    logger.log("run_finished", codelets_run=3, temperature=0.25, time=3)
    logger.close()

    with sqlite3.connect(database) as connection:
        run = connection.execute(
            "SELECT problem, seed, solution, final_temperature, "
            "number_of_codelets_run, number_of_snags FROM runs"
        ).fetchone()
        string = connection.execute(
            "SELECT string_id, role, value FROM strings"
        ).fetchone()
        codelet = connection.execute(
            "SELECT codelet_id, codelet_type, urgency_bin, birth_time, run_time, time_taken, "
            "result, fizzle_reason FROM codelets"
        ).fetchone()

    assert run == ("abc -> abd ==> ijk -> ?", 1234, "ijl", 0.25, 3, 1)
    assert string == ("initial", "initial", "abc")
    assert codelet == ("c-1", "BottomUpBondScout", 2, 0, 1, 125_000_000, "fizzle", "no_bond")


def test_sqlite_logger_records_a_posted_codelets_proposed_structure(tmp_path) -> None:
    database = tmp_path / "cattycam.sqlite"
    logger = SQLiteLogger(database, "copycat")
    proposed_structure = SimpleNamespace(hash_id="bond-1")
    codelet = SimpleNamespace(
        hash_id="codelet-1",
        urgency_bin=2,
        birth_time=0,
        proposed_structure=proposed_structure,
    )

    logger.log("run_started", problem="abc -> abd")
    logger.log("codelet_posted", codelet=codelet)
    logger.close()

    with sqlite3.connect(database) as connection:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(codelets)")
        }
        argument = connection.execute(
            "SELECT codelet_id, attribute, value_json FROM codelet_arguments"
        ).fetchone()

    assert "arguments_json" not in columns
    assert argument == (
        "codelet:codelet-1",
        "proposed_structure",
        '"simplenamespace:bond-1"',
    )


def test_sqlite_logger_excludes_codelet_step_logging_time_from_time_taken(
    tmp_path, monkeypatch
) -> None:
    database = tmp_path / "cattycam.sqlite"
    logger = SQLiteLogger(database, "copycat")
    logger.log("run_started", problem="abc -> abd")
    timestamps = iter([100, 200, 300, 400, 1_000])
    monkeypatch.setattr(
        "cattykit.logging.sqlite_logger.perf_counter_ns", lambda: next(timestamps)
    )

    logger.log("codelet_selected", codelet_id="c-1", codelet_type="Scout")
    logger.log("codelet_step", codelet_id="c-1", attribute="candidate", value="a")
    logger.log("codelet_finished", codelet_id="c-1", outcome="finish")
    logger.close()

    with sqlite3.connect(database) as connection:
        time_taken = connection.execute("SELECT time_taken FROM codelets").fetchone()

    assert time_taken == (700,)


def test_sqlite_logger_records_git_metadata_for_each_run(tmp_path, monkeypatch) -> None:
    database = tmp_path / "cattycam.sqlite"
    monkeypatch.setattr(
        SQLiteLogger,
        "_git_metadata",
        staticmethod(lambda: ("0123456789abcdef", True)),
    )
    logger = SQLiteLogger(database, "copycat")

    logger.log("run_started", seed=99)
    logger.close()

    with sqlite3.connect(database) as connection:
        run = connection.execute(
            "SELECT seed, commit_hash, has_uncommitted_changes FROM runs"
        ).fetchone()

    assert run == (99, "0123456789abcdef", 1)


def test_sqlite_logger_attaches_its_codelet_time_to_untimed_events(tmp_path) -> None:
    database = tmp_path / "cattycam.sqlite"
    logger = SQLiteLogger(database, "copycat")

    logger.log("run_started", problem="abc -> abd")
    logger.log("attribute_updated", object_id="temperature", attribute="value", value=100.0)
    logger.log("codelet_selected", codelet_id="c-1", codelet_type="BottomUpBondScout")
    logger.log("attribute_updated", object_id="temperature", attribute="value", value=90.0)
    logger.close()

    with sqlite3.connect(database) as connection:
        attribute_times = connection.execute(
            "SELECT time FROM attribute_values ORDER BY id"
        ).fetchall()
        codelet_time = connection.execute("SELECT run_time FROM codelets").fetchone()

    assert attribute_times == [(0,), (1,)]
    assert codelet_time == (1,)
    assert logger.codelets_run == 1


def test_sqlite_logger_records_ordered_codelet_steps(tmp_path) -> None:
    database = tmp_path / "cattycam.sqlite"
    logger = SQLiteLogger(database, "copycat")
    logger.log("run_started", problem="abc -> abd")
    logger.log("codelet_selected", codelet_id="codelet:1", codelet_type="Scout")
    logger.log(
        "codelet_step",
        codelet_id="codelet:1",
        attribute="source",
        value="letter:2",
    )
    logger.log(
        "codelet_step",
        codelet_id="codelet:1",
        attribute="target",
        value="letter:5",
    )
    logger.close()

    with sqlite3.connect(database) as connection:
        steps = connection.execute(
            "SELECT time, codelet_id, attribute, value_json FROM codelet_steps ORDER BY id"
        ).fetchall()

    assert steps == [
        (1, "codelet:1", "source", '"letter:2"'),
        (1, "codelet:1", "target", '"letter:5"'),
    ]


def test_sqlite_logger_records_translated_rules_separately(tmp_path) -> None:
    database = tmp_path / "cattycam.sqlite"
    logger = SQLiteLogger(database, "copycat")
    logger.log("run_started", problem="abc -> abd")
    logger.log("translated_rule_created", rule_id="rule:translated:1", source_object_category="letter", source_descriptor="rightmost", replaced_facet="letter_category", relation="successor", time=4)
    logger.close()

    with sqlite3.connect(database) as connection:
        translated_rule = connection.execute(
            "SELECT rule_id, source_descriptor, relation, creation_time FROM translated_rules"
        ).fetchone()

    assert translated_rule == ("rule:translated:1", "rightmost", "successor", 4)


def test_sqlite_logger_updates_a_posted_codelet_when_selected(tmp_path) -> None:
    database = tmp_path / "cattycam.sqlite"
    logger = SQLiteLogger(database, "copycat")
    logger.log("run_started", problem="abc -> abd")
    logger.log("codelet_posted", codelet_id="codelet:1", codelet_type="BottomUpBondScout", urgency_bin=2, birth_time=0)
    logger.log("codelet_selected", codelet_id="codelet:1", codelet_type="BottomUpBondScout", urgency_bin=2, birth_time=0, time=4)
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
    logger = SQLiteLogger(database, "copycat")
    logger.log("run_started", problem="abc -> abd")
    logger.log("codelet_posted", codelet_id="codelet:parent", codelet_type="BondScout", urgency_bin=2)
    logger.log("codelet_selected", codelet_id="codelet:parent", codelet_type="BondScout", urgency_bin=2, time=1)
    logger.log("codelet_posted", codelet_id="codelet:child", codelet_type="BondStrengthTester", urgency_bin=3, parent_codelet_id="codelet:incorrect-parent")
    logger.close()

    with sqlite3.connect(database) as connection:
        parent_id = connection.execute(
            "SELECT parent_codelet_id FROM codelets WHERE codelet_id = 'codelet:child'"
        ).fetchone()

    assert parent_id == ("codelet:parent",)


def test_sqlite_logger_populates_typed_workspace_tables(tmp_path) -> None:
    database = tmp_path / "cattycam.sqlite"
    logger = SQLiteLogger(database, "copycat")
    logger.log("run_started", problem="abc -> abd")
    logger.log("letter_created", letter_id="initial-0", string_id="initial", position=0, letter_category="a", time=0)
    logger.log("bond_created", bond_id="bond-1", string_id="initial", source_id="initial-0", target_id="initial-1", bond_category="successor", direction_category="right", time=1)
    logger.log("group_created", group_id="group-1", string_id="initial", group_category="successor_group", members=["initial-0", "initial-1"], time=2)
    logger.log("correspondence_created", correspondence_id="correspondence-1", source_id="initial-0", target_id="modified-0", time=3)
    logger.log("concept_mapping_created", concept_mapping_id="mapping-1", correspondence_id="correspondence-1", source_facet="letter_category", target_facet="letter_category", source_descriptor="a", target_descriptor="b", label="successor")
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
            "SELECT correspondence_id, source_descriptor, target_descriptor, label "
            "FROM concept_mappings"
        ).fetchone()

    assert letter == ("initial-0", "initial", 0, "a")
    assert bond == ("initial-0", "initial-1", "successor", "right")
    assert members == [("initial-0", 0), ("initial-1", 1)]
    assert mapping == ("correspondence-1", "a", "b", "successor")
