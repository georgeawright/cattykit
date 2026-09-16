from types import SimpleNamespace
from unittest.mock import Mock

import pytest


from copycat import Copycat


def test_logs_answer_letters_created_by_answer_builder():
    events = []
    copycat = Copycat.__new__(Copycat)
    copycat.coderack = SimpleNamespace(number_of_codelets_run=12)
    copycat.logger = SimpleNamespace(log=lambda kind, **data: events.append((kind, data)))
    old_letter = SimpleNamespace(hash_id=1)
    new_letter = SimpleNamespace(
        hash_id=2,
        left_position=0,
        letter_category=SimpleNamespace(name="l"),
    )
    copycat.workspace = SimpleNamespace(
        answer_string=SimpleNamespace(letters=[new_letter])
    )

    copycat._log_answer_letters([old_letter])

    assert events == [
        ("letter_destroyed", {"letter": old_letter, "time": 12}),
        (
            "letter_created",
            {
                "letter": new_letter,
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
        rule=SimpleNamespace(total_strength=rule_strength),
    )
    copycat = Copycat(None, None, workspace, None, None, None, Mock())
    copycat._update_temperature()
    assert copycat.temperature == pytest.approx(expected)
