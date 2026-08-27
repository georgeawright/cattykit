from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest

from copycat.codelets.builders import CorrespondenceBuilder
from copycat.codelet_result import Finish, Fizzle, FizzleReason
from copycat.slipnet import Slipnet


class MockWorkspace:
    def __init__(self):
        self.objects = []
        self.correspondences = []
        self.add_correspondence_called = 0
        self.delete_proposed_correspondence_called = 0
        self.break_bond_called = 0
        self.break_group_called = 0
        self.break_correspondence_called = 0
        self.existing_correspondence = None
        self.rule = None
        self.slippages = [Mock(), Mock()]

    def get_existing_correspondence(self, correspondence):
        return self.existing_correspondence

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


class MockSlipnet:
    def __init__(self):
        self.activate_called = 0
        self.identity = SimpleNamespace(name="identity")
        self.opposite = SimpleNamespace(name="opposite")

    def __getitem__(self, name):
        return SimpleNamespace(name=name)

    def activate_node_from_workspace(self, name):
        self.activate_called += 1

    def get_node_activation(self, name):
        return 0.5

    def get_label_node(self, source, target):
        return self.identity if source is target else self.opposite

    def get_concept_mappings(
        self, source, target, source_descriptions, target_descriptions
    ):
        return Slipnet.get_concept_mappings(
            self, source, target, source_descriptions, target_descriptions
        )


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


def test_deletes_proposal_augments_existing_correspondence_and_fizzles():
    slipnet = MockSlipnet()
    workspace = MockWorkspace()

    mapping_1 = Mock()
    mapping_2 = Mock()
    mapping_3 = Mock()

    correspondence = Mock()
    correspondence.source = Mock()
    correspondence.source.correspondence = None
    correspondence.target = Mock()
    correspondence.target.correspondence = None
    correspondence.concept_mappings = [mapping_1, mapping_2]
    workspace.objects += [correspondence.source, correspondence.target]

    existing_correspondence = Mock()
    existing_correspondence.concept_mappings = [mapping_1, mapping_3]
    workspace.existing_correspondence = existing_correspondence

    builder = CorrespondenceBuilder(
        urgency_bin=0,
        coderack=Mock(),
        slipnet=slipnet,
        workspace=workspace,
        proposed_correspondence=correspondence,
    )
    result = builder.run(temperature=0.0)
    assert workspace.delete_proposed_correspondence_called == 1
    assert slipnet.activate_called == 2
    assert mapping_2 in existing_correspondence.concept_mappings
    assert result == Fizzle(FizzleReason.STRUCTURE_ALREADY_EXISTS)
    assert correspondence.source.correspondence is None
    assert correspondence.target.correspondence is None


def test_fizzles_if_not_all_concept_mappings_relevant():
    slipnet = MockSlipnet()
    workspace = MockWorkspace()

    mapping_1 = Mock()
    mapping_1.is_relevant.return_value = True
    mapping_2 = Mock()
    mapping_1.is_relevant.return_value = False

    correspondence = Mock()
    correspondence.source = Mock()
    correspondence.source.correspondence = None
    correspondence.target = Mock()
    correspondence.target.correspondence = None
    correspondence.concept_mappings = [mapping_1, mapping_2]
    workspace.objects += [correspondence.source, correspondence.target]

    builder = CorrespondenceBuilder(
        urgency_bin=0,
        coderack=Mock(),
        slipnet=slipnet,
        workspace=workspace,
        proposed_correspondence=correspondence,
    )
    result = builder.run(temperature=0.0)
    assert result == Fizzle(FizzleReason.NOT_ALL_CONCEPT_MAPPINGS_RELEVANT)
    assert correspondence.source.correspondence is None
    assert correspondence.target.correspondence is None


def test_fizzles_if_incompatible_correspondences_win():
    slipnet = MockSlipnet()
    workspace = MockWorkspace()

    mapping_1 = Mock()
    mapping_1.is_relevant.return_value = True
    mapping_2 = Mock()
    mapping_1.is_relevant.return_value = True

    correspondence = MagicMock()
    correspondence.total_strength = 0
    correspondence.__len__.return_value = 2
    correspondence.source = Mock()
    correspondence.source.correspondence = None
    correspondence.target = Mock()
    correspondence.target.correspondence = None
    correspondence.concept_mappings = [mapping_1, mapping_2]
    workspace.objects += [correspondence.source, correspondence.target]

    incompatible_correspondence = MagicMock()
    incompatible_correspondence.is_incompatible_argumentwise_with.return_value = True
    incompatible_correspondence.total_strength = 1
    incompatible_correspondence.__len__.return_value = 10
    workspace.correspondences.append(incompatible_correspondence)

    builder = CorrespondenceBuilder(
        urgency_bin=0,
        coderack=Mock(),
        slipnet=slipnet,
        workspace=workspace,
        proposed_correspondence=correspondence,
    )
    result = builder.run(temperature=0.0)
    assert result == Fizzle(FizzleReason.INCOMPATIBLE_STRUCTURES_WON)
    assert correspondence.source.correspondence is None
    assert correspondence.target.correspondence is None


