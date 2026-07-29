from typing import Optional

from copycat.slipnode import Slipnode
from copycat.workspace_structure import WorkspaceStructure


class Rule(WorkspaceStructure):
    def __init__(
        self,
        object_category_1: Optional[Slipnode] = None,
        descriptor_1_facet: Optional[Slipnode] = None,
        descriptor_1: Optional[Slipnode] = None,
        object_category_2: Optional[Slipnode] = None,
        descriptor_2: Optional[Slipnode] = None,
        replaced_description_type: Optional[Slipnode] = None,
        relation: Optional[Slipnode] = None,
    ):
        self.object_category_1 = object_category_1
        self.descriptor_1_facet = descriptor_1_facet
        self.descriptor_1 = descriptor_1
        self.object_category_2 = object_category_2
        self.descriptor_2 = descriptor_2
        self.replaced_description_type = replaced_description_type
        self.relation = relation

    def __eq__(self, other):
        return (
            self.object_category_1,
            self.descriptor_1_facet,
            self.descriptor_1,
            self.object_category_2,
            self.descriptor_2,
            self.replaced_description_type,
            self.relation,
        ) == (
            other.object_category_1,
            other.descriptor_1_facet,
            other.descriptor_1,
            other.object_category_2,
            other.descriptor_2,
            other.replaced_description_type,
            other.relation,
        )

    def expresses_relation(self) -> bool:
        return self.relation is not None

    def specifies_change(self) -> bool:
        return self.descriptor_1 is not None
