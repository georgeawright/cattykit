from types import SimpleNamespace
from typing import NamedTuple

from copycat import Workspace


class MockString:
    def __init__(self, objects):
        self.objects = objects
        self.called_delete_bond = 0
        self.called_delete_group = 0
        self.called_delete_proposed_bond = 0

    def delete_bond(self, bond):
        self.called_delete_bond += 1

    def delete_group(self, group):
        self.called_delete_group += 1

    def delete_proposed_bond(self, proposed_bond):
        self.called_delete_proposed_bond += 1


class MockObject:
    def __init__(self, string=None):
        self.string = string
        self.correspondence = None
        self.outgoing_bonds = []
        self.incoming_bonds = []


class MockCorrespondence(NamedTuple):
    source: MockObject
    target: MockObject

    def equates_to(self, other):
        return self.source == other.source and self.target == other.target


def test_add_and_delete_proposed_correspondence():
    workspace = Workspace(None, None, None, None)
    assert 0 == len(workspace.proposed_correspondences)
    source = MockObject()
    target = MockObject()
    proposed_correspondence = MockCorrespondence(source=source, target=target)
    workspace.add_proposed_correspondence(proposed_correspondence)
    assert 1 == len(workspace.proposed_correspondences)
    workspace.delete_proposed_correspondence(proposed_correspondence)
    assert 0 == len(workspace.proposed_correspondences)


def test_add_get_and_break_correspondence():
    workspace = Workspace(None, None, None, None)
    assert 0 == len(workspace.correspondences)
    source = MockObject()
    target = MockObject()
    correspondence = MockCorrespondence(source=source, target=target)
    assert False == workspace.contains_correspondence(correspondence)
    workspace.add_correspondence(correspondence)
    assert 1 == len(workspace.correspondences)
    assert True == workspace.contains_correspondence(correspondence)
    source.correspondence = correspondence
    target.correspondence = correspondence
    workspace.break_correspondence(correspondence)
    assert 0 == len(workspace.correspondences)


def test_break_bond():
    workspace = Workspace(None, None, None, None)
    string = MockString(objects=[])
    source = MockObject(string=string)
    target = MockObject(string=string)
    bond = SimpleNamespace(
        source=source,
        target=target,
        is_sameness_bond=False,
        left_object=source,
        right_object=target,
    )
    source.outgoing_bonds.append(bond)
    target.incoming_bonds.append(bond)
    workspace.break_bond(bond)
    assert string.called_delete_bond == 1


def test_break_group():
    workspace = Workspace(None, None, None, None)
    string = MockString(objects=[])
    left_object = MockObject(string=string)
    right_object = MockObject(string=string)
    group = SimpleNamespace(
        group=None,
        string=string,
        left_position=0,
        right_position=1,
        objects=[SimpleNamespace()],
        bonds=[SimpleNamespace()],
        correspondence=None,
    )
    bond = SimpleNamespace(
        source=left_object,
        target=group,
        is_sameness_bond=False,
        left_object=left_object,
        right_object=group,
    )
    group.incoming_bonds = [bond]
    group.outgoing_bonds = []
    group.outgoing_and_incoming_bonds = [bond]
    left_object.outgoing_bonds.append(bond)
    proposed_bond = SimpleNamespace(
        source=group,
        target=right_object,
        is_sameness_bond=False,
        left_object=group,
        right_object=None,
    )
    string.proposed_bonds = [proposed_bond]
    workspace.break_group(group)
    assert string.called_delete_group == 1
    assert string.called_delete_proposed_bond == 1


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
    a = SimpleNamespace(spans_whole_string=lambda: False, group=None)
    b = SimpleNamespace(spans_whole_string=lambda: False, group=None)
    c = SimpleNamespace(spans_whole_string=lambda: False, group=None)
    objects = [a, b, c]
    initial_string = SimpleNamespace(objects=objects)
    target_string = SimpleNamespace(objects=[])
    workspace = Workspace(initial_string, None, target_string, None)
    assert 3 == len(workspace.ungrouped_objects)
    ab = SimpleNamespace(spans_whole_string=lambda: False, group=None)
    a.group = ab
    b.group = ab
    objects.append(ab)
    assert 2 == len(workspace.ungrouped_objects)
    abc = SimpleNamespace(spans_whole_string=lambda: True, group=None)
    a.group = abc
    b.group = abc
    c.group = abc
    objects.remove(ab)
    objects.append(abc)
    assert 0 == len(workspace.ungrouped_objects)


def test_unbonded_objects():
    a = SimpleNamespace(
        spans_whole_string=lambda: False,
        group=None,
        bonds=[],
        is_at_edge_of_string=lambda: True,
    )
    b = SimpleNamespace(
        spans_whole_string=lambda: False,
        group=None,
        bonds=[],
        is_at_edge_of_string=lambda: False,
    )
    c = SimpleNamespace(
        spans_whole_string=lambda: False,
        group=None,
        bonds=[],
        is_at_edge_of_string=lambda: True,
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
