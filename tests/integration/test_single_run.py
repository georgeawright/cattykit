import pytest

from copycat import Copycat

SLIPNET_JSON_FILE = "configs/slipnet.json"
CODERACK_JSON_FILE = "configs/coderack.json"


def test_single_run():
    # initial set up
    copycat = Copycat.from_json(SLIPNET_JSON_FILE, CODERACK_JSON_FILE)
    copycat.solve("abc -> abd ==> ijk -> ?")

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
