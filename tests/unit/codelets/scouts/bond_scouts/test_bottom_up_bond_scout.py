from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from copycat.codelets.scouts.bond_scouts import BottomUpBondScout
from copycat.codelets.strength_testers import BondStrengthTester


def test_run():
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
    scout.run(temperature=0.0)
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
    from_obj_bond_facet = SimpleNamespace(
        facet=SimpleNamespace(
            name="from_description_facet",
            category=SimpleNamespace(name="bond_facet"),
            get_total_description_type_support=lambda x: 0.5,
        )
    )
    to_obj_bond_facet = SimpleNamespace(
        facet=SimpleNamespace(
            name="to_description_facet", category=SimpleNamespace(name="bond_facet")
        )
    )
    to_obj = Mock()
    to_obj.left_position = 1
    to_obj.descriptions = [to_obj_bond_facet]
    workspace.object.descriptions = [from_obj_bond_facet]
    workspace.object.choose_neighbor.return_value = to_obj
    scout.run(temperature=0.0)
    assert coderack.post_called == 0
    assert slipnet.activate_called == 0

    # Object with neighbor and shared bond facet but no bond category
    to_obj.descriptions = [from_obj_bond_facet, to_obj_bond_facet]
    link = SimpleNamespace(to_node=Mock(), label=None)
    from_obj_descriptor = SimpleNamespace(name="from_descriptor")
    from_obj_descriptor.outgoing_links = [link]
    workspace.object.get_descriptor.return_value = from_obj_descriptor
    scout.run(temperature=0.0)
    assert coderack.post_called == 0
    assert slipnet.activate_called == 0

    # Object with neighbor, shared bond facet, and bond category
    to_obj_descriptor = SimpleNamespace(name="to_descriptor")
    to_obj.get_descriptor.return_value = to_obj_descriptor
    link.to_node = to_obj_descriptor
    link.label = SimpleNamespace(name="successor", bond_degree_of_association=1)
    scout.run(temperature=0.0)
    assert coderack.post_called == 1
    assert slipnet.activate_called == 3
    assert isinstance(coderack.posted_codelets[0], BondStrengthTester)
