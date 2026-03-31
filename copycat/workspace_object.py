from __future__ import annotations
import random
from typing import List, Union

from .workspace_structure import WorkspaceStructure


class WorkspaceObject:
    def __init__(self, string, left_position: int, right_position: int):
        self.string = string
        self.left_position = left_position
        self.right_position = right_position
        self.raw_importance = 0
        self.relative_importance = 0
        self.intra_string_unhappiness = 0
        self.inter_string_unhappiness = 0
        self.total_unhappiness = 0
        self.intra_string_salience = 0
        self.inter_string_salience = 0
        self.total_salience = 0
        self.descriptions: List["Description"] = []
        self.extrinsic_descriptions: List["Description"] = []
        self.outgoing_bonds: List["Bond"] = []
        self.incoming_bonds: List["Bond"] = []
        self.group = None
        self.replacement = None
        self.correspondence = None
        self.is_changed_letter = False
        self.is_new_answer_letter = False
        self.salience_is_clamped = False

    def add_description(self, description: "Description"):
        self.descriptions.append(description)

    def has_recursive_group_member(self, other_object) -> bool:
        if self == other_object:
            return True

    def update_values(self):
        # TODO
        pass

    @property
    def left_neighbours(self):
        return [
            o for o in self.string.objects if o.right_position == self.left_position - 1
        ]

    @property
    def right_neighbours(self):
        return [
            o for o in self.string.objects if o.left_position == self.right_position + 1
        ]

    def spans_whole_string(self) -> bool:
        return len(self) == len(self.string.letters)

    def is_distinguished_by(self, descriptor: "Slipnode") -> bool:
        """True if no other object of the same type has the same descriptor."""
        if descriptor.name in ["letter", "group", "1", "2", "3", "4", "5", "6"]:
            return False
        return self._is_distinguished_by(descriptor)

    def _is_distinguished_by(self, descriptor: "Slipnode") -> bool:
        raise NotImplementedError

    def choose_left_neighbor(self) -> Union[WorkspaceObject, None]:
        """Returns a left-neighbor probabilistically, based on intra-string-salience."""
        saliences = [o.intra_string_salience for o in self.left_neighbours]
        try:
            return random.choices(self.left_neighbours, weights=saliences, k=1)[0]
        except IndexError:
            return None

    def choose_right_neighbor(self) -> Union[WorkspaceObject, None]:
        """Returns a right-neighbor probabilistically, based on intra-string-salience."""
        saliences = [o.intra_string_salience for o in self.right_neighbours]
        try:
            return random.choices(self.right_neighbours, weights=saliences, k=1)[0]
        except IndexError:
            return None
