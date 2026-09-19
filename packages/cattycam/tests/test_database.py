import sqlite3

from cattycam.database import (
    codelet_arguments,
    codelet_history,
    codelet_step_value_reprs,
    codelet_steps,
    codelet_types,
    coderack_codelets,
    object_history,
    object_display_reprs,
    run_current_time,
    run_component_revisions,
    run_overview_series,
    slipnet_snapshot,
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
        connection.execute(
            "CREATE TABLE snags (run_id INTEGER, snag_start INTEGER, snag_end INTEGER)"
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
        connection.execute("INSERT INTO snags VALUES (1, 1, 2)")

    assert run_overview_series(database, 1) == {
        "coderack": [(1, 12)],
        "temperature": [(2, 0.5)],
        "workspace": [(0, 2), (1, 3), (2, 2)],
        "snags": [(1, 2)],
    }


def test_run_current_time_uses_logged_codelets_before_a_run_finishes(tmp_path) -> None:
    database = tmp_path / "history.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE codelets (run_id INTEGER, run_time INTEGER)")
        connection.executemany(
            "INSERT INTO codelets VALUES (?, ?)", [(1, 2), (1, 7), (2, 9)]
        )

    assert run_current_time(database, 1) == 7
    assert run_current_time(database, 3) == 0


def test_run_component_revisions_ignore_changes_to_other_runs(tmp_path) -> None:
    database = tmp_path / "history.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE runs (id INTEGER PRIMARY KEY)")
        connection.execute("CREATE TABLE codelets (run_id INTEGER, run_time INTEGER)")
        connection.execute(
            """CREATE TABLE attribute_values
               (id INTEGER PRIMARY KEY, run_id INTEGER, time INTEGER, object_id TEXT,
                attribute TEXT, value_json TEXT)"""
        )
        connection.execute("INSERT INTO runs VALUES (1)")
        connection.execute("INSERT INTO runs VALUES (2)")
        connection.commit()
        before = run_component_revisions(database, 1)
        connection.execute("INSERT INTO codelets VALUES (2, 1)")

    assert run_component_revisions(database, 1) == before


def test_object_history_groups_attributes_and_finds_lifecycle_boundaries(tmp_path) -> None:
    database = tmp_path / "history.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE runs (id INTEGER PRIMARY KEY, number_of_codelets_run INTEGER)"
        )
        connection.execute("INSERT INTO runs VALUES (1, 8)")
        connection.execute(
            "CREATE TABLE bonds (run_id INTEGER, bond_id TEXT, source_id TEXT, target_id TEXT, creation_time INTEGER, destruction_time INTEGER)"
        )
        connection.execute("INSERT INTO bonds VALUES (1, 'bond:1', 'letter:1', 'letter:2', 2, 6)")
        connection.execute(
            "CREATE TABLE attribute_values "
            "(id INTEGER PRIMARY KEY, run_id INTEGER, time INTEGER, object_id TEXT, attribute TEXT, value_json TEXT)"
        )
        connection.executemany(
            "INSERT INTO attribute_values (run_id, time, object_id, attribute, value_json) VALUES (?, ?, ?, ?, ?)",
            [
                (1, 2, "bond:1", "strength", "0.2"),
                (1, 4, "bond:1", "strength", "0.8"),
                (1, 2, "bond:1", "facet", '"letter_category"'),
            ],
        )

    assert object_history(database, 1, "bond:1") == {
        "id": "bond:1",
        "table": "bonds",
        "run_length": 8,
        "creation_time": 2,
        "destruction_time": 6,
        "proposal_time": None,
        "attributes": {
            "strength": [(2, 0.2), (4, 0.8)],
            "facet": [(2, "letter_category")],
        },
        "details": [
            ("source_id", "letter:1"),
            ("target_id", "letter:2"),
            ("creation_time", 2),
            ("destruction_time", 6),
        ],
        "group_members": [],
        "group_bonds": [],
        "concept_mappings": [],
        "slipnode_link_arguments": [],
    }


