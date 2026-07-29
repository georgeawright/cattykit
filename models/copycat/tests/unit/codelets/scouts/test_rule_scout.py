from unittest.mock import Mock

import pytest

from copycat.codelet_result import Finish, Fizzle, FizzleReason
from copycat.codelets.scouts import RuleScout


def test_fizzles_if_not_all_initial_string_letters_have_replacements():
    workspace = Mock()
    workspace.all_replacements_found.return_value = False

    rule_scout = RuleScout(
        urgency_bin=0, coderack=Mock(), workspace=workspace, slipnet=Mock()
    )
    result = rule_scout.run(temperature=0.0)

    assert result == Fizzle(FizzleReason.NOT_ALL_REPLACEMENTS_FOUND)


def test_raises_exception_if_more_than_one_changed_letter():
    workspace = Mock()
    workspace.all_replacements_found.return_value = True
    workspace.initial_string.get_changed_objects.return_value = [Mock(), Mock()]

    rule_scout = RuleScout(
        urgency_bin=0, coderack=Mock(), workspace=workspace, slipnet=Mock()
    )
    with pytest.raises(Exception):
        result = rule_scout.run(temperature=0.0)
