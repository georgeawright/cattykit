import sqlite3
from pathlib import Path

from cattykit.logging import ModelEvent, SQLiteLogger
from copycat import Copycat
from copycat.codelets import ReplacementFinder


CONFIG_DIRECTORY = Path(__file__).parents[2] / "configs"


def test_copycat_logs_initial_workspace_and_slipnet_state(tmp_path) -> None:
    database = tmp_path / "history.sqlite"
    logger = SQLiteLogger(database)
    copycat = Copycat.from_json(
        str(CONFIG_DIRECTORY / "slipnet.json"),
        str(CONFIG_DIRECTORY / "coderack.json"),
        str(CONFIG_DIRECTORY / "hyperparameters.json"),
        logger=logger,
    )

    logger.log(
        ModelEvent.create("copycat", "run_started", problem="abc -> abd ==> ijk")
    )
    copycat._add_letters_to_workspace("abc -> abd ==> ijk -> ?")
    copycat._add_initial_descriptions_to_workspace()
    copycat.slipnet.log_definition()
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
                "sliplinks",
                "attribute_values",
            )
        }
        activation = connection.execute(
            "SELECT value_json FROM attribute_values "
            "WHERE object_id = 'slipnode:letter_category' AND attribute = 'activation'"
        ).fetchone()

    assert counts["letters"] == 9
    assert counts["descriptions"] == 27
    assert counts["slipnodes"] > 0
    assert counts["sliplinks"] > 0
    assert counts["attribute_values"] > 0
    assert activation is not None


def test_workspace_logs_the_structure_a_codelet_builds(tmp_path, monkeypatch) -> None:
    database = tmp_path / "history.sqlite"
    logger = SQLiteLogger(database)
    copycat = Copycat.from_json(
        str(CONFIG_DIRECTORY / "slipnet.json"),
        str(CONFIG_DIRECTORY / "coderack.json"),
        str(CONFIG_DIRECTORY / "hyperparameters.json"),
        logger=logger,
    )
    copycat._add_letters_to_workspace("abc -> abd ==> ijk -> ?")
    copycat._add_initial_descriptions_to_workspace()
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

    logger.log(ModelEvent.create("copycat", "run_started", problem="abc -> abd"))
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