def test_object_history_includes_normalized_slipnode_link_arguments(tmp_path) -> None:
    database = tmp_path / "history.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE runs (id INTEGER PRIMARY KEY, number_of_codelets_run INTEGER)"
        )
        connection.execute("INSERT INTO runs VALUES (1, 0)")
        connection.execute(
            """CREATE TABLE attribute_values
               (id INTEGER PRIMARY KEY, run_id INTEGER, time INTEGER, object_id TEXT,
                attribute TEXT, value_json TEXT)"""
        )
        connection.execute(
            "CREATE TABLE slipnodes (id INTEGER PRIMARY KEY, run_id INTEGER, name TEXT)"
        )
        connection.execute(
            """CREATE TABLE slipnode_link_arguments
               (id INTEGER PRIMARY KEY, slipnode_id INTEGER, link_collection TEXT,
                source TEXT, target TEXT, label TEXT)"""
        )
        connection.execute("INSERT INTO slipnodes VALUES (8, 1, 'successor')")
        connection.execute(
            "INSERT INTO slipnode_link_arguments VALUES "
            "(1, 8, 'lateral_sliplinks', 'successor', 'predecessor', 'opposite')"
        )

    history = object_history(database, 1, "slipnode:successor")

    assert history is not None
    assert history["slipnode_link_arguments"] == [
        {
            "collection": "lateral_sliplinks",
            "source": "successor",
            "target": "predecessor",
            "label": "opposite",
        }
    ]


def test_object_table_rows_link_to_their_detail_page(tmp_path) -> None:
    database = tmp_path / "history.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE bonds (run_id INTEGER, bond_id TEXT)")
        connection.execute("INSERT INTO bonds VALUES (1, 'bond:1')")

    documentation = table_documentation(database, "bonds", run_id=1)

    assert "<th>View</th>" in documentation
    assert '?run_id=1&object_id=bond%3A1' in documentation


def test_object_display_reprs_labels_slipnodes_and_codelets(tmp_path) -> None:
    database = tmp_path / "history.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE slipnodes (run_id INTEGER, name TEXT)")
        connection.execute(
            "CREATE TABLE codelets (run_id INTEGER, codelet_id TEXT, codelet_type TEXT)"
        )
        connection.execute("INSERT INTO slipnodes VALUES (1, 'successor')")
        connection.execute("INSERT INTO codelets VALUES (1, 'codelet:9', 'BondBuilder')")

    assert object_display_reprs(database, 1) == {
        "slipnode:successor": "SUCCESSOR",
        "codelet:9": "BondBuilder 9",
    }


def test_coderack_codelets_returns_only_active_codelets_by_urgency(tmp_path) -> None:
    database = tmp_path / "history.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE codelets "
            "(id INTEGER PRIMARY KEY, run_id INTEGER, codelet_id TEXT, codelet_type TEXT, "
            "urgency_bin INTEGER, birth_time INTEGER, removal_time INTEGER)"
        )
        connection.execute(
            "CREATE TABLE snags "
            "(id INTEGER PRIMARY KEY, run_id INTEGER, snag_start INTEGER)"
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


def test_coderack_codelets_excludes_codelets_discarded_when_a_snag_clears_rack(
    tmp_path,
) -> None:
    database = tmp_path / "history.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE codelets "
            "(id INTEGER PRIMARY KEY, run_id INTEGER, codelet_id TEXT, "
            "codelet_type TEXT, urgency_bin INTEGER, birth_time INTEGER, "
            "removal_time INTEGER)"
        )
        connection.execute(
            "CREATE TABLE snags "
            "(id INTEGER PRIMARY KEY, run_id INTEGER, snag_start INTEGER)"
        )
        connection.executemany(
            "INSERT INTO codelets "
            "(run_id, codelet_id, codelet_type, urgency_bin, birth_time, removal_time) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [
                (1, "codelet:discarded", "Scout", 2, 3, None),
                (1, "codelet:new", "Builder", 4, 6, None),
            ],
        )
        connection.execute("INSERT INTO snags (run_id, snag_start) VALUES (1, 5)")

    assert coderack_codelets(database, 1, time=4) == [
        (2, "Scout", "codelet:discarded"),
    ]
    assert coderack_codelets(database, 1, time=6) == [
        (4, "Builder", "codelet:new"),
    ]


