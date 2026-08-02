from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from copycat.codelets.scouts.bond_scouts import BottomUpBondScout
from copycat.codelets.strength_testers import BondStrengthTester
from copycat.codelet_result import Finish, Fizzle, FizzleReason


def test_run():
    class MockCoderack:
        def __init__(self):
            self.posted_codelets = []
            self.post_called = 0

        def post(self, codelet, temperature):
            self.post_called += 1
            self.posted_codelets.append(codelet)

        def get_urgency_level_from_activation(self, activation):
            return 0

    class MockSlipnet:
        def __init__(self):
            self.activate_called = 0

        def __getitem__(self, name):
            return SimpleNamespace(name=name)

        def activate_node_from_workspace(self, name):
            self.activate_called += 1

        def get_node_activation(self, name):
            return 0.5

    class MockWorkspace:
        object = None

        def choose_object(self, temperature, salience_function):
            return self.object

    coderack = MockCoderack()
    slipnet = MockSlipnet()
    workspace = MockWorkspace()

    scout = BottomUpBondScout(
        urgency_bin=0, coderack=coderack, slipnet=slipnet, workspace=workspace
    )

    # No object to choose
    result = scout.run(temperature=0.0)
    assert result == Fizzle(FizzleReason.NO_OBJECTS)
    assert coderack.post_called == 0
    assert slipnet.activate_called == 0

    # Object with no neighbor
    workspace.object = Mock()
    workspace.object.left_position = 0
    workspace.object.choose_neighbor.return_value = None
    scout.run(temperature=0.0)
    assert coderack.post_called == 0
    assert slipnet.activate_called == 0

    # Object with neighbor but no shared bond facets
    source_bond_facet = SimpleNamespace(
        facet=SimpleNamespace(
            name="source_description_facet",
            category=SimpleNamespace(name="bond_facet"),
            get_total_description_type_support=lambda x: 0.5,
        )
    )
    target_bond_facet = SimpleNamespace(
        facet=SimpleNamespace(
            name="target_description_facet", category=SimpleNamespace(name="bond_facet")
        )
    )
    target = Mock()
    target.left_position = 1
    target.descriptions = [target_bond_facet]
    workspace.object.descriptions = [source_bond_facet]
    workspace.object.choose_neighbor.return_value = target
    scout.run(temperature=0.0)
    assert coderack.post_called == 0
    assert slipnet.activate_called == 0

    # Object with neighbor and shared bond facet but no bond category
    target.descriptions = [source_bond_facet, target_bond_facet]
    link = SimpleNamespace(target=Mock(), label=None)
    source_descriptor = SimpleNamespace(name="source_descriptor")
    source_descriptor.outgoing_links = [link]
    workspace.object.get_descriptor.return_value = source_descriptor
    scout.run(temperature=0.0)
    assert coderack.post_called == 0
    assert slipnet.activate_called == 0

    # Object with neighbor, shared bond facet, and bond category
    target_descriptor = SimpleNamespace(name="target_descriptor")
    target.get_descriptor.return_value = target_descriptor
    link.target = target_descriptor
    link.label = SimpleNamespace(name="successor", bond_degree_of_association=1)
    result = scout.run(temperature=0.0)
    assert coderack.post_called == 1
    assert result == Finish()
    assert slipnet.activate_called == 3
    assert isinstance(coderack.posted_codelets[0], BondStrengthTester)
