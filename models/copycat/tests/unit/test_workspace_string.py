from unittest.mock import Mock
from types import SimpleNamespace
from typing import NamedTuple

import pytest

from copycat import WorkspaceString


class MockObject:
    def __init__(self, id):
        self.id = id
        self.outgoing_bonds = []
        self.incoming_bonds = []


class MockBond:
    def __init__(self, source, target, left_object, right_object, is_sameness_bond):
        self.source = source
        self.target = target
        self.left_object = left_object
        self.right_object = right_object
        self.bond_category = Mock(name="sameness" if is_sameness_bond else "successor")


class MockGroup(NamedTuple):
    left_object: MockObject
    right_object: MockObject
    left_position: int
    right_position: int


@pytest.mark.parametrize(
    "raw_importances, expected_relative_importances",
    [
        ([0, 0, 0], [0, 0, 0]),
        ([1, 0, 0], [1, 0, 0]),
        ([0, 1, 0], [0, 1, 0]),
        ([0, 0, 1], [0, 0, 1]),
        ([1, 1, 0], [0.5, 0.5, 0]),
        ([1, 0, 1], [0.5, 0, 0.5]),
        ([0, 1, 1], [0, 0.5, 0.5]),
        ([1, 1, 1], [1 / 3, 1 / 3, 1 / 3]),
    ],
)
def test_update_relative_importances(raw_importances, expected_relative_importances):
    workspace_string = WorkspaceString()
    for i, raw_importance in enumerate(raw_importances):
        obj = SimpleNamespace(raw_importance=raw_importance, relative_importance=None)
        workspace_string.letters.append(obj)
    workspace_string.update_relative_importances()
    for obj, expected in zip(workspace_string.letters, expected_relative_importances):
        assert obj.relative_importance == pytest.approx(expected)


@pytest.mark.parametrize(
    "intra_string_unhappinesses, expected",
    [
        ([], 0),
        ([0, 0, 0], 0),
        ([1, 0, 0], 1 / 3),
        ([1, 0, 1], 2 / 3),
        ([0.5, 0, 1], 0.5),
    ],
)
def test_update_intra_string_unhappiness(intra_string_unhappinesses, expected):
    workspace_string = WorkspaceString()
    for intra_string_unhappiness in intra_string_unhappinesses:
        obj = SimpleNamespace(intra_string_unhappiness=intra_string_unhappiness)
        workspace_string.letters.append(obj)
    workspace_string.update_intra_string_unhappiness()
    assert workspace_string.intra_string_unhappiness == pytest.approx(expected)


def test_add_letter():
    workspace_string = WorkspaceString()
    assert 0 == len(workspace_string.letters)
    letter = SimpleNamespace()
    workspace_string.add_letter(letter)
    assert 1 == len(workspace_string.letters)


def test_add_and_delete_proposed_bond():
    workspace_string = WorkspaceString()
    assert 0 == len(workspace_string.proposed_bonds)
    source = MockObject(id="a")
    target = MockObject(id="b")
    proposed_bond = MockBond(
        source=source,
        target=target,
        left_object=source,
        right_object=target,
        is_sameness_bond=True,
    )
    workspace_string.add_proposed_bond(proposed_bond)
    assert 1 == len(workspace_string.proposed_bonds)
    workspace_string.delete_proposed_bond(proposed_bond)
    assert 0 == len(workspace_string.proposed_bonds)


def test_add_get_and_delete_sameness_bond():
    workspace_string = WorkspaceString()
    assert 0 == len(workspace_string.bonds)
    source = MockObject(id="a")
    target = MockObject(id="b")
    bond = MockBond(
        source=source,
        target=target,
        left_object=source,
        right_object=target,
        is_sameness_bond=True,
    )
    assert False == workspace_string.get_bond_if_present(bond)
    workspace_string.add_bond(bond)
    assert 1 == len(workspace_string.bonds)
    assert bond == workspace_string.get_bond_if_present(bond)
    workspace_string.delete_bond(bond)
    assert 0 == len(workspace_string.bonds)


