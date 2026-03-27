from copycat.workspace_structure import WorkspaceStructure


class Rule(WorkspaceStructure):
    def __init__(
        self,
        object_category_1,
        descriptor_1_facet,
        descriptor_1,
        object_category_2,
        descriptor_2,
        replaced_description_type,
        relation,
        structure_category,
    ):
        self.object_category_1 = object_category_1
        self.descriptor_1_facet = descriptor_1_facet
        self.descriptor_1 = descriptor_1
        self.object_category_2 = object_category_2
        self.descriptor_2 = descriptor_2
        self.replaced_description_type = replaced_description_type
        self.relation = relation
        self.structure_category = structure_category

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
