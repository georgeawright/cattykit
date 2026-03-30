from copycat.workspace_structure import WorkspaceStructure


class Bond(WorkspaceStructure):
    def __init__(
        self,
        from_object,
        to_object,
        bond_category,
        bond_facet,
        from_object_descriptor,
        to_object_descriptor,
    ):
        self.from_object = from_object
        self.to_object = to_object
        self.bond_category = bond_category
        self.bond_facet = bond_facet
        self.from_object_descriptor = from_object_descriptor
        self.to_object_descriptor = to_object_descriptor

    def __len__(self):
        """Returns the number of letters spanned by the bond.
        2 if the objects are not groups,
        otherwise the sum of the lengths of the groups."""
        return len(self.from_object) + len(self.to_object)

    def __eq__(self, other):
        return (
            self.from_object,
            self.to_object,
            self.bond_category,
            self.direction_category,
        ) == (
            other.from_object,
            other.to_object,
            other.bond_category,
            other.direction_category,
        )

    def is_leftmost_in_string(self) -> bool:
        pass

    def is_rightmost_in_string(self) -> bool:
        pass

    def calculate_internal_strength(self) -> float:
        member_compatability_factor = (
            1 if type(self.from_object) is type(self.to_object) else 0.7
        )
        bond_facet_factor = 1 if self.bond_facet.name == "letter_category" else 0.7
        return min(
            1,
            member_compatability_factor
            * bond_facet_factor
            * self.bond_category.bond_degree_of_association,
        )

    def calculate_external_strength(self) -> float:
        pass
