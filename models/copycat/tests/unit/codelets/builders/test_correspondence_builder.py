from unittest.mock import Mock

import pytest

from copycat.codelets.builders import correspondence_builder
from copycat.codelets.builders import CorrespondenceBuilder
from copycat.codelet_result import Finish, Fizzle, FizzleReason


class MockWorkspace:
    def __init__(self):
        self.objects = []
        self.correspondences = []
        self.add_correspondence_called = 0
        self.delete_proposed_correspondence_called = 0
        self.break_bond_called = 0
        self.break_group_called = 0
        self.break_correspondence_called = 0
        self.break_rule_called = 0

    def add_correspondence(self, correspondence):
        self.add_correspondence_called += 1
        self.correspondences.append(correspondence)

    def delete_proposed_correspondence(self, correspondence):
        self.delete_proposed_correspondence_called += 1

    def break_bond(self, bond):
        self.break_bond_called += 1

    def break_group(self, group):
        self.break_group_called += 1

    def break_correspondence(self, correspondence):
        self.break_correspondence_called += 1

    def break_rule(self, rule):
        self.break_rule_called += 1


def test_run_fizzles_if_source_no_longer_exist():
    workspace = MockWorkspace()
    correspondence = Mock()
    correspondence.source = Mock()
    correspondence.source.correspondence = None
    correspondence.target = Mock()
    correspondence.target.correspondence = None
    builder = CorrespondenceBuilder(
        urgency_bin=0,
        coderack=Mock(),
        slipnet=Mock(),
        workspace=workspace,
        proposed_correspondence=correspondence,
    )
    result = builder.run(temperature=0.0)
    assert result == Fizzle(FizzleReason.OBJECTS_NO_LONGER_EXIST)
    assert correspondence.source.correspondence is None
    assert correspondence.target.correspondence is None


def test_run_fizzles_if_target_no_longer_exist():
    workspace = MockWorkspace()
    correspondence = Mock()
    correspondence.source = Mock()
    workspace.objects.append(correspondence.source)
    correspondence.source.correspondence = None
    correspondence.target = Mock()
    correspondence.target.correspondence = None
    builder = CorrespondenceBuilder(
        urgency_bin=0,
        coderack=Mock(),
        slipnet=Mock(),
        workspace=workspace,
        proposed_correspondence=correspondence,
    )
    result = builder.run(temperature=0.0)
    assert result == Fizzle(FizzleReason.OBJECTS_NO_LONGER_EXIST)
    assert correspondence.source.correspondence is None
    assert correspondence.target.correspondence is None


def test_run_fizzles_if_flipped_target_no_longer_exists():
    workspace = MockWorkspace()
    workspace.target_string = Mock()
    workspace.target_string.get_group_if_present.return_value = False
    correspondence = Mock()
    correspondence.source = Mock()
    workspace.objects.append(correspondence.source)
    correspondence.source.correspondence = None
    correspondence.target = Mock()
    correspondence.target.correspondence = None
    builder = CorrespondenceBuilder(
        urgency_bin=0,
        coderack=Mock(),
        slipnet=Mock(),
        workspace=workspace,
        proposed_correspondence=correspondence,
        target_flipped=True,
    )
    result = builder.run(temperature=0.0)
    assert result == Fizzle(FizzleReason.OBJECTS_NO_LONGER_EXIST)
    assert correspondence.source.correspondence is None
    assert correspondence.target.correspondence is None