def test_codelet_history_filters_by_time_and_orders_newest_first(tmp_path) -> None:
    database = tmp_path / "history.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE codelets "
            "(id INTEGER PRIMARY KEY, run_id INTEGER, codelet_id TEXT, "
            "parent_codelet_id TEXT, run_time INTEGER, codelet_type TEXT, "
            "urgency_bin INTEGER, time_taken INTEGER, result TEXT, fizzle_reason TEXT)"
        )
        connection.executemany(
            "INSERT INTO codelets "
            "(run_id, codelet_id, parent_codelet_id, run_time, codelet_type, "
            "urgency_bin, time_taken, result, fizzle_reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (1, "codelet:1", None, 1, "Scout", 2, 125_000_000, "fizzle", "no match"),
                (1, "codelet:2", "codelet:1", 3, "Builder", 4, 250_000_000, "finish", None),
                (1, "codelet:3", None, 4, "Later", 6, 500_000_000, "finish", None),
                (2, "codelet:4", None, 5, "Other run", 7, 750_000_000, "finish", None),
            ],
        )

    assert codelet_history(database, 1, time=3) == [
        ("codelet:2", "codelet:1", 3, "Builder", 4, 250_000_000, "finish", None),
        ("codelet:1", None, 1, "Scout", 2, 125_000_000, "fizzle", "no match"),
    ]
    assert codelet_types(database, 1) == {
        "codelet:1": "Scout",
        "codelet:2": "Builder",
        "codelet:3": "Later",
    }


def test_codelet_steps_are_grouped_and_ordered_by_recording(tmp_path) -> None:
    database = tmp_path / "history.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE codelet_steps "
            "(id INTEGER PRIMARY KEY, run_id INTEGER, time INTEGER, codelet_id TEXT, "
            "attribute TEXT, value_json TEXT)"
        )
        connection.executemany(
            "INSERT INTO codelet_steps (run_id, time, codelet_id, attribute, value_json) "
            "VALUES (?, ?, ?, ?, ?)",
            [
                (1, 2, "codelet:1", "source", '"letter:1"'),
                (1, 2, "codelet:1", "target", '"letter:4"'),
                (1, 3, "codelet:2", "proposed_bond", '"bond:7"'),
                (2, 1, "codelet:3", "ignored", '"letter:9"'),
            ],
        )

    assert codelet_steps(database, 1, time=2) == {
        "codelet:1": [("source", "letter:1"), ("target", "letter:4")]
    }


def test_codelet_arguments_are_grouped_and_ordered_by_posting(tmp_path) -> None:
    database = tmp_path / "history.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE codelet_arguments "
            "(id INTEGER PRIMARY KEY, run_id INTEGER, codelet_id TEXT, "
            "attribute TEXT, value_json TEXT)"
        )
        connection.executemany(
            "INSERT INTO codelet_arguments "
            "(run_id, codelet_id, attribute, value_json) VALUES (?, ?, ?, ?)",
            [
                (1, "codelet:1", "proposed_structure", '"bond:7"'),
                (1, "codelet:2", "proposed_structure", '"group:2"'),
                (2, "codelet:3", "proposed_structure", '"bond:9"'),
            ],
        )

    assert codelet_arguments(database, 1) == {
        "codelet:1": [("proposed_structure", "bond:7")],
        "codelet:2": [("proposed_structure", "group:2")],
    }


