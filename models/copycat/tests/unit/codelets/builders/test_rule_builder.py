from unittest.mock import Mock

import pytest

from copycat.codelets.builders import rule_builder
from copycat.codelets.builders import RuleBuilder
from copycat.codelet_result import Finish, Fizzle, FizzleReason


class MockWorkspace:
    def __init__(self):
        self.rule = None


def test_fizzles_if_rule_already_exist():
    workspace = MockWorkspace()
    rule = Mock()
    workspace.rule = rule
    builder = RuleBuilder(Mock(), Mock(), workspace, Mock(), rule)
    result = builder.run(temperature=0.0)

    assert result == Fizzle(FizzleReason.RULE_ALREADY_EXISTS)
