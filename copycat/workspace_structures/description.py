from copycat.slipnode import Slipnode
from copycat.workspace_structure import WorkspaceStructure


class Description(WorkspaceStructure):
    def __init__(
        self, argument_object: WorkspaceStructure, facet: Slipnode, descriptor: Slipnode
    ):
        self.argument_object = argument_object
        self.facet = facet
        self.descriptor = descriptor

    def __eq__(self, other):
        return (self.facet, self.descriptor) == (other.facet, other.descriptor)
