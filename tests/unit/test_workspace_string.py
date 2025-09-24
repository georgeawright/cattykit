from types import SimpleNamespace
from typing import NamedTuple

from copycat import WorkspaceString


class MockNode(NamedTuple):
    id: str


class MockBond(NamedTuple):
    from_node: MockNode
    to_node: MockNode
    left_node: MockNode
    right_node: MockNode
    is_sameness_bond: bool


class MockGroup(NamedTuple):
    left_node: MockNode
    right_node: MockNode
    left_position: int
    right_position: int


def test_add_letter():
    workspace_string = WorkspaceString()
    assert 0 == len(workspace_string.letters)
    letter = SimpleNamespace()
    workspace_string.add_letter(letter)
    assert 1 == len(workspace_string.letters)


def test_add_and_delete_proposed_bond():
    workspace_string = WorkspaceString()
    assert 0 == len(workspace_string.proposed_bonds)
    from_node = MockNode(id="a")
    to_node = MockNode(id="b")
    proposed_bond = MockBond(
        from_node=from_node,
        to_node=to_node,
        left_node=from_node,
        right_node=to_node,
        is_sameness_bond=True,
    )
    workspace_string.add_proposed_bond(proposed_bond)
    assert 1 == len(workspace_string.proposed_bonds)
    workspace_string.delete_proposed_bond(proposed_bond)
    assert 0 == len(workspace_string.proposed_bonds)


def test_add_get_and_delete_sameness_bond():
    workspace_string = WorkspaceString()
    assert 0 == len(workspace_string.bonds)
    from_node = MockNode(id="a")
    to_node = MockNode(id="b")
    bond = MockBond(
        from_node=from_node,
        to_node=to_node,
        left_node=from_node,
        right_node=to_node,
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
    from_node = MockNode(id="a")
    to_node = MockNode(id="b")
    bond = MockBond(
        from_node=from_node,
        to_node=to_node,
        left_node=from_node,
        right_node=to_node,
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
    left_node = MockNode(id="a")
    right_node = MockNode(id="b")
    proposed_group = MockGroup(
        left_node=left_node, right_node=right_node, left_position=1, right_position=2
    )
    workspace_string.add_proposed_group(proposed_group)
    assert 1 == len(workspace_string.proposed_groups)
    workspace_string.delete_proposed_group(proposed_group)
    assert 0 == len(workspace_string.proposed_groups)


def test_add_get_and_delete_group():
    workspace_string = WorkspaceString()
    assert 0 == len(workspace_string.proposed_groups)
    left_node = MockNode(id="a")
    right_node = MockNode(id="b")
    group = MockGroup(
        left_node=left_node, right_node=right_node, left_position=1, right_position=2
    )
    assert False == workspace_string.get_group_if_present(group)
    workspace_string.add_group(group)
    assert 1 == len(workspace_string.groups)
    assert group == workspace_string.get_group_if_present(group)
    workspace_string.delete_group(group)
    assert 0 == len(workspace_string.groups)


def test_choose_from_leftmost_objects():
    workspace_string = WorkspaceString()
    a = SimpleNamespace(id="a", is_leftmost=True, relative_importance=0.1)
    b = SimpleNamespace(id="b", is_leftmost=False, relative_importance=0.1)
    c = SimpleNamespace(id="c", is_leftmost=False, relative_importance=0.1)
    abc = SimpleNamespace(
        left_node=a,
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
