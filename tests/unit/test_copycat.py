from types import SimpleNamespace

import pytest


from copycat import Copycat


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
    workspace = SimpleNamespace(total_unhappiness=workspace_unhappiness)
    copycat = Copycat(None, None, workspace, None, None, None)
    copycat.translated_rule = SimpleNamespace(total_strength=rule_strength)
    copycat._update_temperature()
    assert copycat.temperature == pytest.approx(expected)
