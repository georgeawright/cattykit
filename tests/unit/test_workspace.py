from types import SimpleNamespace
from typing import NamedTuple

from copycat import Workspace


class MockObject:
    def __init__(self, id):
        self.id = id
        self.correspondence = None


class MockCorrespondence(NamedTuple):
    from_object: MockObject
    to_object: MockObject


def test_add_and_delete_proposed_correspondence():
    workspace = Workspace(None, None, None, None)
    assert 0 == len(workspace.proposed_correspondences)
    from_object = MockObject(id="a")
    to_object = MockObject(id="b")
    proposed_correspondence = MockCorrespondence(
        from_object=from_object, to_object=to_object
    )
    workspace.add_proposed_correspondence(proposed_correspondence)
    assert 1 == len(workspace.proposed_correspondences)
    workspace.delete_proposed_correspondence(proposed_correspondence)
    assert 0 == len(workspace.proposed_correspondences)


def test_add_get_and_break_correspondence():
    workspace = Workspace(None, None, None, None)
    assert 0 == len(workspace.correspondences)
    from_object = MockObject(id="a")
    to_object = MockObject(id="b")
    correspondence = MockCorrespondence(from_object=from_object, to_object=to_object)
    assert False == workspace.contains_correspondence(correspondence)
    workspace.add_correspondence(correspondence)
    assert 1 == len(workspace.correspondences)
    assert True == workspace.contains_correspondence(correspondence)
    from_object.correspondence = correspondence
    to_object.correspondence = correspondence
    workspace.break_correspondence(correspondence)
    assert 0 == len(workspace.correspondences)


def test_letters_without_replacement():
    a = SimpleNamespace(replacement=None)
    b = SimpleNamespace(replacement=None)
    c = SimpleNamespace(replacement=None)
    letters = [a, b, c]
    initial_string = SimpleNamespace(letters=letters)
    workspace = Workspace(initial_string, None, None, None)
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
    workspace = Workspace(initial_string, None, target_string, None)
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
    workspace = Workspace(initial_string, None, target_string, None)
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
    workspace = Workspace(initial_string, None, target_string, None)
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
