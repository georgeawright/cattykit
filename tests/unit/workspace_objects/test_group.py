from types import SimpleNamespace

import pytest

from copycat.workspace_object import WorkspaceObject
from copycat.workspace_objects import Group


def test_has_recursive_group_member():
    string = SimpleNamespace()
    predecessor_category = SimpleNamespace()
    succesor_category = SimpleNamespace()
    left_category = SimpleNamespace()
    right_category = SimpleNamespace()
    object1 = WorkspaceObject(string, 0, 1)
    object2 = WorkspaceObject(string, 2, 3)
    group1 = Group(string, 0, 2, predecessor_category, left_category)
    group2 = Group(string, 2, 3, succesor_category, right_category)
    group3 = Group(string, 1, 2, predecessor_category, left_category)
    group3.objects.append(object2)
    group1.objects.append(object1)
    group1.objects.append(group3)

    assert group1.has_recursive_group_member(group1)
    assert group1.has_recursive_group_member(object1)
    assert group1.has_recursive_group_member(group3)
    assert group1.has_recursive_group_member(object2)

    assert not group1.has_recursive_group_member(group2)
    assert not group2.has_recursive_group_member(group1)
