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
