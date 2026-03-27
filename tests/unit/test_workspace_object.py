import pytest

from copycat.workspace_object import WorkspaceObject


def test_has_recursive_group_member_equivalent_to_object_equality():
    o1 = WorkspaceObject(string=None, left_position=None, right_position=None)
    o2 = WorkspaceObject(string=None, left_position=None, right_position=None)
    assert o1.has_recursive_group_member(o1)
    assert o2.has_recursive_group_member(o2)
    assert not o1.has_recursive_group_member(o2)
    assert not o2.has_recursive_group_member(o1)
