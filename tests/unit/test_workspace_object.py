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

    assert set(l1.left_neighbours) == set()
    assert set(l2.left_neighbours) == {l1}
    assert set(l3.left_neighbours) == {l2, g1}
    assert set(l4.left_neighbours) == {l3}
    assert set(g1.left_neighbours) == set()
    assert set(g2.left_neighbours) == {l2, g1}

    assert set(l1.right_neighbours) == {l2}
    assert set(l2.right_neighbours) == {l3, g2}
    assert set(l3.right_neighbours) == {l4}
    assert set(l4.right_neighbours) == set()
    assert set(g1.right_neighbours) == {l3, g2}
    assert set(g2.right_neighbours) == set()
