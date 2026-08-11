from types import SimpleNamespace
from unittest.mock import Mock

from copycat.codelets.scouts.group_scouts import TopDownCategoryGroupScout
from copycat.codelets.strength_testers import GroupStrengthTester
from copycat.codelet_result import Finish, Fizzle, FizzleReason
from copycat.workspace_objects import Group, Letter
from copycat.workspace_string import WorkspaceString


def test_run(monkeypatch):
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
        def __init__(self, nodes):
            self.nodes = nodes
            self.activate_called = 0

        def __getitem__(self, name):
            return self.nodes[name]

        def activate_node_from_workspace(self, name):
            self.activate_called += 1

    right = SimpleNamespace(name="right", activation=1.0)
    left = SimpleNamespace(name="left", activation=0.0)
    right.get_related_node = lambda relation: left if relation == "opposite" else None
    left.get_related_node = lambda relation: right if relation == "opposite" else None
    right.get_descriptor_support = Mock(return_value=1.0)
    left.get_descriptor_support = Mock(return_value=0.0)

    successor_group = SimpleNamespace(name="successor_group")
    sameness_group = SimpleNamespace(name="sameness_group")
    successor = SimpleNamespace(name="successor", bond_degree_of_association=0.5)
    predecessor = SimpleNamespace(name="predecessor", bond_degree_of_association=0.5)
    sameness = SimpleNamespace(name="sameness", bond_degree_of_association=1.0)
    successor_group.get_related_node = (
        lambda relation: successor if relation == "bond_category" else None
    )
    sameness_group.get_related_node = (
        lambda relation: sameness if relation == "bond_category" else None
    )
    successor.get_related_node = lambda relation: (
        predecessor
        if relation == "opposite"
        else successor_group
        if relation == "group_category"
        else None
    )
    predecessor.get_related_node = lambda relation: (
        successor
        if relation == "opposite"
        else SimpleNamespace(name="predecessor_group")
        if relation == "group_category"
        else None
    )
    sameness.get_related_node = lambda relation: (
        sameness_group if relation == "group_category" else None
    )
    group = SimpleNamespace(name="group")
    length = SimpleNamespace(name="length", activation=0.0)
    slipnet = MockSlipnet(
        {
            "right": right,
            "left": left,
            "successor_group": successor_group,
            "sameness_group": sameness_group,
            "group": group,
            "length": length,
        }
    )

    initial_string = WorkspaceString()
    target_string = WorkspaceString()
    initial_string.intra_string_unhappiness = 1.0
    target_string.intra_string_unhappiness = 0.0
    initial_string.distribution_of_bond_counts = [2]
    target_string.distribution_of_bond_counts = [2]
    a = Letter(initial_string, SimpleNamespace(name="a"), 0)
    b = Letter(initial_string, SimpleNamespace(name="b"), 1)
    c = Letter(initial_string, SimpleNamespace(name="c"), 2)
    initial_string.add_letter(a)
    initial_string.add_letter(b)
    initial_string.add_letter(c)
    initial_string.choose_object = Mock()
    workspace = SimpleNamespace(
        initial_string=initial_string,
        target_string=target_string,
    )
    coderack = MockCoderack()
    selected_random_number = [0.99]
    monkeypatch.setattr(
        "copycat.codelets.scouts.group_scouts.top_down_category_group_scout.random.random",
        lambda: selected_random_number[0],
    )

    scout = TopDownCategoryGroupScout(
        urgency_bin=0,
        coderack=coderack,
        slipnet=slipnet,
        workspace=workspace,
        group_category=successor_group,
    )

    # The chosen object already spans the whole string.
    initial_string.choose_object.return_value = SimpleNamespace(
        spans_whole_string=lambda: True
    )
    result = scout.run(temperature=0.0)
    assert result == Fizzle(FizzleReason.OBJECT_SPANS_WHOLE_STRING)
    assert coderack.post_called == 0
    assert initial_string.proposed_groups == []
    assert slipnet.activate_called == 0

    # A group cannot be used as the only object in a new group.
    chosen_group = Group(
        string=initial_string,
        left_position=0,
        right_position=0,
        objects=[a],
        bonds=[],
        group_category=successor_group,
        direction_category=right,
        bond_category=successor,
    )
    initial_string.choose_object.return_value = chosen_group
    result = scout.run(temperature=0.0)
    assert result == Fizzle(FizzleReason.CANNOT_MAKE_GROUP_FROM_SINGLE_GROUP)
    assert coderack.post_called == 0
    assert initial_string.proposed_groups == []
    assert slipnet.activate_called == 0

    # A group with a bond of the wrong category is still a single-group case.
    chosen_group.right_bond = SimpleNamespace(bond_category=predecessor)
    result = scout.run(temperature=0.0)
    assert result == Fizzle(FizzleReason.CANNOT_MAKE_GROUP_FROM_SINGLE_GROUP)
    assert coderack.post_called == 0
    assert initial_string.proposed_groups == []
    assert slipnet.activate_called == 0

    # A letter without local group support does not become a singleton group.
    a.right_bond = None
    initial_string.choose_object.return_value = a
    selected_random_number[0] = 0.99
    result = scout.run(temperature=0.0)
    assert result == Fizzle(FizzleReason.NOT_ENOUGH_SUPPORT_FOR_SINGLE_LETTER_GROUP)
    assert coderack.post_called == 0
    assert initial_string.proposed_groups == []
    assert slipnet.activate_called == 0
    left.get_descriptor_support.assert_called_with(initial_string, group)
    right.get_descriptor_support.assert_called_with(initial_string, group)

    # A bond of the wrong category is treated like no suitable first bond.
    a.right_bond = SimpleNamespace(bond_category=predecessor)
    result = scout.run(temperature=0.0)
    assert result == Fizzle(FizzleReason.NOT_ENOUGH_SUPPORT_FOR_SINGLE_LETTER_GROUP)
    assert coderack.post_called == 0
    assert initial_string.proposed_groups == []
    assert slipnet.activate_called == 0

    # Strong local support allows a directed singleton group to be proposed.
    a.right_bond = None
    supporting_left_successor_group = Group(
        string=initial_string,
        left_position=1,
        right_position=1,
        objects=[b],
        bonds=[],
        group_category=successor_group,
        direction_category=left,
        bond_category=successor,
    )
    supporting_right_successor_group = Group(
        string=initial_string,
        left_position=2,
        right_position=2,
        objects=[c],
        bonds=[],
        group_category=successor_group,
        direction_category=right,
        bond_category=successor,
    )
    initial_string.add_group(supporting_left_successor_group)
    initial_string.add_group(supporting_right_successor_group)
    b.group = supporting_left_successor_group
    c.group = supporting_right_successor_group
    length.activation = 1.0
    selected_random_number[0] = 0.0
    result = scout.run(temperature=0.0)
    assert result == Finish()
    assert coderack.post_called == 1
    assert isinstance(coderack.posted_codelets[-1], GroupStrengthTester)
    proposed_group = coderack.posted_codelets[-1].proposed_group
    assert proposed_group.objects == [a]
    assert proposed_group.bonds == []
    assert proposed_group.group_category == successor_group
    assert proposed_group.direction_category in [left, right]
    assert proposed_group.bond_category == successor
    assert proposed_group in initial_string.proposed_groups
    assert slipnet.activate_called == 0

    # Without local support, a sameness singleton group also fizzles.
    initial_string.delete_group(supporting_left_successor_group)
    initial_string.delete_group(supporting_right_successor_group)
    b.group = None
    c.group = None
    sameness_scout = TopDownCategoryGroupScout(
        urgency_bin=0,
        coderack=coderack,
        slipnet=slipnet,
        workspace=workspace,
        group_category=sameness_group,
    )
    length.activation = 0.0
    selected_random_number[0] = 0.99
    result = sameness_scout.run(temperature=0.0)
    assert result == Fizzle(FizzleReason.NOT_ENOUGH_SUPPORT_FOR_SINGLE_LETTER_GROUP)
    assert coderack.post_called == 1
    assert slipnet.activate_called == 0

    # Strong local support allows a directionless sameness singleton group.
    supporting_sameness_group = Group(
        string=initial_string,
        left_position=1,
        right_position=1,
        objects=[b],
        bonds=[],
        group_category=sameness_group,
        direction_category=None,
        bond_category=sameness,
    )
    initial_string.add_group(supporting_sameness_group)
    b.group = supporting_sameness_group
    length.activation = 1.0
    selected_random_number[0] = 0.0
    result = sameness_scout.run(temperature=0.0)
    assert result == Finish()
    assert coderack.post_called == 2
    assert isinstance(coderack.posted_codelets[-1], GroupStrengthTester)
    proposed_group = coderack.posted_codelets[-1].proposed_group
    assert proposed_group.objects == [a]
    assert proposed_group.bonds == []
    assert proposed_group.group_category == sameness_group
    assert proposed_group.direction_category is None
    assert proposed_group.bond_category == sameness
    assert proposed_group in initial_string.proposed_groups
    assert slipnet.activate_called == 0

    initial_string.delete_group(supporting_sameness_group)
    b.group = None
    bond_facet = SimpleNamespace(name="letter_category")
    a_to_b = SimpleNamespace(
        bond_category=successor,
        bond_facet=bond_facet,
        direction_category=right,
        left_object=a,
        right_object=b,
    )
    b_to_c = SimpleNamespace(
        bond_category=successor,
        bond_facet=bond_facet,
        direction_category=right,
        left_object=b,
        right_object=c,
    )
    a_to_b.get_object = lambda direction: (a if direction.name == "left" else b)
    b_to_c.get_object = lambda direction: (b if direction.name == "left" else c)
    a.left_bond = None
    a.right_bond = a_to_b
    b.left_bond = a_to_b
    b.right_bond = b_to_c
    c.left_bond = b_to_c
    c.right_bond = None

    # A matching first bond is enough to propose a two-object group.
    initial_string.choose_object.return_value = a
    a_to_b.choose_neighbour = lambda direction: None
    result = scout.run(temperature=0.0)
    assert result == Finish()
    assert coderack.post_called == 3
    proposed_group = coderack.posted_codelets[-1].proposed_group
    assert proposed_group.objects == [a, b]
    assert proposed_group.bonds == [a_to_b]
    assert proposed_group.group_category == successor_group
    assert proposed_group.direction_category == right
    assert proposed_group.bond_category == successor
    assert proposed_group in initial_string.proposed_groups
    assert slipnet.activate_called == 0

    # Compatible bonds in the scan direction are included in the group.
    a_to_b.choose_neighbour = (
        lambda direction: b_to_c if direction.name == "right" else None
    )
    b_to_c.choose_neighbour = (
        lambda direction: None if direction.name == "right" else a_to_b
    )
    result = scout.run(temperature=0.0)
    assert result == Finish()
    assert coderack.post_called == 4
    proposed_group = coderack.posted_codelets[-1].proposed_group
    assert proposed_group.objects == [a, b, c]
    assert proposed_group.bonds == [a_to_b, b_to_c]
    assert proposed_group.group_category == successor_group
    assert proposed_group.direction_category == right
    assert proposed_group.bond_category == successor
    assert proposed_group in initial_string.proposed_groups
    assert slipnet.activate_called == 0

    # An oppositely directed predecessor bond is included in flipped form.
    flipped_b_to_c = SimpleNamespace(name="flipped-b-to-c")
    b_to_c.bond_category = predecessor
    b_to_c.direction_category = left
    b_to_c.get_flipped_version = lambda: flipped_b_to_c
    result = scout.run(temperature=0.0)
    assert result == Finish()
    assert coderack.post_called == 5
    proposed_group = coderack.posted_codelets[-1].proposed_group
    assert proposed_group.objects == [a, b, c]
    assert proposed_group.bonds == [a_to_b, flipped_b_to_c]
    assert proposed_group.group_category == successor_group
    assert proposed_group.direction_category == right
    assert proposed_group.bond_category == successor
    assert proposed_group in initial_string.proposed_groups
    assert slipnet.activate_called == 0

    # An incompatible second bond stops the scan without preventing a proposal.
    b_to_c.direction_category = right
    result = scout.run(temperature=0.0)
    assert result == Finish()
    assert coderack.post_called == 6
    proposed_group = coderack.posted_codelets[-1].proposed_group
    assert proposed_group.objects == [a, b]
    assert proposed_group.bonds == [a_to_b]
    assert proposed_group.group_category == successor_group
    assert proposed_group.direction_category == right
    assert proposed_group.bond_category == successor
    assert proposed_group in initial_string.proposed_groups
    assert slipnet.activate_called == 0

    # A chain of directionless sameness bonds proposes a sameness group.
    a_to_b.bond_category = sameness
    a_to_b.direction_category = None
    b_to_c.bond_category = sameness
    b_to_c.direction_category = None
    result = sameness_scout.run(temperature=0.0)
    assert result == Finish()
    assert coderack.post_called == 7
    proposed_group = coderack.posted_codelets[-1].proposed_group
    assert proposed_group.objects == [a, b, c]
    assert proposed_group.bonds == [a_to_b, b_to_c]
    assert proposed_group.group_category == sameness_group
    assert proposed_group.direction_category is None
    assert proposed_group.bond_category == sameness
    assert proposed_group in initial_string.proposed_groups
    assert slipnet.activate_called == 0

    # Scanning left builds the same directed group from the opposite end.
    a_to_b.bond_category = successor
    a_to_b.direction_category = right
    b_to_c.bond_category = successor
    b_to_c.direction_category = right
    initial_string.choose_object.return_value = c
    result = scout.run(temperature=0.0)
    assert result == Finish()
    assert coderack.post_called == 8
    proposed_group = coderack.posted_codelets[-1].proposed_group
    assert proposed_group.objects == [b, c, a]
    assert proposed_group.bonds == [b_to_c, a_to_b]
    assert proposed_group.group_category == successor_group
    assert proposed_group.direction_category == right
    assert proposed_group.bond_category == successor
    assert proposed_group in initial_string.proposed_groups
    assert slipnet.activate_called == 0
