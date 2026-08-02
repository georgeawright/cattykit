import itertools

from copycat.slipnode import Slipnode
from copycat.workspace_object import WorkspaceObject
from copycat.workspace_structure import WorkspaceStructure


class ExtrinsicDescription(WorkspaceStructure):
    """A description with respect to another object in the workspace.
    For example in "abc -> abd", the 'd' could be "successor of the 'c'"
    d ~ ExtrinsicDescription(successor, letter-category, c)."""

    _next_id = itertools.count(1)

    def __init__(
        self,
        relation: Slipnode,
        description_type_related: Slipnode,
        other_object: WorkspaceObject,
    ):
        self.relation = relation
        self.description_type_related = description_type_related
        self.other_object = other_object
        self.hash_id = next(ExtrinsicDescription._next_id)

    @property
    def conceptual_depth(self):
        return self.relation.conceptual_depth
