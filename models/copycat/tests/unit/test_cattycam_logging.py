import sqlite3
from pathlib import Path

from cattykit.logging import SQLiteLogger
from copycat import Copycat
from copycat.codelets import ReplacementFinder


CONFIG_DIRECTORY = Path(__file__).parents[2] / "copycat/configs"


def test_copycat_logs_initial_workspace_and_slipnet_state(tmp_path) -> None:
    database = tmp_path / "history.sqlite"
    logger = SQLiteLogger(database, "copycat")
    copycat = Copycat.from_json(
        str(CONFIG_DIRECTORY / "slipnet.json"),
        str(CONFIG_DIRECTORY / "coderack.json"),
        str(CONFIG_DIRECTORY / "hyperparameters.json"),
        logger=logger,
    )

    logger.log("run_started", problem="abc -> abd ==> ijk")
    copycat.workspace.initialize("abc -> abd ==> ijk -> ?", copycat.slipnet)
    copycat.slipnet.initialize()
    copycat.workspace.update()
    copycat.slipnet.update_activations()
    logger.close()

    with sqlite3.connect(database) as connection:
        counts = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
                "letters",
                "descriptions",
                "slipnodes",
                "slipnode_link_arguments",
                "sliplinks",
                "attribute_values",
            )
        }
        activation = connection.execute(
            "SELECT value_json FROM attribute_values "
            "WHERE object_id = 'slipnode:letter_category' AND attribute = 'activation'"
        ).fetchone()
        link_argument_counts = dict(
            connection.execute(
                """SELECT link_collection, COUNT(*)
                   FROM slipnode_link_arguments
                   GROUP BY link_collection"""
            )
        )
        slipnode_columns = {
            column[1] for column in connection.execute("PRAGMA table_info(slipnodes)")
        }

    assert counts["letters"] == 9
    assert counts["descriptions"] == 27
    assert counts["slipnodes"] > 0
    assert counts["slipnode_link_arguments"] > 0
    assert counts["sliplinks"] > 0
    assert counts["attribute_values"] > 0
    assert activation is not None
    assert link_argument_counts.keys() == {
        "category_links",
        "instance_links",
        "has_property_links",
        "lateral_sliplinks",
        "lateral_non_sliplinks",
        "incoming_links",
    }
    assert all(count > 0 for count in link_argument_counts.values())
    assert not {column for column in slipnode_columns if column.endswith("_json")}


def test_workspace_logs_the_structure_a_codelet_builds(tmp_path, monkeypatch) -> None:
    database = tmp_path / "history.sqlite"
    logger = SQLiteLogger(database, "copycat")
    copycat = Copycat.from_json(
        str(CONFIG_DIRECTORY / "slipnet.json"),
        str(CONFIG_DIRECTORY / "coderack.json"),
        str(CONFIG_DIRECTORY / "hyperparameters.json"),
        logger=logger,
    )
    copycat.workspace.initialize("abc -> abd ==> ijk -> ?", copycat.slipnet)
    codelet = ReplacementFinder(
        urgency_bin=2,
        coderack=copycat.coderack,
        workspace=copycat.workspace,
        slipnet=copycat.slipnet,
    )
    monkeypatch.setattr(
        "copycat.codelets.replacement_finder.random.choice",
        lambda _: copycat.workspace.initial_string.letters[2],
    )

    logger.log("run_started", problem="abc -> abd")
    codelet.run(temperature=1.0)
    logger.close()

    with sqlite3.connect(database) as connection:
        replacement = connection.execute(
            "SELECT source_id, target_id, creation_time FROM replacements"
        ).fetchone()

    assert replacement is not None
    assert replacement[0].startswith("letter:")
    assert replacement[1].startswith("letter:")
    assert replacement[2] == 0


def test_coderack_logs_a_codelet_when_it_is_posted(tmp_path) -> None:
    database = tmp_path / "history.sqlite"
    logger = SQLiteLogger(database, "copycat")
    copycat = Copycat.from_json(
        str(CONFIG_DIRECTORY / "slipnet.json"),
        str(CONFIG_DIRECTORY / "coderack.json"),
        str(CONFIG_DIRECTORY / "hyperparameters.json"),
        logger=logger,
    )
    codelet = ReplacementFinder(
        urgency_bin=2,
        coderack=copycat.coderack,
        workspace=copycat.workspace,
        slipnet=copycat.slipnet,
    )

    logger.log("run_started", problem="abc -> abd")
    copycat.coderack.post(codelet, temperature=1.0)
    logger.close()

    with sqlite3.connect(database) as connection:
        posted_codelet = connection.execute(
            "SELECT codelet_id, codelet_type, urgency_bin, birth_time, run_time "
            "FROM codelets"
        ).fetchone()

    assert posted_codelet == (
        f"codelet:{codelet.hash_id}",
        "ReplacementFinder",
        2,
        0,
        None,
    )
