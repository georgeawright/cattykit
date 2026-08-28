from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from copycat.workspace_object import WorkspaceObject
from copycat.workspace_objects import Group


class MockLetter:
    def __init__(self, id, string_position, string):
        self.id = id
        self.left_position = string_position
        self.right_position = string_position
        self.string = string
        self.intra_string_salience = 1
        self.letters = [self]


def test_has_recursive_group_member():
    string = SimpleNamespace()
    predecessor_category = SimpleNamespace()
    succesor_category = SimpleNamespace()
    left_category = SimpleNamespace()
    right_category = SimpleNamespace()
    object1 = WorkspaceObject(string, 0, 1)
    object2 = WorkspaceObject(string, 2, 3)
    group3 = Group(
        string, 1, 2, [object2], [], predecessor_category, left_category, None
    )
    group2 = Group(string, 2, 3, [object2], [], succesor_category, right_category, None)
    group1 = Group(
        string, 0, 2, [object1, group3], [], predecessor_category, left_category, None
    )

    assert group1.has_recursive_group_member(group1)
    assert group1.has_recursive_group_member(object1)
    assert group1.has_recursive_group_member(group3)
    assert group1.has_recursive_group_member(object2)

    assert not group1.has_recursive_group_member(group2)
    assert not group2.has_recursive_group_member(group1)


def test_has_description():
    group = Group(None, None, None, [], [], None, None, None)
    description = SimpleNamespace(
        facet=SimpleNamespace(name="test_facet"),
        descriptor=SimpleNamespace(name="test_descriptor"),
    )
    bond_description = SimpleNamespace(
        facet=SimpleNamespace(name="bond_facet"),
        descriptor=SimpleNamespace(name="test_descriptor"),
    )
    assert not group.has_description(description)
    assert not group.has_description(bond_description)
    group.descriptions.append(description)
    assert group.has_description(description)
    group.bond_descriptions.append(bond_description)
    assert group.has_description(bond_description)


@pytest.mark.parametrize(
    "descriptor, super_group_descriptors, sub_group_descriptors,"
    " other_group_descriptors, expected",
    [
        (
            "letter",
            ["super_descriptor"],
            ["sub_descriptor"],
            ["other_descriptor"],
            False,
        ),
        (
            "group",
            ["super_descriptor"],
            ["sub_descriptor"],
            ["other_descriptor"],
            False,
        ),
        (
            "one",
            ["super_descriptor"],
            ["sub_descriptor"],
            ["other_descriptor"],
            False,
        ),
        (
            "descriptor",
            ["super_descriptor"],
            ["sub_descriptor"],
            ["other_descriptor"],
            True,
        ),
        (
            "descriptor",
            ["super_descriptor"],
            ["sub_descriptor"],
            ["descriptor"],
            False,
        ),
        (
            "descriptor",
            ["super_descriptor"],
            ["descriptor"],
            ["other_descriptor"],
            True,
        ),
        (
            "descriptor",
            ["descriptor"],
            ["sub_descriptor"],
            ["other_descriptor"],
            True,
        ),
    ],
)
def test_is_distinguished_by(
    descriptor,
    super_group_descriptors,
    sub_group_descriptors,
    other_group_descriptors,
    expected,
):
    string = SimpleNamespace()

    slipnodes = {
        d: SimpleNamespace(name=d)
        for d in set(
            [descriptor]
            + super_group_descriptors
            + sub_group_descriptors
            + other_group_descriptors
        )
    }

    sub_group = Group(string, 0, 1, [], [], None, None, None)
    for d in sub_group_descriptors:
        sub_group.descriptions.append(SimpleNamespace(descriptor=slipnodes[d]))
    group = Group(string, 0, 2, [sub_group], [], None, None, None)
    sub_group.group = group
    group.descriptions.append(SimpleNamespace(descriptor=slipnodes[descriptor]))
    super_group = Group(string, 0, 3, [group], [], None, None, None)
    group.group = super_group
    for d in super_group_descriptors:
        super_group.descriptions.append(SimpleNamespace(descriptor=slipnodes[d]))
    other_group = Group(string, 4, 5, [], [], None, None, None)
    for d in other_group_descriptors:
        other_group.descriptions.append(SimpleNamespace(descriptor=slipnodes[d]))

    string.groups = [group, sub_group, super_group, other_group]

    assert expected == group.is_distinguished_by(slipnodes[descriptor])


@pytest.mark.parametrize(
    "bond_facet_name, bond_category_degree_of_association, length, expected",
    [
        ("letter_category", 1.0, 4, 1.0),
        ("length", 1.0, 4, 0.697208),
        ("letter_category", 0.5, 4, 0.697208),
        ("letter_category", 1.0, 1, 1.0),
        ("length", 1.0, 1, 0.278141),
    ],
)
def test_calculate_internal_strength(
    bond_facet_name, bond_category_degree_of_association, length, expected
):
    bond_facet = SimpleNamespace(name=bond_facet_name)
    related_node = SimpleNamespace(
        degree_of_association=bond_category_degree_of_association
    )
    group_category = Mock()
    group_category.get_related_node = (
        lambda x: related_node if x == "bond_category" else None
    )
    letters = [SimpleNamespace() for _ in range(length)]
    for letter in letters:
        letter.letters = [letter]
    group = Group(None, 0, 1, letters, [], group_category, None, None, bond_facet)

    assert group.calculate_internal_strength() == pytest.approx(expected)


