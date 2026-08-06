from unittest.mock import Mock
from types import SimpleNamespace

import pytest

from copycat.codelets.builders import group_builder
from copycat.codelets.builders import GroupBuilder
from copycat.codelet_result import Finish, Fizzle, FizzleReason


class MockSlipnet:
    def __init__(self):
        self.activate_node_from_workspace_called = 0
        self._nodes = {
            name: SimpleNamespace(name=name, activation=0.0)
            for name in (
                "bond_category",
                "bond_facet",
                "direction_category",
                "group",
                "group_category",
                "i",
                "leftmost",
                "length",
                "letter_category",
                "middle",
                "object_category",
                "rightmost",
                "sameness",
                "sameness_group",
                "string_position_category",
                "whole",
            )
        }
        self.numbers = []

    def __getitem__(self, name):
        return self._nodes[name]

    def activate_node_from_workspace(self, name):
        self.activate_node_from_workspace_called += 1


class MockWorkspace:
    def __init__(self):
        self.objects = []
        self.break_bond_called = 0
        self.break_group_called = 0
        self.break_correspondence_called = 0

    def break_bond(self, bond):
        self.break_bond_called += 1

    def break_group(self, group):
        self.break_group_called += 1

    def break_correspondence(self, correspondence):
        self.break_correspondence_called += 1


class MockWorkspaceString:
    def __init__(self, groups):
        self.bonds = []
        self.groups = groups
        self.add_group_called = 0
        self.delete_proposed_group_called = 0

    def add_group(self, group):
        self.add_group_called += 1
        self.groups.append(group)

    def delete_proposed_group(self, group):
        self.delete_proposed_group_called += 1


def test_transfers_descriptions_and_fizzles_if_group_exists():
    workspace = MockWorkspace()
    slipnet = MockSlipnet()
    coderack = Mock()
    proposed_group = Mock()
    proposed_group.descriptions = [Mock()]
    existing_group = Mock()
    existing_group.descriptions = [Mock()]
    existing_group.has_description = lambda description: False
    existing_group.add_description_called = 0
    existing_group.add_description = lambda description: setattr(
        existing_group,
        "add_description_called",
        existing_group.add_description_called + 1,
    )

    # Simulate that the group already exists in the workspace
    workspace_string = MockWorkspaceString(groups=[])
    workspace_string.get_group_if_present = lambda group: existing_group
    proposed_group.string = workspace_string

    builder = GroupBuilder(
        urgency_bin=0,
        coderack=coderack,
        workspace=workspace,
        slipnet=slipnet,
        proposed_group=proposed_group,
    )

    # Run the builder
    result = builder.run(temperature=0.5)

    assert slipnet.activate_node_from_workspace_called == 1
    assert existing_group.add_description_called == len(proposed_group.descriptions)
    assert workspace_string.delete_proposed_group_called == 1


def test_fizzles_if_bonds_no_longer_exist():
    workspace = MockWorkspace()
    slipnet = MockSlipnet()
    coderack = Mock()
    proposed_group = Mock()
    bond_1 = Mock()
    bond_2 = Mock()
    proposed_group.bonds = [bond_1, bond_2]
    proposed_group.string = MockWorkspaceString(groups=[])
    proposed_group.string.bonds = [bond_1]
    proposed_group.get_bonds_to_be_flipped = lambda: []
    proposed_group.left_object = Mock()
    proposed_group.right_object = Mock()

    proposed_group.string.get_group_if_present = lambda group: None

    builder = GroupBuilder(
        urgency_bin=0,
        coderack=coderack,
        workspace=workspace,
        slipnet=slipnet,
        proposed_group=proposed_group,
    )

    # Run the builder
    result = builder.run(temperature=0.5)
    assert result == Fizzle(FizzleReason.REQUIRED_BONDS_NO_LONGER_EXIST)

    assert slipnet.activate_node_from_workspace_called == 0
    assert workspace.break_bond_called == 0
    assert workspace.break_group_called == 0
    assert workspace.break_correspondence_called == 0


def test_fizzles_if_bonds_to_be_flipped_lose_fight():
    workspace = MockWorkspace()
    slipnet = MockSlipnet()
    coderack = Mock()
    proposed_group = Mock()
    proposed_group.__len__ = lambda x: 2
    bond_1, bond_2 = Mock(), Mock()
    proposed_group.bonds = [bond_1, bond_2]
    proposed_group.string = MockWorkspaceString(groups=[])
    proposed_group.string.bonds = [bond_1, bond_2]
    proposed_group.get_bonds_to_be_flipped = lambda: [Mock()]
    proposed_group.left_object = Mock()
    proposed_group.right_object = Mock()

    # Simulate that the bonds still exist
    proposed_group.string.get_group_if_present = lambda group: None

    # Patch the structure_beats_structures function to always return False
    original_structure_beats_structures = group_builder.structure_beats_structures
    group_builder.structure_beats_structures = lambda *args, **kwargs: False

    builder = GroupBuilder(
        urgency_bin=0,
        coderack=coderack,
        workspace=workspace,
        slipnet=slipnet,
        proposed_group=proposed_group,
    )

    # Run the builder
    result = builder.run(temperature=0.5)

    assert slipnet.activate_node_from_workspace_called == 0
    assert workspace.break_bond_called == 0
    assert workspace.break_group_called == 0
    assert workspace.break_correspondence_called == 0

    # Restore the original function
    group_builder.structure_beats_structures = original_structure_beats_structures


