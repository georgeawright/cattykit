from unittest.mock import Mock

import pytest

from copycat.codelet_result import Finish, Fizzle, FizzleReason
from copycat.codelets.scouts import RuleScout
from copycat.codelets.strength_testers import RuleStrengthTester


class MockCoderack:
    def __init__(self):
        self.posted_codelets = []
        self.post_called = 0

    def post(self, codelet):
        self.post_called += 1
        self.posted_codelets.append(codelet)

    def get_urgency_level_from_activation(self, activation):
        return 0


class MockSlipnet:
    nodes = {"object_category": Mock()}

    def __getitem__(self, item):
        return self.nodes[item]


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
        rule_scout.run(temperature=0.0)


def test_proposes_null_rule_if_there_are_no_changed_letters():
    coderack = MockCoderack()
    slipnet = MockSlipnet()

    workspace = Mock()
    workspace.all_replacements_found.return_value = True
    workspace.initial_string.get_changed_objects.return_value = []

    rule_scout = RuleScout(
        urgency_bin=0, coderack=coderack, workspace=workspace, slipnet=slipnet
    )
    result = rule_scout.run(temperature=0.0)

    assert result == Finish()
    assert coderack.post_called == 1
    follow_up = coderack.posted_codelets[0]
    assert isinstance(follow_up, RuleStrengthTester)
    proposed_rule = follow_up.proposed_rule
    assert proposed_rule.object_category_1 is None
    assert proposed_rule.descriptor_1_facet is None
    assert proposed_rule.descriptor_1 is None
    assert proposed_rule.object_category_2 is None
    assert proposed_rule.descriptor_2 is None
    assert proposed_rule.replaced_description_type is None
    assert proposed_rule.relation is None


def test_fizzles_if_there_is_no_initial_description():
    coderack = MockCoderack()
    slipnet = MockSlipnet()

    workspace = Mock()
    workspace.all_replacements_found.return_value = True

    initial_object = Mock()
    initial_object.rule_initial_string_descriptions = []
    workspace.initial_string.get_changed_objects.return_value = [initial_object]

    rule_scout = RuleScout(
        urgency_bin=0, coderack=coderack, workspace=workspace, slipnet=slipnet
    )
    result = rule_scout.run(temperature=0.0)

    assert result == Fizzle(FizzleReason.NO_INITIAL_DESCRIPTIONS)
