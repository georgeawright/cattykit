from __future__ import annotations
import itertools
from typing import Optional

from copycat.workspace_structure import WorkspaceStructure
from copycat.tools import select_item_from_list


class Bond(WorkspaceStructure):
    _next_id = itertools.count(1)

    def __init__(
        self,
        source: "WorkspaceObject",
        target: "WorkspaceObject",
        bond_category: "Slipnode",
        direction_category: Optional["Slipnode"],
        bond_facet: "Slipnode",
        source_descriptor: "Slipnode",
        target_descriptor: "Slipnode",
    ):
        super().__init__()
        self.source = source
        self.target = target
        self.string = source.string
        (self.left_object, self.right_object) = (
            (source, target)
            if source.left_position < target.left_position
            else (target, source)
        )
        self.bond_category = bond_category
        self.direction_category = direction_category
        self.bond_facet = bond_facet
        self.source_descriptor = source_descriptor
        self.target_descriptor = target_descriptor
        self.group = None
        self.hash_id = next(Bond._next_id)

    def __repr__(self):
        labels = [
            l
            for l in [self.bond_facet, self.bond_category, self.direction_category]
            if l is not None
        ]
        return f"{self.source} --{labels}--> {self.target}"

    def __len__(self):
        """Returns the number of letters spanned by the bond.
        2 if the objects are not groups,
        otherwise the sum of the lengths of the groups."""
        return len(self.source) + len(self.target)

    def equates_to(self, other) -> bool:
        return (
            self.source,
            self.target,
            self.bond_category,
            self.bond_facet,
        ) == (
            other.source,
            other.target,
            other.bond_category,
            other.bond_facet,
        )

    @property
    def importance(self) -> float:
        return 1.0 if self.bond_category.name == "sameness" else 0.5

    @property
    def happiness(self) -> float:
        return self.group.total_strength if self.group is not None else 0.0

    @property
    def unhappiness(self) -> float:
        return 1.0 - self.happiness

    @property
    def is_sameness_bond(self) -> bool:
        return self.bond_category.name == "sameness"

    @property
    def salience(self) -> float:
        return (self.importance + self.unhappiness) / 2

    def is_leftmost_in_string(self) -> bool:
        return self.left_object.left_position == 0

    def is_rightmost_in_string(self) -> bool:
        return self.right_object.right_position == len(self.string) - 1

    def choose_neighbour(self, direction: "Slipnode") -> Optional[Bond]:
        if direction.name == "left":
            if self.is_leftmost_in_string():
                return None
            neighbours = [
                self.string.bonds_by_position[obj][self.left_object]
                for obj in self.left_object.left_neighbours
                if self.string.bonds_by_position[obj][self.left_object] is not None
            ]
        elif direction.name == "right":
            if self.is_rightmost_in_string():
                return None
            neighbours = [
                self.string.bonds_by_position[self.right_object][obj]
                for obj in self.right_object.right_neighbours
                if self.string.bonds_by_position[self.right_object][obj] is not None
            ]
        else:
            raise ValueError(f"Invalid direction: {direction}")
        if not neighbours:
            return None
        return select_item_from_list(neighbours, [n.salience for n in neighbours])

    def get_object(self, direction: "Slipnode") -> "WorkspaceObject":
        if direction.name == "left":
            return self.left_object
        elif direction.name == "right":
            return self.right_object
        else:
            raise ValueError(f"Invalid direction: {direction}")

    def get_flipped_version(self) -> Bond:
        return Bond(
            source=self.target,
            target=self.source,
            bond_category=self.bond_category.get_related_node("opposite"),
            direction_category=self.direction_category.get_related_node("opposite")
            if self.direction_category is not None
            else None,
            bond_facet=self.bond_facet,
            source_descriptor=self.target_descriptor,
            target_descriptor=self.source_descriptor,
        )

    def calculate_internal_strength(self) -> float:
        member_compatability_factor = (
            1 if type(self.source) is type(self.target) else 0.7
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
        density = self._local_density()
        adjusted_density = density**0.5
        support_factor = min(1, 0.6 ** (1 / (number_of_local_supporting_bonds**3)))
        return adjusted_density * support_factor

    def _number_of_local_supporting_bonds(self) -> int:
        supporting_bonds = [
            b
            for b in self.source.string.bonds
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
        left_object = self.left_object.choose_left_neighbour()
        while left_object is not None:
            slot_sum += 1
            next_bond = bonds_by_position[left_object][right_object]
            if (
                next_bond is not None
                and next_bond.bond_category == self.bond_category
                and next_bond.bond_facet == self.bond_facet
            ):
                support_sum += 1
            right_object = left_object
            left_object = right_object.choose_left_neighbour()
        # Loop rightwards looking for bonds.
        left_object = self.right_object
        right_object = self.right_object.choose_right_neighbour()
        while right_object is not None:
            slot_sum += 1
            next_bond = bonds_by_position[left_object][right_object]
            if (
                next_bond is not None
                and next_bond.bond_category == self.bond_category
                and next_bond.bond_facet == self.bond_facet
            ):
                support_sum += 1
            left_object = right_object
            right_object = right_object.choose_right_neighbour()
        return 0.0 if slot_sum == 0 else support_sum / slot_sum
