from copycat.slipnode import Slipnode
from copycat.workspace_structure import WorkspaceStructure


class Description(WorkspaceStructure):
    def __init__(
        self, argument_object: "WorkspaceObject", facet: Slipnode, descriptor: Slipnode
    ):
        self.argument_object = argument_object
        self.facet = facet
        self.descriptor = descriptor

    def __eq__(self, other):
        return (self.facet, self.descriptor) == (other.facet, other.descriptor)

    def calculate_internal_strength(self):
        return self.descriptor.conceptual_depth

    def calculate_external_strength(self):
        return (self._local_support() + self.facet.activation) / 2

    def _local_support(self) -> float:
        """Returns a rough measure of the support for this description from
        other descriptions of the same facet on other objects in the same string.
        Does not take into account distance;
        all qualifying objects in the string give the same amount of support."""
        supporting_objects = [
            o
            for o in self.argument_object.string.objects
            if o != self.argument_object
            and not o.has_recursive_group_member(self.argument_object)
            and not self.argument_object.has_recursive_group_member(o)
            and any(description.facet == self.facet for description in o.descriptions)
        ]
        if len(supporting_objects) == 0:
            return 0.0
        elif len(supporting_objects) == 1:
            return 0.2
        elif len(supporting_objects) == 2:
            return 0.6
        elif len(supporting_objects) == 3:
            return 0.9
        else:
            return 1.0