@pytest.mark.parametrize(
    "string_length, group_length, spans, expected",
    [
        (3, 3, True, 1.0),
        (4, 3, False, None),
    ],
)
def test_external_strength_is_one_if_spans_whole_string_else_local_support(
    string_length, group_length, spans, expected
):
    string = SimpleNamespace(letters=[SimpleNamespace() for _ in range(string_length)])
    letters = [SimpleNamespace() for _ in range(group_length)]
    for letter in letters:
        letter.letters = [letter]
    group = Group(string, 0, 1, letters, [], None, None, None)

    assert spans == group.spans_whole_string()
    if spans:
        assert group.calculate_external_strength() == pytest.approx(expected)
    else:
        # assert local_support is called when group does not span whole string
        group._local_support = lambda: expected
        assert group.calculate_external_strength() == pytest.approx(expected)


def test_calculate_external_strength():
    predecessor_category = SimpleNamespace(name="predecessor_category")
    successor_category = SimpleNamespace(name="successor_category")
    left_category = SimpleNamespace(name="left")
    right_category = SimpleNamespace(name="right")
    letter_category = SimpleNamespace(name="letter_category")

    string_length = 6
    string = SimpleNamespace(letters=[])
    letter_0 = MockLetter(id="l0", string_position=0, string=string)
    letter_1 = MockLetter(id="l1", string_position=1, string=string)
    letter_2 = MockLetter(id="l2", string_position=2, string=string)
    letter_3 = MockLetter(id="l3", string_position=3, string=string)
    letter_4 = MockLetter(id="l4", string_position=4, string=string)
    letter_5 = MockLetter(id="l5", string_position=5, string=string)
    letter_0.choose_left_neighbour = lambda: None
    letter_0.choose_right_neighbour = lambda: letter_1
    letter_1.choose_left_neighbour = lambda: letter_0
    letter_1.choose_right_neighbour = lambda: letter_2
    letter_2.choose_left_neighbour = lambda: letter_1
    letter_2.choose_right_neighbour = lambda: letter_3
    letter_3.choose_left_neighbour = lambda: letter_2
    letter_3.choose_right_neighbour = lambda: letter_4
    letter_4.choose_left_neighbour = lambda: letter_3
    letter_4.choose_right_neighbour = lambda: letter_5
    letter_5.choose_left_neighbour = lambda: letter_4
    letter_5.choose_right_neighbour = lambda: None

    group_0_1 = Group(
        string,
        0,
        1,
        [letter_0, letter_1],
        [],
        predecessor_category,
        right_category,
        None,
    )
    letter_0.group = group_0_1
    letter_1.group = group_0_1
    group_2_3 = Group(
        string,
        2,
        3,
        [letter_2, letter_3],
        [],
        predecessor_category,
        right_category,
        None,
    )
    letter_2.group = group_2_3
    letter_3.group = group_2_3
    group_4_5 = Group(
        string, 4, 5, [letter_4, letter_5], [], successor_category, left_category, None
    )
    letter_4.group = group_4_5
    letter_5.group = group_4_5
    string.letters = [letter_0, letter_1, letter_2, letter_3, letter_4, letter_5]
    string.groups = [group_0_1, group_2_3, group_4_5]
    string.objects = string.letters + string.groups

    assert group_0_1._number_of_local_supporting_groups() == 1
    assert group_2_3._number_of_local_supporting_groups() == 1
    assert group_4_5._number_of_local_supporting_groups() == 0

    # because choosing neighbours is probabilistic,density is 1/2 if the other group is chosen as neighbour and 1/3 if it is not
    group_0_1_density = group_0_1._local_density()
    assert any(
        [
            group_0_1_density == pytest.approx(1 / 3),
            group_0_1_density == pytest.approx(1 / 2),
        ]
    )
    group_2_3_density = group_2_3._local_density()
    assert any(
        [
            group_2_3_density == pytest.approx(1 / 3),
            group_2_3_density == pytest.approx(1 / 2),
        ]
    )
    group_4_5_density = group_4_5._local_density()
    assert group_4_5_density == pytest.approx(0)

    group_0_1_external_strength = group_0_1.calculate_external_strength()
    assert any(
        [
            group_0_1_external_strength == pytest.approx(0.3464102),
            group_0_1_external_strength == pytest.approx(0.4242641),
        ]
    )
    group_2_3_external_strength = group_2_3.calculate_external_strength()
    assert any(
        [
            group_2_3_external_strength == pytest.approx(0.3464102),
            group_2_3_external_strength == pytest.approx(0.4242641),
        ]
    )
    assert group_4_5._local_support() == pytest.approx(0.0)


def test_intra_string_happiness_and_unhappiness():
    string = SimpleNamespace()

    letter_1 = MockLetter(id="l1", string_position=0, string=string)
    letter_2 = MockLetter(id="l2", string_position=1, string=string)
    letter_3 = MockLetter(id="l3", string_position=2, string=string)
    string.letters = [letter_1, letter_2, letter_3]

    group_1 = Group(string, 0, 3, [letter_1, letter_2, letter_3], [], None, None, None)
    string.groups = [group_1]

    # group spans whole string so is maximally happy and not unhappy
    assert group_1.calculate_intra_string_happiness() == 1
    assert group_1.calculate_intra_string_unhappiness() == 0

    # no group, no bonds
    group_2 = Group(string, 0, 2, [letter_1, letter_2], [], None, None, None)
    assert group_2.calculate_intra_string_happiness() == 0
    assert group_2.calculate_intra_string_unhappiness() == 1

    # one bond, leftmost position
    bond = SimpleNamespace(total_strength=1.0)
    group_2.outgoing_bonds.append(bond)
    assert group_2.calculate_intra_string_happiness() == pytest.approx(1 / 3)
    assert group_2.calculate_intra_string_unhappiness() == pytest.approx(2 / 3)
