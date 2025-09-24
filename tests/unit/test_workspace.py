from types import SimpleNamespace
from typing import NamedTuple

from copycat import Workspace


class MockNode(NamedTuple):
    id: str


class MockCorrespondence(NamedTuple):
    from_node: MockNode
    to_node: MockNode


def test_add_and_delete_proposed_correspondence():
    workspace = Workspace(None, None)
    assert 0 == len(workspace.proposed_correspondences)
    from_node = MockNode(id="a")
    to_node = MockNode(id="b")
    proposed_correspondence = MockCorrespondence(from_node=from_node, to_node=to_node)
    workspace.add_proposed_correspondence(proposed_correspondence)
    assert 1 == len(workspace.proposed_correspondences)
    workspace.delete_proposed_correspondence(proposed_correspondence)
    assert 0 == len(workspace.proposed_correspondences)


def test_add_get_and_delete_group():
    workspace = Workspace(None, None)
    assert 0 == len(workspace.correspondences)
    from_node = MockNode(id="a")
    to_node = MockNode(id="b")
    correspondence = MockCorrespondence(from_node=from_node, to_node=to_node)
    assert False == workspace.contains_correspondence(correspondence)
    workspace.add_correspondence(correspondence)
    assert 1 == len(workspace.correspondences)
    assert True == workspace.contains_correspondence(correspondence)
    workspace.delete_correspondence(correspondence)
    assert 0 == len(workspace.correspondences)


def test_letters_without_replacement():
    a = SimpleNamespace(replacement=None)
    b = SimpleNamespace(replacement=None)
    c = SimpleNamespace(replacement=None)
    letters = [a, b, c]
    initial_string = SimpleNamespace(letters=letters)
    workspace = Workspace(initial_string, None)
    assert 3 == len(workspace.letters_without_replacement)
    a.replacement = SimpleNamespace()
    assert 2 == len(workspace.letters_without_replacement)
    b.replacement = SimpleNamespace()
    assert 1 == len(workspace.letters_without_replacement)
    c.replacement = SimpleNamespace()
    assert 0 == len(workspace.letters_without_replacement)


def test_ungrouped_objects():
    a = SimpleNamespace(spans_whole_string=False, group=None)
    b = SimpleNamespace(spans_whole_string=False, group=None)
    c = SimpleNamespace(spans_whole_string=False, group=None)
    objects = [a, b, c]
    initial_string = SimpleNamespace(objects=objects)
    target_string = SimpleNamespace(objects=[])
    workspace = Workspace(initial_string, target_string)
    assert 3 == len(workspace.ungrouped_objects)
    ab = SimpleNamespace(spans_whole_string=False, group=None)
    a.group = ab
    b.group = ab
    objects.append(ab)
    assert 2 == len(workspace.ungrouped_objects)
    abc = SimpleNamespace(spans_whole_string=True, group=None)
    a.group = abc
    b.group = abc
    c.group = abc
    objects.remove(ab)
    objects.append(abc)
    assert 0 == len(workspace.ungrouped_objects)


def test_unbonded_objects():
    a = SimpleNamespace(
        spans_whole_string=False, group=None, bonds=[], is_at_edge_of_string=True
    )
    b = SimpleNamespace(
        spans_whole_string=False, group=None, bonds=[], is_at_edge_of_string=False
    )
    c = SimpleNamespace(
        spans_whole_string=False, group=None, bonds=[], is_at_edge_of_string=True
    )
    objects = [a, b, c]
    initial_string = SimpleNamespace(objects=objects)
    target_string = SimpleNamespace(objects=[])
    workspace = Workspace(initial_string, target_string)
    assert 3 == len(workspace.unbonded_objects)
    a_to_b = SimpleNamespace()
    a.bonds.append(a_to_b)
    b.bonds.append(a_to_b)
    assert 2 == len(workspace.unbonded_objects)
    b_to_c = SimpleNamespace()
    b.bonds.append(b_to_c)
    c.bonds.append(b_to_c)
    assert 0 == len(workspace.unbonded_objects)


def test_uncorresponded_objects():
    a = SimpleNamespace(correspondence=None)
    b = SimpleNamespace(correspondence=None)
    c = SimpleNamespace(correspondence=None)
    initial_string = SimpleNamespace(objects=[a, b, c])
    x = SimpleNamespace(correspondence=None)
    y = SimpleNamespace(correspondence=None)
    z = SimpleNamespace(correspondence=None)
    target_string = SimpleNamespace(objects=[x, y, z])
    workspace = Workspace(initial_string, target_string)
    assert 6 == len(workspace.uncorresponded_objects)
    a_to_z = SimpleNamespace()
    a.correspondence = a_to_z
    z.correspondence = a_to_z
    assert 4 == len(workspace.uncorresponded_objects)
    b_to_y = SimpleNamespace()
    b.correspondence = b_to_y
    y.correspondence = b_to_y
    assert 2 == len(workspace.uncorresponded_objects)
    c_to_x = SimpleNamespace()
    c.correspondence = c_to_x
    x.correspondence = c_to_x
    assert 0 == len(workspace.uncorresponded_objects)
