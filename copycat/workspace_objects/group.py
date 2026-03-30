from __future__ import annotations
from typing import List

from copycat.slipnet import Slipnode
from copycat.workspace_object import WorkspaceObject


class Group(WorkspaceObject):
    def __init__(
        self,
        string: "WorkspaceString",
        left_position: int,
        right_position: int,
        objects: List[WorkspaceObject],
        group_category: Slipnode,
        direction_category: Slipnode,
        bond_facet: Slipnode,
    ):
        super().__init__(string, left_position, right_position)
        self.objects = objects
        self.group_category = group_category
        self.direction_category = direction_category
        self.bond_facet = bond_facet
        self.bond_descriptions: List = []

    def __len__(self):
        return len(self.letters)

    def __eq__(self, other):
        if not isinstance(other, Group):
            return False
        return (
            self.left_position,
            self.right_position,
            self.group_category,
            self.direction_category,
        ) == (
            other.left_position,
            other.right_position,
            other.group_category,
            other.direction_category,
        )

    def __contains__(self):
        pass

    @property
    def letters(self):
        letters = []
        for o in self.objects:
            letters += o.letters
        return letters

    @property
    def leftmost_letter(self):
        return [
            letter
            for letter in self.letters
            if letter.left_position == self.left_position
        ][0]

    @property
    def rightmost_letter(self):
        return [
            letter
            for letter in self.letters
            if letter.right_position == self.right_position
        ][0]

    def has_recursive_group_member(self, other_object) -> bool:
        if self == other_object:
            return True
        for o in self.objects:
            if o.has_recursive_group_member(other_object):
                return True
        return False

    def is_leftmost_in_string(self) -> bool:
        # TODO
        pass

    def is_rightmost_in_string(self) -> bool:
        # TODO
        pass

    def spans_whole_string(self) -> bool:
        return len(self) == len(self.string.letters)

    def has_sub_group(self, other_group: Group) -> bool:
        return (
            self.left_position <= other_group.left_position
            and self.right_position >= other_group.right_position
        )

    def overlaps_with(self, other_group: Group) -> bool:
        return not (
            self.right_position <= other_group.left_position
            or self.left_position >= other_group.right_position
        )

    def get_left_neighbour(self):
        # TODO
        pass

    def get_right_neighbour(self):
        # TODO
        pass

    def calculate_internal_strength(self) -> float:
        """The description-type upon which the bonds making up
        this group are based (i.e., letter-category or
        length)."""
        bond_facet_factor = 1 if self.group_category.name == "letter_category" else 0.5
        bond_component = (
            self.group_category.get_related_node("bond_category").degree_of_association
            * bond_facet_factor
        )
        length_component = {1: 0.05, 2: 0.2, 3: 0.6}.get(len(self), 0.9)
        bond_component_weight = bond_component**0.98
        length_component_weight = 1 - bond_component_weight
        return (
            bond_component * bond_component_weight
            + length_component * length_component_weight
        )

    def calculate_external_strength(self) -> float:
        return 1 if self.spans_whole_string() else self._local_support()

    def _local_support(self) -> float:
        number_of_local_supporting_groups = self._number_of_local_supporting_groups()
        if number_of_local_supporting_groups == 0:
            return 0.0
        else:
            density = self._local_density()
            adjusted_density = density**0.5
            number_factor = min(
                1, 0.6 ** (1 / (number_of_local_supporting_groups**3))
            )
            return adjusted_density * number_factor

    def _number_of_local_supporting_groups(self) -> int:
        supporting_groups = [
            g
            for g in self.string.groups
            if g != self
            and not self.has_sub_group(g)
            and not g.has_sub_group(self)
            and not self.overlaps_with(g)
            and g.group_category == self.group_category
            and g.direction_category == self.direction_category
        ]
        return len(supporting_groups)

    def _local_density(self) -> float:
        """Rough measure of the density in the string of groups
        of the same group-category and direction-category as this group.
        Probabilistic as it depends on which neighbors are chosen."""
        slot_sum = 0
        support_sum = 0
        # Loop leftwards looking for groups.
        right_object = self.leftmost_letter
        left_object = right_object.choose_left_neighbor()
        # might need to be fixed
        left_object = (
            left_object
            if left_object is None or isinstance(left_object, Group)
            else left_object.group
        )
        # TODO: fix left neighbour choice
        while left_object is not None:
            slot_sum += 1
            next_group = left_object if isinstance(left_object, Group) else None
            if (
                next_group is not None
                and not self.overlaps_with(next_group)
                and next_group.group_category == self.group_category
                and next_group.direction_category == self.direction_category
            ):
                support_sum += 1
            right_object = left_object
            left_object = right_object.choose_left_neighbor()
        # Loop rightwards looking for groups.
        left_object = self.rightmost_letter
        right_object = left_object.choose_right_neighbor()
        right_object = (
            right_object
            if right_object is None or isinstance(right_object, Group)
            else right_object.group
        )
        while right_object is not None:
            slot_sum += 1
            next_group = right_object if isinstance(right_object, Group) else None
            if (
                next_group is not None
                and not self.has_sub_group(next_group)
                and not next_group.has_sub_group(self)
                and not self.overlaps_with(next_group)
                and next_group.group_category == self.group_category
                and next_group.direction_category == self.direction_category
            ):
                support_sum += 1
            left_object = right_object
            right_object = left_object.choose_right_neighbor()
        return support_sum / slot_sum if slot_sum > 0 else 1.0
