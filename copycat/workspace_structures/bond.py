import random
from typing import Optional

from copycat.workspace_structure import WorkspaceStructure


class Bond(WorkspaceStructure):
    def __init__(
        self,
        from_object: "WorkspaceObject",
        to_object: "WorkspaceObject",
        bond_category: "Slipnode",
        direction_category: Optional["Slipnode"],
        bond_facet: "Slipnode",
        from_object_descriptor: "Slipnode",
        to_object_descriptor: "Slipnode",
    ):
        self.from_object = from_object
        self.to_object = to_object
        self.string = from_object.string
        (self.left_object, self.right_object) = (
            (from_object, to_object)
            if from_object.left_position < to_object.left_position
            else (to_object, from_object)
        )
        self.bond_category = bond_category
        self.direction_category = direction_category
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
            self.bond_facet,
        ) == (
            other.from_object,
            other.to_object,
            other.bond_category,
            other.bond_facet,
        )

    def is_leftmost_in_string(self) -> bool:
        return self.left_object.left_position == 0

    def is_rightmost_in_string(self) -> bool:
        return self.right_object.right_position == len(self.string) - 1

    def choose_neighbour(self, direction: "Slipnode") -> Optional["Bond"]:
        if direction.name == "left":
            if self.is_leftmost_in_string():
                return None
            neighbours = [
                self.string.bonds_by_position[obj.id][self.left_object.id]
                for obj in self.left_object.left_neighbours
                if self.string.bonds_by_position[obj.id][self.left_object.id]
                is not None
            ]
        elif direction.name == "right":
            if self.is_rightmost_in_string():
                return None
            neighbours = [
                self.string.bonds_by_position[self.right_object.id][obj.id]
                for obj in self.right_object.right_neighbours
                if self.string.bonds_by_position[self.right_object.id][obj.id]
                is not None
            ]
        else:
            raise ValueError(f"Invalid direction: {direction}")
        if not neighbours:
            return None
        return random.choices(neighbours, weights=[n.salience for n in neighbours])[0]

    def get_object(self, direction: "Slipnode") -> "WorkspaceObject":
        if direction.name == "left":
            return self.left_object
        elif direction.name == "right":
            return self.right_object
        else:
            raise ValueError(f"Invalid direction: {direction}")

    def get_flipped_version(self) -> "Bond":
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
        return self._local_support()

    def _local_support(self) -> float:
        """Measures the support of a bond according to
        presence of bonds of the same type in the string.
        Doesn't take distance into account."""
        number_of_local_supporting_bonds = self._number_of_local_supporting_bonds()
        if number_of_local_supporting_bonds == 0:
            return 0.0
        else:
            density = self._local_density()
            adjusted_density = density**0.5
            support_factor = min(
                1, 0.6 ** (1 / (number_of_local_supporting_bonds**3))
            )
            return adjusted_density * support_factor

    def _number_of_local_supporting_bonds(self) -> int:
        supporting_bonds = [
            b
            for b in self.from_object.string.bonds
            if b != self
            and b.left_object.distance_from(self.left_object) != 0
            and b.right_object.distance_from(self.right_object) != 0
            and b.bond_category == self.bond_category
            and b.bond_facet == self.bond_facet
        ]
        return len(supporting_bonds)

    def _local_density(self) -> float:
        """Rough measure of the density in the string of bonds
        of the same bond-category and direction-category as this bond.
        Probabilistic as it depends on which neighbors are chosen."""
        slot_sum = 0
        support_sum = 0
        bonds_by_position = self.left_object.string.bonds_by_position
        # Loop leftwards looking for bonds.
        right_object = self.left_object
        left_object = self.left_object.choose_left_neighbor()
        while left_object is not None:
            slot_sum += 1
            next_bond = bonds_by_position[left_object.id][right_object.id]
            if (
                next_bond is not None
                and next_bond.bond_category == self.bond_category
                and next_bond.bond_facet == self.bond_facet
            ):
                support_sum += 1
            right_object = left_object
            left_object = right_object.choose_left_neighbor()
        # Loop rightwards looking for bonds.
        left_object = self.right_object
        right_object = self.right_object.choose_right_neighbor()
        while right_object is not None:
            slot_sum += 1
            next_bond = bonds_by_position[left_object.id][right_object.id]
            if (
                next_bond is not None
                and next_bond.bond_category == self.bond_category
                and next_bond.bond_facet == self.bond_facet
            ):
                support_sum += 1
            left_object = right_object
            right_object = right_object.choose_right_neighbor()
        return 0.0 if slot_sum == 0 else support_sum / slot_sum