def test_fizzles_if_incompatible_bond_wins():
    slipnet = MockSlipnet()
    workspace = MockWorkspace()

    mapping_1 = Mock()
    mapping_1.is_relevant.return_value = True
    mapping_2 = Mock()
    mapping_1.is_relevant.return_value = True

    correspondence = MagicMock()
    correspondence.total_strength = 0.1
    correspondence.__len__.return_value = 2
    correspondence.source = Mock()
    correspondence.source.correspondence = None
    correspondence.target = Mock()
    correspondence.target.correspondence = None
    correspondence.concept_mappings = [mapping_1, mapping_2]
    workspace.objects += [correspondence.source, correspondence.target]

    source_bond = Mock()
    correspondence.source.is_leftmost_in_string.return_value = True
    correspondence.source.right_bond = source_bond
    target_bond = Mock()
    target_bond.total_strength = 1
    correspondence.target.is_leftmost_in_string.return_value = True
    correspondence.target.right_bond = target_bond
    mapping_1.is_incompatible_with.return_value = True

    builder = CorrespondenceBuilder(
        urgency_bin=0,
        coderack=Mock(),
        slipnet=slipnet,
        workspace=workspace,
        proposed_correspondence=correspondence,
    )
    result = builder.run(temperature=0.0)
    assert result == Fizzle(FizzleReason.INCOMPATIBLE_STRUCTURES_WON)
    assert correspondence.source.correspondence is None
    assert correspondence.target.correspondence is None


def test_fizzles_if_incompatible_group_wins():
    slipnet = MockSlipnet()
    workspace = MockWorkspace()

    mapping_1 = Mock()
    mapping_1.is_relevant.return_value = True
    mapping_2 = Mock()
    mapping_1.is_relevant.return_value = True

    correspondence = MagicMock()
    correspondence.total_strength = 0.1
    correspondence.__len__.return_value = 2
    correspondence.source = Mock()
    correspondence.source.correspondence = None
    correspondence.target = Mock()
    correspondence.target.correspondence = None
    correspondence.concept_mappings = [mapping_1, mapping_2]
    workspace.objects += [correspondence.source, correspondence.target]

    source_bond = Mock()
    correspondence.source.is_leftmost_in_string.return_value = True
    correspondence.source.right_bond = source_bond
    target_bond = Mock()
    target_bond.total_strength = 0.1
    correspondence.target.is_leftmost_in_string.return_value = True
    correspondence.target.right_bond = target_bond
    mapping_1.is_incompatible_with.return_value = True
    incompatible_group = Mock()
    incompatible_group.total_strength = 1
    target_bond.group = incompatible_group

    builder = CorrespondenceBuilder(
        urgency_bin=0,
        coderack=Mock(),
        slipnet=slipnet,
        workspace=workspace,
        proposed_correspondence=correspondence,
    )
    result = builder.run(temperature=0.0)
    assert result == Fizzle(FizzleReason.INCOMPATIBLE_STRUCTURES_WON)
    assert correspondence.source.correspondence is None
    assert correspondence.target.correspondence is None


def test_fizzles_if_existing_target_wins():
    slipnet = MockSlipnet()
    workspace = MockWorkspace()

    existing_target = Mock()
    existing_target.total_strength = 1

    workspace.target_string = Mock()
    workspace.target_string.get_group_if_present.return_value = existing_target

    correspondence = MagicMock()
    correspondence.total_strength = 0
    correspondence.__len__.return_value = 4
    correspondence.source = Mock()
    workspace.objects.append(correspondence.source)
    correspondence.source.correspondence = None
    correspondence.target = Mock()
    correspondence.target.correspondence = None

    builder = CorrespondenceBuilder(
        urgency_bin=0,
        coderack=Mock(),
        slipnet=slipnet,
        workspace=workspace,
        proposed_correspondence=correspondence,
        target_flipped=True,
    )
    result = builder.run(temperature=0.0)
    assert result == Fizzle(FizzleReason.INCOMPATIBLE_STRUCTURES_WON)
    assert correspondence.source.correspondence is None
    assert correspondence.target.correspondence is None


