from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from copycat.codelets.scouts.bond_scouts import TopDownCategoryBondScout
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
        initial_string = Mock()
        target_string = Mock()

        def choose_object(self, temperature, salience_function):
            return self.object

    coderack = MockCoderack()
    slipnet = MockSlipnet()
    workspace = MockWorkspace()
    workspace.initial_string.get_local_bond_category_relevance.return_value = 1.0
    workspace.initial_string.intra_string_unhappiness = 1.0
    workspace.target_string.get_local_bond_category_relevance.return_value = 0.0
    workspace.target_string.intra_string_unhappiness = 0.0

    bond_category = SimpleNamespace(name="successor", bond_degree_of_association=0.5)

    scout = TopDownCategoryBondScout(
        urgency_bin=0,
        coderack=coderack,
        slipnet=slipnet,
        workspace=workspace,
        bond_category=bond_category,
    )

    # No object to choose
    workspace.initial_string.choose_object.return_value = None
    scout.run(temperature=0.0)
    assert coderack.post_called == 0
    assert slipnet.activate_called == 0

    # Object with no neighbor
    object_1 = Mock()
    workspace.initial_string.choose_object.return_value = object_1
    object_1.left_position = 0
    object_1.choose_neighbor.return_value = None
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
    object_2 = Mock()
    object_2.left_position = 1
    object_2.descriptions = [to_obj_bond_facet]
    object_1.descriptions = [from_obj_bond_facet]
    object_1.choose_neighbor.return_value = object_2
    scout.run(temperature=0.0)
    assert coderack.post_called == 0
    assert slipnet.activate_called == 0

    # Object with neighbor and shared bond facet one object missing descriptor
    object_2.descriptions = [from_obj_bond_facet, to_obj_bond_facet]
    link = SimpleNamespace(to_node=Mock(), label=None)
    from_obj_descriptor = SimpleNamespace(name="from_descriptor")
    from_obj_descriptor.outgoing_links = [link]
    object_1.get_descriptor.return_value = from_obj_descriptor
    object_2.get_descriptor.return_value = None
    scout.run(temperature=0.0)
    assert coderack.post_called == 0
    assert slipnet.activate_called == 0

    # Object with neighbor, shared bond facet, and 1-2 bond category matches bond category
    to_obj_descriptor = SimpleNamespace(name="to_descriptor")
    object_2.get_descriptor.return_value = to_obj_descriptor
    link.to_node = to_obj_descriptor
    link.label = bond_category
    scout.run(temperature=0.0)
    assert coderack.post_called == 1
    assert slipnet.activate_called == 3
    assert isinstance(coderack.posted_codelets[0], BondStrengthTester)

    # Object with neighbor, shared bond facet, and 2-1 bond category matches bond category
    coderack.post_called = 0
    slipnet.activate_called = 0
    bond_category = SimpleNamespace(name="predecessor", bond_degree_of_association=0.5)
    scout.bond_category = bond_category
    link_2 = SimpleNamespace(to_node=from_obj_descriptor, label=bond_category)
    to_obj_descriptor.outgoing_links = [link_2]
    scout.run(temperature=0.0)
    assert coderack.post_called == 1
    assert slipnet.activate_called == 3
    assert isinstance(coderack.posted_codelets[0], BondStrengthTester)
