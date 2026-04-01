from types import SimpleNamespace

import pytest

from copycat.workspace_object import WorkspaceObject


def test_has_recursive_group_member_equivalent_to_object_equality():
    o1 = WorkspaceObject(string=None, left_position=None, right_position=None)
    o2 = WorkspaceObject(string=None, left_position=None, right_position=None)
    assert o1.has_recursive_group_member(o1)
    assert o2.has_recursive_group_member(o2)
    assert not o1.has_recursive_group_member(o2)
    assert not o2.has_recursive_group_member(o1)


def test_left_and_right_neighbours():
    string = SimpleNamespace()
    l1 = WorkspaceObject(string=string, left_position=0, right_position=0)
    l2 = WorkspaceObject(string=string, left_position=1, right_position=1)
    l3 = WorkspaceObject(string=string, left_position=2, right_position=2)
    l4 = WorkspaceObject(string=string, left_position=3, right_position=3)
    g1 = WorkspaceObject(string=string, left_position=0, right_position=1)
    g2 = WorkspaceObject(string=string, left_position=2, right_position=3)
    string.objects = [l1, l2, l3, l4, g1, g2]
    for o in string.objects:
        o.intra_string_salience = 1

    assert set(l1.left_neighbours) == set()
    assert l1.choose_left_neighbor() is None
    assert set(l2.left_neighbours) == {l1}
    assert l2.choose_left_neighbor() == l1
    assert set(l3.left_neighbours) == {l2, g1}
    assert l3.choose_left_neighbor() in {l2, g1}
    assert set(l4.left_neighbours) == {l3}
    assert l4.choose_left_neighbor() == l3
    assert set(g1.left_neighbours) == set()
    assert g1.choose_left_neighbor() is None
    assert set(g2.left_neighbours) == {l2, g1}
    assert g2.choose_left_neighbor() in {l2, g1}

    assert set(l1.right_neighbours) == {l2}
    assert l1.choose_right_neighbor() == l2
    assert set(l2.right_neighbours) == {l3, g2}
    assert l2.choose_right_neighbor() in {l3, g2}
    assert set(l3.right_neighbours) == {l4}
    assert l3.choose_right_neighbor() == l4
    assert set(l4.right_neighbours) == set()
    assert l4.choose_right_neighbor() is None
    assert set(g1.right_neighbours) == {l3, g2}
    assert g1.choose_right_neighbor() in {l3, g2}
    assert set(g2.right_neighbours) == set()
    assert g2.choose_right_neighbor() is None


@pytest.mark.parametrize(
    "number_of_relevant_descriptions, is_changed_letter, group, expected",
    [
        (0, False, None, 0),
        (0, False, "group", 0),
        (0, True, None, 0),
        (0, True, "group", 0),
        (1, False, None, 1),
        (1, False, "group", 0.666667),
        (1, True, None, 2),
        (1, True, "group", 1.333333),
        (2, False, None, 2),
        (2, False, "group", 1.333333),
        (2, True, None, 4),
        (2, True, "group", 2.666667),
    ],
)
def test_calculate_raw_importance(
    number_of_relevant_descriptions, is_changed_letter, group, expected
):
    object = WorkspaceObject(string=None, left_position=None, right_position=None)
    object.is_changed_letter = is_changed_letter
    object.group = None if group is None else SimpleNamespace(members=[object])
    object.descriptions = [
        SimpleNamespace(is_relevant=lambda: True)
        for _ in range(number_of_relevant_descriptions)
    ]

    assert object.calculate_raw_importance() == pytest.approx(expected)


@pytest.mark.parametrize(
    "correspondence_strength, expected_happiness, expected_unhappiness",
    [
        (None, 0, 1),
        (0, 0, 1),
        (0.5, 0.5, 0.5),
        (1, 1, 0),
    ],
)
def test_inter_string_happiness_and_unhappiness(
    correspondence_strength, expected_happiness, expected_unhappiness
):
    object = WorkspaceObject(string=None, left_position=None, right_position=None)
    object.correspondence = (
        SimpleNamespace(total_strength=correspondence_strength)
        if correspondence_strength is not None
        else None
    )
    assert object.calculate_inter_string_happiness() == pytest.approx(
        expected_happiness
    )
    assert object.calculate_inter_string_unhappiness() == pytest.approx(
        expected_unhappiness
    )


@pytest.mark.parametrize(
    "relative_importance, intra_string_unhappiness, clamped, expected",
    [
        (0, 0, False, 0.0),
        (0, 1, False, 0.8),
        (1, 0, False, 0.2),
        (1, 1, False, 1.0),
        (0.5, 0.5, False, 0.5),
        (0.5, 0.5, True, 1.0),
    ],
)
def test_calculate_intra_string_salience(
    relative_importance, intra_string_unhappiness, clamped, expected
):
    object = WorkspaceObject(string=None, left_position=None, right_position=None)
    object.salience_is_clamped = clamped
    object.relative_importance = relative_importance
    object.intra_string_unhappiness = intra_string_unhappiness
    assert object.calculate_intra_string_salience() == pytest.approx(expected)


@pytest.mark.parametrize(
    "relative_importance, inter_string_unhappiness, clamped, expected",
    [
        (0, 0, False, 0.0),
        (0, 1, False, 0.2),
        (1, 0, False, 0.8),
        (1, 1, False, 1.0),
        (0.5, 0.5, False, 0.5),
        (0.5, 0.5, True, 1.0),
    ],
)
def test_calculate_inter_string_salience(
    relative_importance, inter_string_unhappiness, clamped, expected
):
    object = WorkspaceObject(string=None, left_position=None, right_position=None)
    object.salience_is_clamped = clamped
    object.relative_importance = relative_importance
    object.inter_string_unhappiness = inter_string_unhappiness
    assert object.calculate_inter_string_salience() == pytest.approx(expected)
