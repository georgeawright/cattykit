import pytest

from copycat import Copycat

SLIPNET_JSON_FILE = "configs/slipnet.json"
CODERACK_JSON_FILE = "configs/coderack.json"


def test_single_run():
    # initial set up
    copycat = Copycat.from_json(SLIPNET_JSON_FILE, CODERACK_JSON_FILE)

    assert copycat.coderack.population == 0

    copycat.solve("abc -> abd ==> ijk -> ?")

    # all node activations are zero except for initially clamped nodes
    active_node_count = 0
    for node_id, node in copycat.slipnet.node_index_lookup.items():
        if node_id in ["letter_category", "string_position_category"]:
            assert copycat.slipnet.get_node_activation(node_id) == 1.0
            active_node_count += 1
        else:
            assert copycat.slipnet.get_node_activation(node_id) == 0.0
    assert active_node_count == 2

    # each string should have letter category and position descriptions
    assert {
        l.letter_category.name: [
            (d.facet.name, d.descriptor.name) for d in l.descriptions
        ]
        for l in copycat.workspace.initial_string.letters
    } == {
        "a": [
            ("object_category", "letter"),
            ("letter_category", "a"),
            ("string_position_category", "leftmost"),
        ],
        "b": [
            ("object_category", "letter"),
            ("letter_category", "b"),
            ("string_position_category", "middle"),
        ],
        "c": [
            ("object_category", "letter"),
            ("letter_category", "c"),
            ("string_position_category", "rightmost"),
        ],
    }
    assert {
        l.letter_category.name: [
            (d.facet.name, d.descriptor.name) for d in l.descriptions
        ]
        for l in copycat.workspace.modified_string.letters
    } == {
        "a": [
            ("object_category", "letter"),
            ("letter_category", "a"),
            ("string_position_category", "leftmost"),
        ],
        "b": [
            ("object_category", "letter"),
            ("letter_category", "b"),
            ("string_position_category", "middle"),
        ],
        "d": [
            ("object_category", "letter"),
            ("letter_category", "d"),
            ("string_position_category", "rightmost"),
        ],
    }
    assert {
        l.letter_category.name: [
            (d.facet.name, d.descriptor.name) for d in l.descriptions
        ]
        for l in copycat.workspace.target_string.letters
    } == {
        "i": [
            ("object_category", "letter"),
            ("letter_category", "i"),
            ("string_position_category", "leftmost"),
        ],
        "j": [
            ("object_category", "letter"),
            ("letter_category", "j"),
            ("string_position_category", "middle"),
        ],
        "k": [
            ("object_category", "letter"),
            ("letter_category", "k"),
            ("string_position_category", "rightmost"),
        ],
    }
    # the answer string is empty at the start
    assert [
        l.letter_category.name for l in copycat.workspace.answer_string.letters
    ] == []

    # 3 types of codelets have been added.
    # 2 for each workspace object (initial and target string objects)
    assert copycat.coderack.population == 36
