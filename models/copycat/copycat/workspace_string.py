from collections import defaultdict
import random
from typing import Dict, List

from cattykit.logging import ModelEvent, ModelLogger

from .tools import select_item_from_list, temperature_adjust


class WorkspaceString:
    def __init__(self, string_id: str = "unknown", logger: ModelLogger | None = None):
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
                obj.relative_importance = obj.raw_importance / total_raw_importance
            if self.logger is not None:
                self.logger.log(
                    ModelEvent.create(
                        "copycat",
                        "attribute_updated",
                        object_id=_object_id(obj),
                        attribute="relative_importance",
                        value=obj.relative_importance,
                    )
                )

    def update_intra_string_unhappiness(self):
        self.intra_string_unhappiness = (
            sum(o.intra_string_unhappiness for o in self.objects) / len(self.objects)
            if self.objects
            else 0
        )
        if self.logger is not None:
            self.logger.log(
                ModelEvent.create(
                    "copycat",
                    "attribute_updated",
                    object_id=f"string:{self.string_id}",
                    attribute="intra_string_unhappiness",
                    value=self.intra_string_unhappiness,
                )
            )

    def empty(self):
        self.__init__(self.string_id, self.logger)

    def add_letter(self, letter):
        self.letters.append(letter)
        if self.logger is not None:
            self._log(
                "letter_created",
                letter_id=f"letter:{letter.hash_id}",
                string_id=self.string_id,
                position=letter.left_position,
                letter_category=letter.letter_category.name,
            )

    def add_proposed_bond(self, bond):
        """Add to a maintained list of proposed bonds between two nodes."""
        self.proposed_bonds_by_role[bond.source][bond.target].append(bond)
        self._log_structure("bond_proposed", bond)

    def delete_proposed_bond(self, bond):
        """Delete from a maintained list of proposed bonds between two objects."""
        self.proposed_bonds_by_role[bond.source][bond.target].remove(bond)
        self._log_structure("bond_destroyed", bond)

    def add_bond(self, bond):
        """Add the only bond between two objects."""
        self.bonds_by_role[bond.source][bond.target] = bond
        self.bonds_by_position[bond.left_object][bond.right_object] = bond
        if bond.bond_category.name == "sameness":
            self.bonds_by_role[bond.target][bond.source] = bond
            self.bonds_by_position[bond.left_object][bond.right_object] = bond
        self._log_structure("bond_created", bond)

    def delete_bond(self, bond):
        """Delete the only bond between two objects."""
        self.bonds_by_role[bond.source][bond.target] = None
        self.bonds_by_position[bond.left_object][bond.right_object] = None
        if bond.bond_category.name == "sameness":
            self.bonds_by_role[bond.target][bond.source] = None
            self.bonds_by_position[bond.left_object][bond.right_object] = None
        self._log_structure("bond_destroyed", bond)

    def get_bond_if_present(self, bond):
        """Return the equivalent bond if it is already in the string, else False."""
        existing_bond = self.bonds_by_role[bond.source][bond.target]
        if existing_bond == bond:
            return existing_bond
        return False

    def add_proposed_group(self, group):
        """Add to a list of proposed groups spanning from one object to another."""
        self._proposed_groups[group.left_object][group.right_object].append(group)
        self._log_structure("group_proposed", group)

    def delete_proposed_group(self, group):
        """Delete from a list of proposed bonds spanning from one object to another."""
        self._proposed_groups[group.left_object][group.right_object].remove(group)
        self._log_structure("group_destroyed", group)

    def add_group(self, group):
        """Add the only group spanning from one object to another."""
        self._groups[group.left_object] = group
        self.object_positions[group.left_position].append(group)
        self.object_positions[group.right_position].append(group)
        self._log_structure("group_created", group)

    def delete_group(self, group):
        """Delete the only group spanning from one object to another."""
        self._groups[group.left_object] = None
        self.object_positions[group.left_position].remove(group)
        self.object_positions[group.right_position].remove(group)
        self._log_structure("group_destroyed", group)

    def _log_structure(self, kind: str, structure: object) -> None:
        if self.logger is None:
            return
        data = (
            _bond_data(structure)
            if kind.startswith("bond_")
            else _group_data(structure)
        )
        self._log(kind, **data)

    def _log(self, kind: str, **data: object) -> None:
        if self.logger is None:
            return
        entity = kind.rsplit("_", maxsplit=1)[0]
        identifier = f"{entity}_id"
        if identifier not in data:
            value = data.pop(entity)
            data[identifier] = f"{entity}:{value.hash_id}"
        self.logger.log(ModelEvent.create("copycat", kind, **data))

    def get_group_if_present(self, group):
        """Return the equivalent group if it is already in the string, else False."""
        try:
            existing_group = self._groups[group.left_object]
        except KeyError:
            return False
        if existing_group == group:
            return existing_group
        return False

    def choose_object(self, temperature, method) -> "WorkspaceObject":
        """Return an object probabilistically according to temperature and method."""
        weights = [temperature_adjust(method(obj), temperature) for obj in self.objects]
        return select_item_from_list(self.objects, weights)

    def choose_from_leftmost_objects(self):
        """Returns one of the leftmost objects probabilistically."""
        leftmost_objects = [obj for obj in self.objects if obj.is_leftmost_in_string()]
        weights = [obj.relative_importance for obj in leftmost_objects]
        try:
            return select_item_from_list(leftmost_objects, weights)
        except IndexError:
            return None

    def get_local_bond_category_relevance(self, bond_category: "Slipnode") -> float:
        """A rough estimate of the relevance of bond category in this string."""
        if len(self.non_string_spanning_objects) <= 1:
            return 0
        bond_count = sum(
            1
            for obj in self.non_string_spanning_objects
            if obj.right_bond is not None
            and obj.right_bond.bond_category == bond_category
        )
        return bond_count / (len(self.non_string_spanning_objects) - 1)

    def get_local_direction_category_relevance(
        self, direction_category: "Slipnode"
    ) -> float:
        """A rough estimate of the relevance of direction category in this string."""
        if len(self.non_string_spanning_objects) <= 1:
            return 0
        bond_count = sum(
            1
            for obj in self.non_string_spanning_objects
            if obj.right_bond is not None
            and obj.right_bond.direction_category == direction_category
        )
        return bond_count / (len(self.non_string_spanning_objects) - 1)

    def get_changed_objects(self) -> List["WorkspaceObject"]:
        return [l for l in self.letters if l.is_changed_letter]


def _object_id(obj: object) -> str:
    return f"{type(obj).__name__.lower()}:{obj.hash_id}"


def _node_name(value: object | None) -> str | None:
    return None if value is None else value.name


def _bond_data(bond: object) -> dict[str, object]:
    return {
        "bond": bond,
        "string_id": bond.string.string_id,
        "source_id": _object_id(bond.source),
        "target_id": _object_id(bond.target),
        "bond_category": bond.bond_category.name,
        "direction_category": _node_name(bond.direction_category),
        "bond_facet": bond.bond_facet.name,
        "source_descriptor": bond.source_descriptor.name,
        "target_descriptor": bond.target_descriptor.name,
    }


def _group_data(group: object) -> dict[str, object]:
    return {
        "group": group,
        "string_id": group.string.string_id,
        "group_category": group.group_category.name,
        "direction_category": _node_name(group.direction_category),
        "bond_category": group.bond_category.name,
        "bond_facet": _node_name(group.bond_facet),
        "left_position": group.left_position,
        "right_position": group.right_position,
        "members": [_object_id(member) for member in group.objects],
        "bonds": [f"bond:{bond.hash_id}" for bond in group.bonds],
    }