def test_fizzles_if_incompatible_rule_wins():
    slipnet = MockSlipnet()
    workspace = MockWorkspace()

    mapping_1 = Mock()
    mapping_1.is_relevant.return_value = True
    mapping_2 = Mock()
    mapping_1.is_relevant.return_value = True

    correspondence = MagicMock()
    correspondence.total_strength = 0.1
    correspondence.__len__.return_value = 2
    correspondence.source = Mock()
    correspondence.source.is_changed_letter = True
    correspondence.source.correspondence = None
    correspondence.target = Mock()
    correspondence.target.correspondence = None
    correspondence.target.get_relevant_descriptions = lambda: [Mock()]
    correspondence.concept_mappings = [mapping_1, mapping_2]
    workspace.objects += [correspondence.source, correspondence.target]

    correspondence.source.is_leftmost_in_string.return_value = False
    correspondence.source.is_rightmost_in_string.return_value = False
    correspondence.target.is_leftmost_in_string.return_value = False
    correspondence.target.is_rightmost_in_string.return_value = False

    workspace.rule = Mock()
    workspace.rule.total_strength = 1

    builder = CorrespondenceBuilder(
        urgency_bin=0,
        coderack=Mock(),
        slipnet=slipnet,
        workspace=workspace,
        proposed_correspondence=correspondence,
    )
    result = builder.run(temperature=0.0)
    assert result == Fizzle(FizzleReason.INCOMPATIBLE_STRUCTURES_WON)
    assert correspondence.source.correspondence is None
    assert correspondence.target.correspondence is None


def test_breaks_incompatible_structures_and_builds_correspondence():
    slipnet = MockSlipnet()
    workspace = MockWorkspace()

    existing_target = Mock()
    existing_target.total_strength = 0
    existing_target.bonds = [Mock()]

    workspace.target_string = Mock()
    workspace.target_string.get_group_if_present.return_value = existing_target

    mapping_1 = Mock()
    mapping_1.is_relevant.return_value = True
    mapping_2 = Mock()
    mapping_1.is_relevant.return_value = True

    correspondence = MagicMock()
    correspondence.total_strength = 1
    correspondence.__len__.return_value = 4
    correspondence.source = Mock()
    correspondence.source.is_changed_letter = True
    correspondence.source.correspondence = None
    correspondence.target = Mock()
    correspondence.target.bonds = [Mock()]
    correspondence.target.correspondence = None
    correspondence.target.get_relevant_descriptions = lambda: [Mock()]
    correspondence.concept_mappings = [mapping_1, mapping_2]
    workspace.objects += [correspondence.source, correspondence.target]

    incompatible_correspondence = MagicMock()
    incompatible_correspondence.is_incompatible_argumentwise_with.return_value = True
    incompatible_correspondence.total_strength = 0
    incompatible_correspondence.__len__.return_value = 10
    workspace.correspondences.append(incompatible_correspondence)

    source_bond = Mock()
    correspondence.source.is_leftmost_in_string.return_value = True
    correspondence.source.right_bond = source_bond
    target_bond = Mock()
    target_bond.total_strength = 0
    correspondence.target.is_leftmost_in_string.return_value = True
    correspondence.target.right_bond = target_bond
    correspondence.target.objects = [Mock(), Mock()]
    correspondence.target.descriptions = [Mock(), Mock()]
    mapping_1.is_incompatible_with.return_value = True
    incompatible_group = Mock()
    incompatible_group.total_strength = 0
    target_bond.group = incompatible_group

    workspace.rule = Mock()
    workspace.rule.total_strength = 0

    builder = CorrespondenceBuilder(
        urgency_bin=0,
        coderack=Mock(),
        slipnet=slipnet,
        workspace=workspace,
        proposed_correspondence=correspondence,
        target_flipped=True,
    )
    result = builder.run(temperature=0.0)
    assert result == Finish()
    assert workspace.break_group_called == 2
    assert workspace.break_bond_called == 2
    assert workspace.break_correspondence_called == 1
    assert workspace.rule is None
    assert correspondence.source.correspondence == correspondence
    assert correspondence.target.correspondence == correspondence
    assert workspace.add_correspondence_called == 1
    assert slipnet.activate_called == 5
