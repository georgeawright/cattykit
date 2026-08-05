from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from copycat.codelets.scouts.bond_scouts import TopDownDirectionBondScout
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
        initial_string = Mock()
        target_string = Mock()

        def choose_object(self, temperature, salience_function):
            return self.object

    coderack = MockCoderack()
    slipnet = MockSlipnet()
    workspace = MockWorkspace()
    workspace.initial_string.get_local_direction_category_relevance.return_value = 1.0
    workspace.initial_string.intra_string_unhappiness = 1.0
    workspace.target_string.get_local_direction_category_relevance.return_value = 0.0
    workspace.target_string.intra_string_unhappiness = 0.0

    direction_category = SimpleNamespace(name="left", bond_degree_of_association=0.5)

    scout = TopDownDirectionBondScout(
        urgency_bin=0,
        coderack=coderack,
        slipnet=slipnet,
        workspace=workspace,
        direction_category=direction_category,
    )

    # No object to choose
    workspace.initial_string.choose_object.return_value = None
    result = scout.run(temperature=0.0)
    assert result == Fizzle(FizzleReason.NO_OBJECTS)
    assert coderack.post_called == 0
    assert slipnet.activate_called == 0

    # Object with no neighbour
    object_1 = Mock()
    workspace.initial_string.choose_object.return_value = object_1
    object_1.left_position = 0
    object_1.choose_left_neighbour.return_value = None
    scout.run(temperature=0.0)
    assert coderack.post_called == 0
    assert slipnet.activate_called == 0

    # Object with neighbour but no shared bond facets
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
    object_2 = Mock()
    object_2.left_position = 1
    object_2.descriptions = [target_bond_facet]
    object_1.descriptions = [source_bond_facet]
    object_1.choose_left_neighbour.return_value = object_2
    scout.run(temperature=0.0)
    assert coderack.post_called == 0
    assert slipnet.activate_called == 0

    # Object with neighbour and shared bond facet one object missing descriptor
    object_2.descriptions = [source_bond_facet, target_bond_facet]
    link = SimpleNamespace(target=Mock(), label=None)
    source_descriptor = SimpleNamespace(name="source_descriptor")
    source_descriptor.outgoing_links = [link]
    object_1.get_descriptor.return_value = source_descriptor
    object_2.get_descriptor.return_value = None
    scout.run(temperature=0.0)
    assert coderack.post_called == 0
    assert slipnet.activate_called == 0

    # Object with neighbour, shared bond facet, but bond category is not directed
    target_descriptor = SimpleNamespace(name="target_descriptor")
    object_2.get_descriptor.return_value = target_descriptor
    link.target = target_descriptor
    bond_category = Mock()
    bond_category.name = "successor"
    bond_category.bond_degree_of_association = 0.5
    bond_category.is_directed.return_value = False
    link.label = bond_category
    scout.run(temperature=0.0)
    assert coderack.post_called == 0
    assert slipnet.activate_called == 0

    # Object with neighbour, shared bond facet, and bond category is directed
    bond_category.is_directed.return_value = True
    result = scout.run(temperature=0.0)
    assert coderack.post_called == 1
    assert result == Finish()
    assert slipnet.activate_called == 3
    assert isinstance(coderack.posted_codelets[0], BondStrengthTester)
