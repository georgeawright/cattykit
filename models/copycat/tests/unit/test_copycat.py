from types import SimpleNamespace

import pytest


from copycat import Copycat


def test_logs_answer_letters_created_by_answer_builder():
    events = []
    copycat = Copycat.__new__(Copycat)
    copycat.coderack = SimpleNamespace(number_of_codelets_run=12)
    copycat.logger = SimpleNamespace(log=events.append)
    old_letter = SimpleNamespace(hash_id=1)
    new_letter = SimpleNamespace(
        hash_id=2,
        left_position=0,
        letter_category=SimpleNamespace(name="l"),
    )
    copycat.workspace = SimpleNamespace(answer_string=SimpleNamespace(letters=[new_letter]))

    copycat._log_answer_letters([old_letter])

    assert [(event.kind, event.data) for event in events] == [
        ("letter_destroyed", {"letter_id": "letter:1", "time": 12}),
        (
            "letter_created",
            {
                "letter_id": "letter:2",
                "string_id": "answer",
                "position": 0,
                "letter_category": "l",
                "time": 12,
            },
        ),
    ]


@pytest.mark.parametrize(
    "rule_strength, workspace_unhappiness, expected",
    [
        (0.0, 0.0, 0.2),
        (0.0, 1.0, 1.0),
        (0.5, 0.0, 0.1),
        (0.5, 1.0, 0.9),
        (1.0, 0.0, 0.0),
        (1.0, 1.0, 0.8),
    ],
)
def test_update_temperature(rule_strength, workspace_unhappiness, expected):
    workspace = SimpleNamespace(
        total_unhappiness=workspace_unhappiness,
        translated_rule=SimpleNamespace(total_strength=rule_strength),
    )
    copycat = Copycat(None, None, workspace, None, None, None)
    copycat._update_temperature()
    assert copycat.temperature == pytest.approx(expected)
