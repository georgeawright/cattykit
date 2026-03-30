from types import SimpleNamespace

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


def test_has_recursive_group_member():
    string = SimpleNamespace()
    predecessor_category = SimpleNamespace()
    succesor_category = SimpleNamespace()
    left_category = SimpleNamespace()
    right_category = SimpleNamespace()
    object1 = WorkspaceObject(string, 0, 1)
    object2 = WorkspaceObject(string, 2, 3)
    group3 = Group(string, 1, 2, [object2], predecessor_category, left_category, None)
    group2 = Group(string, 2, 3, [object2], succesor_category, right_category, None)
    group1 = Group(
        string, 0, 2, [object1, group3], predecessor_category, left_category, None
    )

    assert group1.has_recursive_group_member(group1)
    assert group1.has_recursive_group_member(object1)
    assert group1.has_recursive_group_member(group3)
    assert group1.has_recursive_group_member(object2)

    assert not group1.has_recursive_group_member(group2)
    assert not group2.has_recursive_group_member(group1)


@pytest.mark.parametrize(
    "group_category_name, bond_category_degree_of_association, length, expected",
    [
        ("letter_category", 1.0, 4, 1.0),
        ("length", 1.0, 4, 0.697208),
        ("letter_category", 0.5, 4, 0.697208),
        ("letter_category", 1.0, 1, 1.0),
        ("length", 1.0, 1, 0.278141),
    ],
)
def test_calculate_internal_strength(
    group_category_name, bond_category_degree_of_association, length, expected
):
    group_category = SimpleNamespace(name=group_category_name)
    related_node = SimpleNamespace(
        degree_of_association=bond_category_degree_of_association
    )
    group_category.get_related_node = (
        lambda x: related_node if x == "bond_category" else None
    )
    letters = [SimpleNamespace() for _ in range(length)]
    for letter in letters:
        letter.letters = [letter]
    group = Group(None, 0, 1, letters, group_category, None, None)

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
    group = Group(string, 0, 1, letters, None, None, None)

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
    for i in range(string_length):
        string.letters.append(MockLetter(id=f"l{i}", string_position=i, string=string))
    for i, letter in enumerate(string.letters):
        letter.letters = [letter]
        letter.choose_left_neighbor = lambda: string.letters[i - 1] if i > 0 else None
        letter.choose_right_neighbor = (
            lambda: string.letters[i + 1] if i < string_length - 1 else None
        )

    group_0_1 = Group(
        string,
        0,
        1,
        [string.letters[0], string.letters[1]],
        letter_category,
        predecessor_category,
        right_category,
    )
    string.letters[0].group = group_0_1
    string.letters[1].group = group_0_1
    group_2_3 = Group(
        string,
        2,
        3,
        [string.letters[2], string.letters[3]],
        letter_category,
        predecessor_category,
        right_category,
    )
    string.letters[2].group = group_2_3
    string.letters[3].group = group_2_3
    group_4_5 = Group(
        string,
        4,
        5,
        [string.letters[4], string.letters[5]],
        letter_category,
        successor_category,
        left_category,
    )
    string.letters[4].group = group_4_5
    string.letters[5].group = group_4_5
    string.groups = [group_0_1, group_2_3, group_4_5]
    string.objects = string.letters + string.groups

    assert group_0_1._number_of_local_supporting_groups() == 1
    assert group_2_3._number_of_local_supporting_groups() == 1
    assert group_4_5._number_of_local_supporting_groups() == 0

    assert group_0_1._local_density() == pytest.approx(0.5)
    assert group_2_3._local_density() == pytest.approx(0.5)
    assert group_4_5._local_density() == pytest.approx(0)

    assert group_0_1.calculate_external_strength() == pytest.approx(0.4242641)
    assert group_2_3.calculate_external_strength() == pytest.approx(0.4242641)
    assert group_4_5._local_support() == pytest.approx(0.0)
