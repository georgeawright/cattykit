from collections import defaultdict
import random
from typing import Dict, List

from cattykit.logging import ModelLogger

from .tools import select_item_from_list, temperature_adjust


class WorkspaceString:
    def __init__(self, string_id: str, logger: ModelLogger):
        self.string_id = string_id
        self.logger = logger
        self.letters = []
        self.object_positions = defaultdict(list)
        self.proposed_bonds_by_role = defaultdict(lambda: defaultdict(list))
        self.bonds_by_role = defaultdict(lambda: defaultdict(lambda: None))
        self.bonds_by_position = defaultdict(lambda: defaultdict(lambda: None))
        self._proposed_groups = defaultdict(lambda: defaultdict(list))
        self._groups: Dict["Group"] = {}
        self.distribution_of_bond_counts = [0]
        self.intra_string_unhappiness = 0

    def __len__(self):
        return len(self.letters)

    def __repr__(self):
        return f"WorkspaceString({self.letters})"

    @property
    def proposed_bonds(self):
        unique_bonds = []
        added = set()
        for source_index, bonds in self.proposed_bonds_by_role.items():
            for target_index, bond_list in bonds.items():
                for bond in bond_list:
                    if bond in added:
                        continue
                    unique_bonds.append(bond)
                    added.add(bond)
        return unique_bonds

    @property
    def bonds(self):
        unique_bonds = []
        added = set()
        for source_index, bonds in self.bonds_by_role.items():
            for target_index, bond in bonds.items():
                if bond is None:
                    continue
                if bond in added:
                    continue
                unique_bonds.append(bond)
                added.add(bond)
        return unique_bonds

    @property
    def proposed_groups(self):
        return [
            group
            for left_index, groups in self._proposed_groups.items()
            for right_index, group_list in groups.items()
            for group in group_list
        ]

    @property
    def groups(self):
        return [
            group for left_index, group in self._groups.items() if group is not None
        ]

    @property
    def objects(self):
        return self.letters + self.groups

    @property
    def non_string_spanning_objects(self):
        return [obj for obj in self.objects if not obj.spans_whole_string]

    def update_relative_importances(self):
        total_raw_importance = sum(obj.raw_importance for obj in self.objects)
        for obj in self.objects:
            if total_raw_importance == 0:
                obj.relative_importance = 0
            else:
                obj.relative_importance = self._relative_importance(
                    obj.raw_importance, total_raw_importance
                )
            self.logger.log(
                "attribute_updated", object=obj, attribute="relative_importance"
            )

    def update_intra_string_unhappiness(self):
        self.intra_string_unhappiness = self._average_unhappiness(
            [object_.intra_string_unhappiness for object_ in self.objects]
        )
        self.logger.log(
            "attribute_updated", object=self, attribute="intra_string_unhappiness"
        )

    def empty(self):
        self.__init__(self.string_id, self.logger)

    def add_letter(self, letter):
        self.letters.append(letter)
        self.logger.log("letter_created", letter=letter)

    def contains_bond(self, b) -> bool:
        """Returns True if the string contains an equivalent bond."""
        for bond in self.bonds:
            if b.equates_to(bond):
                return True
        return False

    def add_proposed_description(self, description):
        self.logger.log("description_proposed", description=description)

    def add_proposed_bond(self, bond):
        """Add to a maintained list of proposed bonds between two nodes."""
        self.proposed_bonds_by_role[bond.source][bond.target].append(bond)
        self.logger.log("bond_proposed", bond=bond)

    def delete_proposed_bond(self, bond):
        """Delete from a maintained list of proposed bonds between two objects."""
        self.proposed_bonds_by_role[bond.source][bond.target].remove(bond)
        self.logger.log("bond_destroyed", bond=bond)

    def add_bond(self, bond):
        """Add the only bond between two objects."""
        self.bonds_by_role[bond.source][bond.target] = bond
        self.bonds_by_position[bond.left_object][bond.right_object] = bond
        if bond.bond_category.name == "sameness":
            self.bonds_by_role[bond.target][bond.source] = bond
            self.bonds_by_position[bond.left_object][bond.right_object] = bond
        self.logger.log("bond_created", bond=bond)

    def delete_bond(self, bond):
        """Delete the only bond between two objects."""
        self.bonds_by_role[bond.source][bond.target] = None
        self.bonds_by_position[bond.left_object][bond.right_object] = None
        if bond.bond_category.name == "sameness":
            self.bonds_by_role[bond.target][bond.source] = None
            self.bonds_by_position[bond.left_object][bond.right_object] = None
        self.logger.log("bond_destroyed", bond=bond)

    def get_bond_if_present(self, bond):
        """Return the equivalent bond if it is already in the string, else False."""
        existing_bond = self.bonds_by_role[bond.source][bond.target]
        if bond.equates_to(existing_bond):
            return existing_bond
        return False

    def add_proposed_group(self, group):
        """Add to a list of proposed groups spanning from one object to another."""
        self._proposed_groups[group.left_object][group.right_object].append(group)
        self.logger.log("group_proposed", group=group)

    def delete_proposed_group(self, group):
        """Delete from a list of proposed bonds spanning from one object to another."""
        self._proposed_groups[group.left_object][group.right_object].remove(group)
        self.logger.log("group_destroyed", group=group)

    def add_group(self, group):
        """Add the only group spanning from one object to another."""
        self._groups[group.left_object] = group
        self.object_positions[group.left_position].append(group)
        self.object_positions[group.right_position].append(group)
        self.logger.log("group_created", group=group)

    def delete_group(self, group):
        """Delete the only group spanning from one object to another."""
        # A codelet can retain a group instance that is semantically equivalent
        # to one subsequently rebuilt in the string.  Reconcile to the
        # canonical instance before removing it from positional indexes.
        existing_group = self.get_group_if_present(group)
        if not existing_group:
            return
        group = existing_group
        self._groups[group.left_object] = None
        self.object_positions[group.left_position].remove(group)
        self.object_positions[group.right_position].remove(group)
        self.logger.log("group_destroyed", group=group)

    def get_group_if_present(self, group):
        """Return the equivalent group if it is already in the string, else False."""
        try:
            existing_group = self._groups[group.left_object]
        except KeyError:
            return False
        if group.equates_to(existing_group):
            return existing_group
        return False

    def choose_object(self, temperature, method) -> "WorkspaceObject":
        """Return an object probabilistically according to temperature and method."""
        weights = [temperature_adjust(method(obj), temperature) for obj in self.objects]
        return select_item_from_list(self.objects, weights)

    def choose_from_leftmost_objects(self):
        """Returns one of the leftmost objects probabilistically."""
        leftmost_objects = [
            obj
            for obj in self.objects
            if (lambda x: x is not None and x.name == "leftmost")(
                obj.get_descriptor_with_facet_name("string_position_category")
            )
        ]
        weights = [obj.relative_importance for obj in leftmost_objects]
        try:
            return select_item_from_list(leftmost_objects, weights)
        except IndexError:
            return None

    def get_local_bond_category_relevance(self, bond_category: "Slipnode") -> float:
        """A rough estimate of the relevance of bond category in this string."""
        objects = self.non_string_spanning_objects
        bond_count = sum(
            1
            for obj in objects
            if obj.right_bond is not None
            and obj.right_bond.bond_category == bond_category
        )
        return self._local_relevance(bond_count, max(0, len(objects) - 1))

    def get_local_direction_category_relevance(
        self, direction_category: "Slipnode"
    ) -> float:
        """A rough estimate of the relevance of direction category in this string."""
        objects = self.non_string_spanning_objects
        bond_count = sum(
            1
            for obj in objects
            if obj.right_bond is not None
            and obj.right_bond.direction_category == direction_category
        )
        return self._local_relevance(bond_count, max(0, len(objects) - 1))

    @staticmethod
    def _relative_importance(
        raw_importance: float, total_raw_importance: float
    ) -> float:
        """Return one object's share of its string's raw importance.

        pre: 0.0 <= raw_importance <= total_raw_importance
        pre: 0.0 < total_raw_importance
        post: 0.0 <= _ <= 1.0
        """
        return raw_importance / total_raw_importance

    @staticmethod
    def _average_unhappiness(unhappinesses: list[float]) -> float:
        """Return the average of zero or more normalized unhappiness values.

        pre: all(0.0 <= unhappiness <= 1.0 for unhappiness in unhappinesses)
        post: 0.0 <= _ <= 1.0
        """
        return sum(unhappinesses) / len(unhappinesses) if unhappinesses else 0.0

    @staticmethod
    def _local_relevance(matching_bond_count: int, available_slots: int) -> float:
        """Return the proportion of available bond slots that match a category.

        pre: 0 <= available_slots
        pre: 0 <= matching_bond_count <= available_slots
        post: 0.0 <= _ <= 1.0
        """
        return matching_bond_count / available_slots if available_slots else 0.0

    def get_changed_objects(self) -> List["WorkspaceObject"]:
        return [l for l in self.letters if l.is_changed_letter]
