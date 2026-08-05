from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from copycat.codelets.scouts.group_scouts import TopDownDirectionGroupScout
from copycat.codelets.strength_testers import GroupStrengthTester
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
        right_node = SimpleNamespace(name="right")
        left_node = SimpleNamespace(name="left")

        def __init__(self):
            self.activate_called = 0

        def __getitem__(self, name):
            return SimpleNamespace(name=name)

        def activate_node_from_workspace(self, name):
            self.activate_called += 1

        def get_node_activation(self, name):
            return 0.5

        def get_node(self, name):
            return (
                self.right_node
                if name == "right"
                else self.left_node
                if name == "left"
                else None
            )

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

    direction_category = slipnet.right_node
    bond_category = SimpleNamespace(name="successor", bond_degree_of_association=0.5)
    group_category = SimpleNamespace(name="successor_group")
    opposite_bond_category = SimpleNamespace(name="predecessor")
    bond_category.get_related_node = lambda relation: (
        opposite_bond_category
        if relation == "opposite"
        else group_category
        if relation == "group_category"
        else None
    )
    group_category.get_related_node = lambda relation: (
        bond_category if relation == "bond_category" else None
    )
    slipnet.right_node.get_related_node = lambda relation: (
        slipnet.left_node if relation == "opposite" else None
    )
    slipnet.left_node.get_related_node = lambda relation: (
        slipnet.right_node if relation == "opposite" else None
    )

    scout = TopDownDirectionGroupScout(
        urgency_bin=0,
        coderack=coderack,
        slipnet=slipnet,
        workspace=workspace,
        direction_category=direction_category,
    )

    # Chosen object spans whole string
    workspace.initial_string.choose_object.return_value = SimpleNamespace(
        spans_whole_string=lambda: True
    )
    result = scout.run(temperature=0.0)
    assert result == Fizzle(FizzleReason.OBJECT_SPANS_WHOLE_STRING)
    assert coderack.post_called == 0
    assert slipnet.activate_called == 0

    # First bond is None
    workspace.initial_string.choose_object.return_value = SimpleNamespace(
        is_leftmost_in_string=lambda: True,
        right_bond=None,
        spans_whole_string=lambda: False,
    )
    workspace.initial_string.distribution_of_bond_counts = [2]
    scout.run(temperature=0.0)
    assert coderack.post_called == 0
    assert slipnet.activate_called == 0

    # First bond has wrong direction
    first_bond = SimpleNamespace(direction_category=SimpleNamespace(name="left"))
    workspace.initial_string.choose_object.return_value = SimpleNamespace(
        is_leftmost_in_string=lambda: True,
        right_bond=first_bond,
        spans_whole_string=lambda: False,
    )
    scout.run(temperature=0.0)
    assert coderack.post_called == 0
    assert slipnet.activate_called == 0

    # set up a string with multiple objects and bonds
    a = SimpleNamespace(
        string=workspace.initial_string,
        left_position=0,
        right_position=0,
        is_leftmost_in_string=lambda: True,
        is_rightmost_in_string=False,
        spans_whole_string=lambda: False,
    )
    b = SimpleNamespace(
        string=workspace.initial_string,
        left_position=1,
        right_position=1,
        is_leftmost_in_string=False,
        is_rightmost_in_string=False,
        spans_whole_string=lambda: False,
    )
    c = SimpleNamespace(
        string=workspace.initial_string,
        left_position=2,
        right_position=2,
        is_leftmost_in_string=False,
        is_rightmost_in_string=True,
        spans_whole_string=lambda: False,
    )
    a_to_b = SimpleNamespace(
        bond_category=bond_category,
        bond_facet=SimpleNamespace(name="facet"),
        direction_category=slipnet.right_node,
        left_object=a,
        right_object=b,
    )
    b_to_c = SimpleNamespace(
        bond_category=bond_category,
        bond_facet=SimpleNamespace(name="facet"),
        direction_category=slipnet.right_node,
        left_object=b,
        right_object=c,
    )
    a_to_b.choose_neighbour = (
        lambda direction: b_to_c if direction.name == "right" else None
    )
    a_to_b.get_object = lambda position: a if position == "left" else b
    b_to_c.choose_neighbour = (
        lambda direction: None if direction.name == "right" else a_to_b
    )
    b_to_c.get_object = lambda position: b if position == "left" else c
    a.left_bond = None
    a.right_bond = a_to_b
    b.left_bond = a_to_b
    b.right_bond = b_to_c
    c.left_bond = b_to_c
    c.right_bond = None

    # Valid first bond
    workspace.initial_string.choose_object.return_value = a
    result = scout.run(temperature=0.0)
    assert coderack.post_called == 1
    assert result == Finish()
    assert isinstance(coderack.posted_codelets[0], GroupStrengthTester)
