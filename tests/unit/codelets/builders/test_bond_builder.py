from unittest.mock import Mock

import pytest

from copycat.codelets.builders import bond_builder
from copycat.codelets.builders import BondBuilder
from copycat.codelet_result import Finish, Fizzle, FizzleReason


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
    def __init__(self, bonds):
        self.bonds = bonds
        self.add_bond_called = 0

    def add_bond(self, bond):
        self.add_bond_called += 1
        self.bonds.append(bond)

    def delete_proposed_bond(self, bond):
        pass


def test_run_fizzles_if_argument_objects_no_longer_exist():
    workspace = MockWorkspace()
    bond = Mock()
    bond.from_object = Mock()
    bond.to_object = Mock()
    bond.from_object.outgoing_bonds = []
    bond.from_object.incoming_bonds = []
    bond.to_object.outgoing_bonds = []
    bond.to_object.incoming_bonds = []
    builder = BondBuilder(
        urgency_bin=0,
        coderack=Mock(),
        slipnet=Mock(),
        workspace=workspace,
        proposed_bond=bond,
    )
    result = builder.run(temperature=0.0)
    assert result == Fizzle(FizzleReason.OBJECTS_NO_LONGER_EXIST)
    # If the from and to objects don't exist, the bond shouldn't be added to them
    assert bond.from_object.outgoing_bonds == []
    assert bond.from_object.incoming_bonds == []
    assert bond.to_object.outgoing_bonds == []
    assert bond.to_object.incoming_bonds == []


def test_run_fizzles_if_bond_has_already_been_built():
    workspace = MockWorkspace()
    bond = Mock()
    bond.from_object = Mock()
    bond.to_object = Mock()
    workspace.objects.extend([bond.from_object, bond.to_object])
    bond.string = MockWorkspaceString([bond])
    builder = BondBuilder(
        urgency_bin=0,
        coderack=Mock(),
        slipnet=Mock(),
        workspace=workspace,
        proposed_bond=bond,
    )
    builder.run(temperature=0.0)
    # If the bond is already in the string, add_bond shouldn't be called
    assert bond.string.add_bond_called == 0


def test_fizzles_if_incompatible_bonds_beat_proposed_bond(monkeypatch):
    workspace = MockWorkspace()
    bond = Mock()
    bond.from_object = Mock()
    bond.to_object = Mock()
    workspace.objects.extend([bond.from_object, bond.to_object])
    bond.string = MockWorkspaceString([])
    incompatible_bonds = [Mock(), Mock()]
    builder = BondBuilder(
        urgency_bin=0,
        coderack=Mock(),
        slipnet=Mock(),
        workspace=workspace,
        proposed_bond=bond,
    )
    builder._get_incompatible_bonds = lambda: incompatible_bonds

    monkeypatch.setattr(
        bond_builder, "structure_beats_structures", lambda *_, **__: False
    )

    builder.run(temperature=0.5)
    assert bond.string.add_bond_called == 0


def test_fizzles_if_incompatible_groups_beat_proposed_bond(monkeypatch):
    workspace = MockWorkspace()
    bond = Mock()
    bond.from_object = Mock()
    bond.to_object = Mock()
    workspace.objects.extend([bond.from_object, bond.to_object])
    bond.string = MockWorkspaceString([])
    incompatible_bonds = [Mock(), Mock()]
    incompatible_groups = [Mock(), Mock()]
    incompatible_groups[0].letter_span = 2
    incompatible_groups[1].letter_span = 3
    builder = BondBuilder(
        urgency_bin=0,
        coderack=Mock(),
        slipnet=Mock(),
        workspace=workspace,
        proposed_bond=bond,
    )
    builder._get_incompatible_bonds = lambda: incompatible_bonds
    builder._get_incompatible_groups = lambda: incompatible_groups

    def mock_structure_beats_structures(
        proposed_structure,
        proposed_structure_weight,
        incompatible_structures,
        incompatible_structure_weight,
        temperature,
    ):
        if incompatible_structures == incompatible_bonds:
            return True
        elif incompatible_structures == incompatible_groups:
            return False
        else:
            raise ValueError("Unexpected incompatible structures")

    # return True to get past incompatible bonds check, but False for incompatible groups check
    monkeypatch.setattr(
        bond_builder, "structure_beats_structures", mock_structure_beats_structures
    )

    builder.run(temperature=0.5)
    assert bond.string.add_bond_called == 0


def test_fizzles_if_incompatible_correspondences_beat_proposed_bond(monkeypatch):
    workspace = MockWorkspace()
    bond = Mock()
    bond.from_object = Mock()
    bond.to_object = Mock()
    workspace.objects.extend([bond.from_object, bond.to_object])
    bond.string = MockWorkspaceString([])
    incompatible_bonds = [Mock(), Mock()]
    incompatible_groups = [Mock(), Mock()]
    incompatible_groups[0].letter_span = 2
    incompatible_groups[1].letter_span = 3
    incompatible_correspondences = [Mock(), Mock()]
    builder = BondBuilder(
        urgency_bin=0,
        coderack=Mock(),
        slipnet=Mock(),
        workspace=workspace,
        proposed_bond=bond,
    )
    builder._get_incompatible_bonds = lambda: incompatible_bonds
    builder._get_incompatible_groups = lambda: incompatible_groups
    builder._get_incompatible_correspondences = lambda: incompatible_correspondences

    def mock_structure_beats_structures(
        proposed_structure,
        proposed_structure_weight,
        incompatible_structures,
        incompatible_structure_weight,
        temperature,
    ):
        if incompatible_structures == incompatible_bonds:
            return True
        elif incompatible_structures == incompatible_groups:
            return True
        elif incompatible_structures == incompatible_correspondences:
            return False
        else:
            raise ValueError("Unexpected incompatible structures")

    # return True to get past incompatible bonds and groups check, but False for incompatible correspondences check
    monkeypatch.setattr(
        bond_builder, "structure_beats_structures", mock_structure_beats_structures
    )

    builder.run(temperature=0.5)
    assert bond.string.add_bond_called == 0


def test_builds_bond_and_breaks_incompatible_structures(monkeypatch):
    workspace = MockWorkspace()
    bond = Mock()
    bond.from_object = Mock()
    bond.to_object = Mock()
    workspace.objects.extend([bond.from_object, bond.to_object])
    bond.string = MockWorkspaceString([])
    incompatible_bonds = [Mock(), Mock()]
    incompatible_groups = [Mock(), Mock()]
    incompatible_groups[0].letter_span = 2
    incompatible_groups[1].letter_span = 3
    incompatible_correspondences = [Mock(), Mock()]

    builder = BondBuilder(
        urgency_bin=0,
        coderack=Mock(),
        slipnet=Mock(),
        workspace=workspace,
        proposed_bond=bond,
    )
    builder._get_incompatible_bonds = lambda: incompatible_bonds
    builder._get_incompatible_groups = lambda: incompatible_groups
    builder._get_incompatible_correspondences = lambda: incompatible_correspondences

    # return True to get past incompatible bonds, groups, and correspondences check
    monkeypatch.setattr(
        bond_builder, "structure_beats_structures", lambda *_, **__: True
    )

    result = builder.run(temperature=0.5)
    assert bond.string.add_bond_called == 1
    assert result == Finish()
    assert builder.workspace.break_bond_called == 2
    assert builder.workspace.break_group_called == 2
    assert builder.workspace.break_correspondence_called == 2
