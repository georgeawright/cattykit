from copycat.workspace_structure import WorkspaceStructure


class Correspondence(WorkspaceStructure):
    def __init__(from_object, to_object, concept_mappings):
        self.from_object = from_object
        self.to_object = to_object
        self.concept_mappings = concept_mappings

    def __len__(self):
        """Returns the number of letters spanned by the objects."""
        return len(self.from_object) + len(self.to_object)
