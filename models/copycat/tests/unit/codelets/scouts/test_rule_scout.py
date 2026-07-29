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
