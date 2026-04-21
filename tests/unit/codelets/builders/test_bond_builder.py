from unittest.mock import Mock

import pytest

from copycat.codelets.builders import BondBuilder


def test_run_fizzles_if_argument_objects_no_longer_exist():
    class MockWorkspace:
        objects = []

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
    builder.run(temperature=0.0)
    # If the from and to objects don't exist, the bond shouldn't be added to them
    assert bond.from_object.outgoing_bonds == []
    assert bond.from_object.incoming_bonds == []
    assert bond.to_object.outgoing_bonds == []
    assert bond.to_object.incoming_bonds == []


def test_run_fizzles_if_bond_has_already_been_built():
    class MockWorkspace:
        objects = []

    class MockWorkspaceString:
        def __init__(self, bonds):
            self.bonds = bonds
            self.add_bond_called = 0

        def add_bond(self, bond):
            self.add_bond_called += 1
            self.bonds.append(bond)

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