def test_fizzles_if_incompatible_structures_win_fight():
    workspace = MockWorkspace()
    slipnet = MockSlipnet()
    coderack = Mock()
    proposed_group = Mock()
    obj_1, obj_2 = Mock(), Mock()
    obj_1.correspondence = None
    obj_2.correspondence = None
    obj_1.group = Mock()
    obj_2.group = Mock()
    obj_1.group.equates_to.return_value = False
    obj_2.group.equates_to.return_value = False
    proposed_group.objects = [obj_1, obj_2]
    proposed_group.__len__ = lambda x: 2
    bond_1, bond_2 = Mock(), Mock()
    proposed_group.bonds = [bond_1, bond_2]
    proposed_group.string = MockWorkspaceString(groups=[])
    proposed_group.string.bonds = [bond_1, bond_2]
    proposed_group.get_bonds_to_be_flipped = lambda: []
    proposed_group.left_object = Mock()
    proposed_group.right_object = Mock()

    # Simulate that the bonds still exist
    proposed_group.string.get_group_if_present = lambda group: None

    # Patch the structure_beats_structures function to always return False
    original_structure_beats_structures = group_builder.structure_beats_structures
    group_builder.structure_beats_structures = lambda *args, **kwargs: False

    builder = GroupBuilder(
        urgency_bin=0,
        coderack=coderack,
        workspace=workspace,
        slipnet=slipnet,
        proposed_group=proposed_group,
    )

    # Run the builder
    result = builder.run(temperature=0.5)

    assert slipnet.activate_node_from_workspace_called == 0
    assert workspace.break_bond_called == 0
    assert workspace.break_group_called == 0
    assert workspace.break_correspondence_called == 0

    # Restore the original function
    group_builder.structure_beats_structures = original_structure_beats_structures


def test_breaks_incompatible_structures_flips_bonds_and_builds_group():
    workspace = MockWorkspace()
    slipnet = MockSlipnet()
    coderack = Mock()
    proposed_group = Mock()
    proposed_group.__len__ = lambda x: 2
    obj_1, obj_2 = Mock(), Mock()
    obj_1.correspondence = None
    obj_2.correspondence = None
    obj_1.group = Mock()
    obj_2.group = Mock()
    obj_1.group.equates_to.return_value = False
    obj_2.group.equates_to.return_value = False
    proposed_group.objects = [obj_1, obj_2]
    bond_1, bond_2 = Mock(), Mock()
    proposed_group.bonds = [bond_1, bond_2]
    proposed_group.string = MockWorkspaceString(groups=[])
    proposed_group.string.bonds = [bond_1, bond_2]
    proposed_group.get_bonds_to_be_flipped = lambda: []
    proposed_group.left_object = Mock()
    proposed_group.right_object = Mock()
    proposed_group.left_object.get_descriptor.return_value = slipnet["i"]
    proposed_group.spans_whole_string.return_value = False
    proposed_group.is_leftmost_in_string.return_value = True
    proposed_group.group_category = slipnet["sameness_group"]
    proposed_group.direction_category = None
    proposed_group.bond_category = slipnet["sameness"]
    proposed_group.descriptions = [
        SimpleNamespace(descriptor=SimpleNamespace(name="descriptor1"))
    ]
    proposed_group.bond_descriptions = []
    bond_1.bond_facet = slipnet["letter_category"]
    bond_2.bond_facet = slipnet["letter_category"]

    def add_description(description):
        if description.is_bond_description():
            proposed_group.bond_descriptions.append(description)
        else:
            proposed_group.descriptions.append(description)

    proposed_group.add_description.side_effect = add_description

    # Simulate that the bonds still exist
    proposed_group.string.get_group_if_present = lambda group: None

    # Patch the structure_beats_structures function to always return True
    original_structure_beats_structures = group_builder.structure_beats_structures
    group_builder.structure_beats_structures = lambda *args, **kwargs: True

    builder = GroupBuilder(
        urgency_bin=0,
        coderack=coderack,
        workspace=workspace,
        slipnet=slipnet,
        proposed_group=proposed_group,
    )

    # Run the builder
    result = builder.run(temperature=0.5)

    assert slipnet.activate_node_from_workspace_called == 5
    assert workspace.break_group_called == 2
    assert proposed_group.string.add_group_called == 1
    assert [
        (description.facet.name, description.descriptor.name)
        for description in proposed_group.descriptions[1:]
    ] == [
        ("object_category", "group"),
        ("string_position_category", "leftmost"),
        ("letter_category", "i"),
        ("group_category", "sameness_group"),
    ]
    assert [
        (description.facet.name, description.descriptor.name)
        for description in proposed_group.bond_descriptions
    ] == [
        ("bond_facet", "letter_category"),
        ("bond_category", "sameness"),
    ]
    assert result == Finish()

    # Restore the original function
    group_builder.structure_beats_structures = original_structure_beats_structures
