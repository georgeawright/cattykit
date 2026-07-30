from unittest.mock import Mock

import pytest

from copycat.codelet_result import Finish, Fizzle, FizzleReason
from copycat.codelets import RuleTranslator


def test_fizzles_if_no_rule_in_workspace():
    workspace = Mock()
    workspace.rule = None
    workspace.translated_rule = None
    translator = RuleTranslator(Mock(), Mock(), workspace, Mock())
    result = translator.run(temperature=0.0)

    assert result == Fizzle(FizzleReason.NO_RULE_IN_WORKSPACE)
    assert workspace.translated_rule is None


def test_makes_translated_rule_null_rule_if_rule_has_no_change():
    workspace = Mock()
    rule = Mock()
    rule.specifies_change.return_value = False
    workspace.rule = rule
    workspace.translated_rule = None
    translator = RuleTranslator(Mock(), Mock(), workspace, Mock())
    result = translator.run(temperature=0.0)

    assert result == Finish()
    assert workspace.translated_rule is not None
    assert workspace.translated_rule.object_category_1 is None
    assert workspace.translated_rule.descriptor_1_facet is None
    assert workspace.translated_rule.descriptor_1 is None
    assert workspace.translated_rule.object_category_2 is None
    assert workspace.translated_rule.descriptor_2 is None
    assert workspace.translated_rule.replaced_description_type is None
    assert workspace.translated_rule.relation is None


def test_fizzles_if_temperature_is_too_high(monkeypatch):
    workspace = Mock()
    rule = Mock()
    rule.specifies_change.return_value = True
    workspace.rule = rule
    workspace.translated_rule = None

    monkeypatch.setattr(
        RuleTranslator, "_get_answer_temperature_threshold", lambda *_, **__: 0.5
    )

    translator = RuleTranslator(Mock(), Mock(), workspace, Mock())
    result = translator.run(temperature=0.6)

    assert result == Fizzle(FizzleReason.TEMPERATURE_TOO_HIGH)
    assert workspace.translated_rule is None


def test_fizzles_if_there_is_no_changed_object(monkeypatch):
    workspace = Mock()
    workspace.initial_string.changed_objects = []
    rule = Mock()
    rule.specifies_change.return_value = True
    workspace.rule = rule
    workspace.translated_rule = None

    monkeypatch.setattr(
        RuleTranslator, "_get_answer_temperature_threshold", lambda *_, **__: 0.5
    )

    translator = RuleTranslator(Mock(), Mock(), workspace, Mock())
    result = translator.run(temperature=0.0)

    assert result == Fizzle(FizzleReason.NO_CHANGED_OBJECT)
    assert workspace.translated_rule is None


def test_sets_translated_rule(monkeypatch):
    workspace = Mock()
    changed_object = Mock(correspondence=None)
    workspace.initial_string.changed_objects = [changed_object]
    rule = Mock()
    rule.specifies_change.return_value = True
    workspace.rule = rule
    workspace.translated_rule = None

    monkeypatch.setattr(
        RuleTranslator, "_get_answer_temperature_threshold", lambda *_, **__: 0.5
    )

    translator = RuleTranslator(Mock(), Mock(), workspace, Mock())
    result = translator.run(temperature=0.0)

    assert result == Finish()
    assert workspace.translated_rule is not None
