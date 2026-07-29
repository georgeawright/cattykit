from unittest.mock import Mock

import pytest

from copycat.codelets.builders import rule_builder
from copycat.codelets.builders import RuleBuilder
from copycat.codelet_result import Finish, Fizzle, FizzleReason


class MockWorkspace:
    def __init__(self):
        self.rule = None


class MockSlipnet:
    def __init__(self):
        self.activate_called = 0

    def activate_node_from_workspace(self, name):
        self.activate_called += 1


def test_fizzles_if_rule_already_exist():
    slipnet = MockSlipnet()
    workspace = MockWorkspace()
    rule = Mock()
    workspace.rule = rule
    builder = RuleBuilder(Mock(), Mock(), workspace, slipnet, rule)
    result = builder.run(temperature=0.0)

    assert result == Fizzle(FizzleReason.RULE_ALREADY_EXISTS)
    assert slipnet.activate_called == 3


def test_fizzles_if_existing_rule_wins(monkeypatch):
    slipnet = MockSlipnet()
    workspace = MockWorkspace()
    workspace.rule = Mock()
    rule = Mock()
    builder = RuleBuilder(Mock(), Mock(), workspace, slipnet, rule)
    monkeypatch.setattr(
        rule_builder, "structure_beats_structures", lambda *_, **__: False
    )
    result = builder.run(temperature=0.0)

    assert result == Fizzle(FizzleReason.INCOMPATIBLE_STRUCTURES_WON)
    assert slipnet.activate_called == 0