def test_codelet_step_value_reprs_reconstruct_workspace_objects(tmp_path) -> None:
    database = tmp_path / "history.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE letters "
            "(run_id INTEGER, letter_id TEXT, string_id TEXT, letter_category TEXT, position INTEGER)"
        )
        connection.execute(
            "CREATE TABLE groups "
            "(run_id INTEGER, group_id TEXT, string_id TEXT, left_position INTEGER, "
            "right_position INTEGER, group_category TEXT, direction_category TEXT)"
        )
        connection.execute(
            "CREATE TABLE bonds "
            "(run_id INTEGER, bond_id TEXT, source_id TEXT, target_id TEXT, "
            "bond_facet TEXT, bond_category TEXT, direction_category TEXT)"
        )
        connection.execute(
            "CREATE TABLE descriptions "
            "(run_id INTEGER, description_id TEXT, object_id TEXT, facet TEXT, descriptor TEXT)"
        )
        connection.execute(
            "CREATE TABLE correspondences "
            "(run_id INTEGER, correspondence_id TEXT, source_id TEXT, target_id TEXT)"
        )
        connection.executemany(
            "INSERT INTO letters VALUES (?, ?, ?, ?, ?)",
            [(1, "letter:1", "initial", "a", 0), (1, "letter:2", "initial", "b", 1)],
        )
        connection.execute(
            "INSERT INTO bonds VALUES (?, ?, ?, ?, ?, ?, ?)",
            (1, "bond:1", "letter:1", "letter:2", "letter_category", "successor", "right"),
        )
        connection.execute(
            "INSERT INTO descriptions VALUES (?, ?, ?, ?, ?)",
            (1, "description:1", "letter:1", "letter_category", "a"),
        )

    assert codelet_step_value_reprs(database, 1) == {
        "letter:1": "a@0",
        "letter:2": "b@1",
        "bond:1": "a@0 --['LETTER_CATEGORY', 'SUCCESSOR', 'RIGHT']--> b@1",
        "description:1": "LETTER_CATEGORY of a@0 is A",
    }


def test_codelet_history_links_workspace_object_references(tmp_path) -> None:
    from cattycam.details import _codelet_history

    database = tmp_path / "history.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE codelets (id INTEGER PRIMARY KEY, run_id INTEGER, codelet_id TEXT, "
            "parent_codelet_id TEXT, run_time INTEGER, codelet_type TEXT, "
            "urgency_bin INTEGER, time_taken INTEGER, result TEXT, fizzle_reason TEXT)"
        )
        connection.execute(
            "CREATE TABLE codelet_arguments (id INTEGER PRIMARY KEY, run_id INTEGER, codelet_id TEXT, "
            "attribute TEXT, value_json TEXT)"
        )
        connection.execute(
            "CREATE TABLE codelet_steps (id INTEGER PRIMARY KEY, run_id INTEGER, codelet_id TEXT, "
            "time INTEGER, attribute TEXT, value_json TEXT)"
        )
        connection.execute(
            "CREATE TABLE letters (run_id INTEGER, letter_id TEXT, string_id TEXT, "
            "letter_category TEXT, position INTEGER)"
        )
        connection.execute(
            "CREATE TABLE groups (run_id INTEGER, group_id TEXT, string_id TEXT, "
            "left_position INTEGER, right_position INTEGER, group_category TEXT, "
            "direction_category TEXT)"
        )
        connection.execute(
            "CREATE TABLE bonds (run_id INTEGER, bond_id TEXT, source_id TEXT, "
            "target_id TEXT, bond_facet TEXT, bond_category TEXT, direction_category TEXT)"
        )
        connection.execute(
            "CREATE TABLE descriptions (run_id INTEGER, description_id TEXT, "
            "object_id TEXT, facet TEXT, descriptor TEXT)"
        )
        connection.execute(
            "CREATE TABLE correspondences (run_id INTEGER, correspondence_id TEXT, "
            "source_id TEXT, target_id TEXT)"
        )
        connection.execute("INSERT INTO letters VALUES (1, 'letter:1', 'initial', 'a', 0)")
        connection.execute(
            "INSERT INTO codelets VALUES (1, 1, 'codelet:1', NULL, 1, 'Builder', 3, 1, 'finish', NULL)"
        )
        connection.execute(
            "INSERT INTO codelet_arguments VALUES (1, 1, 'codelet:1', 'object', '\"letter:1\"')"
        )
        connection.execute(
            "INSERT INTO codelet_steps VALUES (1, 1, 'codelet:1', 1, 'objects', '[\"letter:1\"]')"
        )

    history = _codelet_history(database, run_id=1, time=1)

    assert history.object.count('?run_id=1&object_id=letter%3A1') == 2