def test_add_and_delete_non_sameness_bond():
    workspace_string = WorkspaceString()
    assert 0 == len(workspace_string.bonds)
    source = MockObject(id="a")
    target = MockObject(id="b")
    bond = MockBond(
        source=source,
        target=target,
        left_object=source,
        right_object=target,
        is_sameness_bond=False,
    )
    assert False == workspace_string.get_bond_if_present(bond)
    workspace_string.add_bond(bond)
    assert 1 == len(workspace_string.bonds)
    assert bond == workspace_string.get_bond_if_present(bond)
    workspace_string.delete_bond(bond)
    assert 0 == len(workspace_string.bonds)


def test_add_and_delete_proposed_group():
    workspace_string = WorkspaceString()
    assert 0 == len(workspace_string.proposed_groups)
    left_object = MockObject(id="a")
    right_object = MockObject(id="b")
    proposed_group = MockGroup(
        left_object=left_object,
        right_object=right_object,
        left_position=1,
        right_position=2,
    )
    workspace_string.add_proposed_group(proposed_group)
    assert 1 == len(workspace_string.proposed_groups)
    workspace_string.delete_proposed_group(proposed_group)
    assert 0 == len(workspace_string.proposed_groups)


def test_add_get_and_delete_group():
    workspace_string = WorkspaceString()
    assert 0 == len(workspace_string.groups)
    left_object = MockObject(id="a")
    right_object = MockObject(id="b")
    group = MockGroup(
        left_object=left_object,
        right_object=right_object,
        left_position=1,
        right_position=2,
    )
    assert False == workspace_string.get_group_if_present(group)
    workspace_string.add_group(group)
    assert 1 == len(workspace_string.groups)
    assert group == workspace_string.get_group_if_present(group)
    workspace_string.delete_group(group)
    assert 0 == len(workspace_string.groups)


def test_choose_from_leftmost_objects():
    workspace_string = WorkspaceString()
    a = Mock(id="a", is_leftmost=True, relative_importance=0.1)
    b = Mock(id="b", is_leftmost=False, relative_importance=0.1)
    c = Mock(id="c", is_leftmost=False, relative_importance=0.1)
    abc = Mock(
        left_object=a,
        left_position=0,
        right_position=2,
        is_leftmost=True,
        relative_importance=0.1,
    )
    workspace_string.add_letter(a)
    workspace_string.add_letter(b)
    workspace_string.add_letter(c)
    workspace_string.add_group(abc)
    assert workspace_string.choose_from_leftmost_objects() in (a, abc)


def test_get_local_bond_category_relevance():
    workspace_string = WorkspaceString()
    category = SimpleNamespace(name="category")
    assert workspace_string.get_local_bond_category_relevance(category) == 0.0

    bond = SimpleNamespace(bond_category=category)
    object_1 = SimpleNamespace(right_bond=bond, spans_whole_string=False)
    object_2 = SimpleNamespace(right_bond=None, spans_whole_string=False)
    workspace_string.add_letter(object_1)
    workspace_string.add_letter(object_2)
    assert workspace_string.get_local_bond_category_relevance(category) == 1.0

    object_3 = SimpleNamespace(right_bond=None, spans_whole_string=False)
    workspace_string.add_letter(object_3)
    assert workspace_string.get_local_bond_category_relevance(category) == 0.5


def test_get_local_direction_category_relevance():
    workspace_string = WorkspaceString()
    category = SimpleNamespace(name="category")
    assert workspace_string.get_local_direction_category_relevance(category) == 0.0

    bond = SimpleNamespace(direction_category=category)
    object_1 = SimpleNamespace(right_bond=bond, spans_whole_string=False)
    object_2 = SimpleNamespace(right_bond=None, spans_whole_string=False)
    workspace_string.add_letter(object_1)
    workspace_string.add_letter(object_2)
    assert workspace_string.get_local_direction_category_relevance(category) == 1.0

    object_3 = SimpleNamespace(right_bond=None, spans_whole_string=False)
    workspace_string.add_letter(object_3)
    assert workspace_string.get_local_direction_category_relevance(category) == 0.5
