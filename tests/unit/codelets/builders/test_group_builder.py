from unittest.mock import Mock

import pytest

from copycat.codelets.builders import group_builder
from copycat.codelets.builders import GroupBuilder


class MockSlipnet:
    def __init__(self):
        self.activate_node_from_workspace_called = 0

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
    builder.run(temperature=0.5)

    assert slipnet.activate_node_from_workspace_called == 1
    assert existing_group.add_description_called == len(proposed_group.descriptions)
    assert workspace_string.delete_proposed_group_called == 1


def test_fizzles_if_bonds_no_longer_exist():
    workspace = MockWorkspace()
    slipnet = MockSlipnet()
    coderack = Mock()
    proposed_group = Mock()
    proposed_group.bonds = [Mock(), Mock()]
    proposed_group.string = MockWorkspaceString(groups=[])
    proposed_group.get_bonds_to_be_flipped = lambda: []
    proposed_group.left_object = Mock()
    proposed_group.right_object = Mock()

    # Simulate that the bonds no longer exist
    proposed_group.string.get_group_if_present = lambda group: None
    builder = GroupBuilder(
        urgency_bin=0,
        coderack=coderack,
        workspace=workspace,
        slipnet=slipnet,
        proposed_group=proposed_group,
    )

    # Run the builder
    builder.run(temperature=0.5)

    assert slipnet.activate_node_from_workspace_called == 0
    assert workspace.break_bond_called == 0
    assert workspace.break_group_called == 0
    assert workspace.break_correspondence_called == 0