def test_codelet_history_links_only_executed_codelet_references(tmp_path) -> None:
    from cattycam.details import _codelet_history

    database = tmp_path / "history.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE codelets (id INTEGER PRIMARY KEY, run_id INTEGER, codelet_id TEXT, "
            "parent_codelet_id TEXT, run_time INTEGER, codelet_type TEXT, "
            "urgency_bin INTEGER, time_taken INTEGER, result TEXT, fizzle_reason TEXT)"
        )
        connection.execute(
            "CREATE TABLE codelet_arguments (id INTEGER PRIMARY KEY, run_id INTEGER, "
            "codelet_id TEXT, attribute TEXT, value_json TEXT)"
        )
        connection.execute(
            "CREATE TABLE codelet_steps (id INTEGER PRIMARY KEY, run_id INTEGER, "
            "time INTEGER, codelet_id TEXT, attribute TEXT, value_json TEXT)"
        )
        connection.executemany(
            "INSERT INTO codelets VALUES (?, 1, ?, ?, ?, ?, 1, 1, 'finish', NULL)",
            [
                (1, "codelet:parent", None, 1, "Parent"),
                (2, "codelet:child", "codelet:parent", 2, "Child"),
                (3, "codelet:orphan", "codelet:not-run", 3, "Orphan"),
                (4, "codelet:not-run", "codelet:parent", None, "Pending"),
            ],
        )

    history = _codelet_history(database, run_id=1, time=3).object

    assert '?run_id=1&time=1">Parent parent</a>' in history
    assert '?run_id=1&time=2">Child child</a>' in history
    assert 'Child codelet: <a href="?run_id=1&time=2">Child child</a>, Pending not-run' in history
    assert "Parent codelet: Pending not-run" in history


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
            ("replacements", "replacement_id"),
        ):
            columns = (
                "string_id TEXT, left_position INTEGER, right_position INTEGER"
                if table == "groups"
                else (
                    "source_id TEXT, target_id TEXT, bond_facet TEXT, bond_category TEXT, direction_category TEXT"
                    if table == "bonds"
                    else "source_id TEXT, target_id TEXT"
                )
            )
            connection.execute(
                f"CREATE TABLE {table} "
                f"(run_id INTEGER, {identifier} TEXT, {columns}, proposal_time INTEGER, "
                "creation_time INTEGER, destruction_time INTEGER)"
            )
        connection.execute(
            "CREATE TABLE descriptions "
            "(run_id INTEGER, object_id TEXT, facet TEXT, descriptor TEXT, "
            "proposal_time INTEGER, creation_time INTEGER, destruction_time INTEGER)"
        )
        connection.execute(
            "CREATE TABLE concept_mappings "
            "(id INTEGER PRIMARY KEY, run_id INTEGER, correspondence_id TEXT, "
            "source_facet TEXT, target_facet TEXT, source_descriptor TEXT, "
            "target_descriptor TEXT, label TEXT)"
        )
        connection.execute(
            "CREATE TABLE rules "
            "(id INTEGER PRIMARY KEY, run_id INTEGER, rule_id TEXT, source_object_category TEXT, "
            "source_descriptor TEXT, replaced_facet TEXT, target_descriptor TEXT, relation TEXT, "
            "proposal_time INTEGER, creation_time INTEGER, destruction_time INTEGER)"
        )
        connection.execute(
            "CREATE TABLE translated_rules "
            "(id INTEGER PRIMARY KEY, run_id INTEGER, rule_id TEXT, source_object_category TEXT, "
            "source_descriptor TEXT, replaced_facet TEXT, target_descriptor TEXT, relation TEXT, "
            "proposal_time INTEGER, creation_time INTEGER, destruction_time INTEGER)"
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
            "INSERT INTO bonds VALUES (1, 'bond:1', 'letter:1', 'letter:2', "
            "'letter_category', 'successor', 'right', 1, 2, NULL)"
        )
        connection.execute(
            "INSERT INTO descriptions VALUES (1, 'letter:1', 'object_category', 'letter', 0, 0, NULL)"
        )
        connection.execute(
            "INSERT INTO correspondences VALUES (1, 'correspondence:1', 'letter:1', 'letter:2', 2, NULL, NULL)"
        )
        connection.execute(
            "INSERT INTO concept_mappings VALUES "
            "(1, 1, 'correspondence:1', 'letter_category', 'letter_category', 'a', 'b', 'successor')"
        )
        connection.execute(
            "INSERT INTO replacements VALUES (1, 'replacement:1', 'letter:1', 'letter:2', 2, NULL, NULL)"
        )
        connection.execute(
            "INSERT INTO rules VALUES (1, 1, 'rule:1', 'letter', 'a', 'letter_category', 'b', NULL, 2, NULL, NULL)"
        )
        connection.execute(
            "INSERT INTO translated_rules VALUES (1, 1, 'rule:translated:1', 'letter', 'a', "
            "'letter_category', 'b', NULL, NULL, 2, NULL)"
        )

    snapshot = workspace_snapshot(database, 1, 2)

    assert [letter["value"] for letter in snapshot["letters"]] == ["a", "b"]
    assert snapshot["groups"][0]["proposed"] is True
    assert snapshot["bonds"][0]["proposed"] is False
    assert snapshot["bonds"][0]["facet"] == "letter_category"
    assert snapshot["bonds"][0]["category"] == "successor"
    assert snapshot["bonds"][0]["direction"] == "right"
    assert snapshot["correspondences"][0]["proposed"] is True
    assert snapshot["correspondences"][0]["mappings"] == [
        {"source": "a", "target": "b", "label": "successor", "source_type": "letter_category", "target_type": "letter_category"}
    ]
    assert snapshot["replacements"][0]["proposed"] is True
    assert snapshot["descriptions"]["letter:1"] == [
        {"facet": "object_category", "descriptor": "letter"}
    ]
    assert snapshot["rule"] == {
        "id": "rule:1", "source_object_category": "letter", "source_descriptor": "a",
        "replaced_facet": "letter_category", "target_descriptor": "b", "relation": None,
    }
    assert snapshot["translated_rule"] == {
        "id": "rule:translated:1", "source_object_category": "letter", "source_descriptor": "a",
        "replaced_facet": "letter_category", "target_descriptor": "b", "relation": None,
    }


def test_slipnet_snapshot_uses_the_latest_activation_at_the_selected_time(tmp_path) -> None:
    database = tmp_path / "history.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE slipnodes (run_id INTEGER, name TEXT)")
        connection.execute(
            "CREATE TABLE sliplinks "
            "(id INTEGER PRIMARY KEY, run_id INTEGER, source TEXT, target TEXT, "
            "label TEXT, fixed_length REAL)"
        )
        connection.execute(
            "CREATE TABLE attribute_values "
            "(id INTEGER PRIMARY KEY, run_id INTEGER, time INTEGER, object_id TEXT, "
            "attribute TEXT, value_json TEXT)"
        )
        connection.executemany(
            "INSERT INTO slipnodes VALUES (1, ?)", [("left",), ("right",)]
        )
        connection.execute(
            "INSERT INTO sliplinks VALUES (1, 1, 'left', 'right', 'opposite', 0.8)"
        )
        connection.executemany(
            "INSERT INTO attribute_values VALUES (?, 1, ?, ?, 'activation', ?)",
            [
                (1, 0, "slipnode:left", "0.2"),
                (2, 1, "slipnode:right", "0.4"),
                (3, 3, "slipnode:left", "0.9"),
            ],
        )

    snapshot = slipnet_snapshot(database, 1, 2)

    assert snapshot["nodes"] == [
        {"name": "left", "activation": 0.2},
        {"name": "right", "activation": 0.4},
    ]
    assert snapshot["links"] == [
        {"source": "left", "target": "right", "label": "opposite", "fixed_length": 0.8}
    ]
