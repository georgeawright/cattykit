from __future__ import annotations
import random
from typing import List, Union

from cattykit.logging import ModelEvent

from .tools import select_item_from_list
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
        self.bond_descriptions: List["Description"] = []
        self.extrinsic_descriptions: List["Description"] = []
        self.right_bond: Optional["Bond"] = None
        self.left_bond: Optional["Bond"] = None
        self.outgoing_bonds: List["Bond"] = []
        self.incoming_bonds: List["Bond"] = []
        self.group = None
        self.replacement = None
        self.correspondence = None
        self.is_changed_letter = False
        self.is_new_answer_letter = False
        self.salience_is_clamped = False

    def __hash__(self):
        return self.hash_id

    @property
    def neighbours(self) -> list[WorkspaceObject]:
        return self.left_neighbours + self.right_neighbours

    @property
    def left_neighbours(self) -> list[WorkspaceObject]:
        return [
            o for o in self.string.objects if o.right_position == self.left_position - 1
        ]

    @property
    def right_neighbours(self) -> list[WorkspaceObject]:
        return [
            o for o in self.string.objects if o.left_position == self.right_position + 1
        ]

    @property
    def outgoing_and_incoming_bonds(self) -> list["Bond"]:
        return self.outgoing_bonds + [
            b for b in self.incoming_bonds if b not in self.outgoing_bonds
        ]

    @property
    def rule_initial_string_descriptions(self):
        return [
            d
            for d in self.descriptions
            if d.facet.is_active()
            and self.is_distinguished_by(d.descriptor)
            and not (d.facet.name == "object_category")
        ]

    @property
    def rule_modified_string_descriptions(self):
        return [
            d
            for d in self.descriptions
            if d.facet.is_active()
            and self.is_distinguished_by(d.descriptor)
            and d.facet.name != "string_position_category"
            and d.facet.name != "object_category"
        ]

    def distance_from(self, other_object) -> int:
        """Returns the number of letters between this object and another object."""
        if self.string != other_object.string:
            raise ValueError("Objects are not in the same string.")
        if self.right_position < other_object.left_position:
            return other_object.left_position - self.right_position
        elif other_object.right_position < self.left_position:
            return self.left_position - other_object.right_position
        else:
            return 0

    def is_leftmost_in_string(self) -> bool:
        return self.left_position == 0

    def is_rightmost_in_string(self) -> bool:
        return self.right_position == len(self.string.letters) - 1

    def is_at_edge_of_string(self) -> bool:
        return self.is_leftmost_in_string() or self.is_rightmost_in_string()

    def has_description(self, description: "Description") -> bool:
        return any([description.equates_to(d) for d in self.descriptions])

    def get_descriptor(self, facet: "Slipnode") -> Union["Slipnode", None]:
        for description in self.descriptions:
            if description.facet == facet:
                return description.descriptor
        return None

    def get_descriptor_with_facet_name(
        self, facet_name: str
    ) -> Union["Slipnode", None]:
        for description in self.descriptions:
            if description.facet.name == facet_name:
                return description.descriptor
        return None

    def add_description(self, description: "Description"):
        if description.is_bond_description():
            self.bond_descriptions.append(description)
        else:
            self.descriptions.append(description)
        logger = self.string.logger
        if logger is not None:
            logger.log(
                ModelEvent.create(
                    "copycat",
                    "description_created",
                    description_id=f"description:{description.hash_id}",
                    object_id=f"{type(self).__name__.lower()}:{self.hash_id}",
                    facet=description.facet.name,
                    descriptor=description.descriptor.name,
                )
            )

    def has_recursive_group_member(self, other_object) -> bool:
        return self == other_object

    def get_relevant_descriptions(self) -> List["Description"]:
        return [d for d in self.descriptions if d.is_relevant()]

    def get_relevant_distinguishing_descriptions(self) -> List["Description"]:
        return [
            d
            for d in self.descriptions
            if d.is_relevant() and self.is_distinguished_by(d.descriptor)
        ]

    def update_values(self):
        self.raw_importance = self.calculate_raw_importance()
        self.intra_string_unhappiness = self.calculate_intra_string_unhappiness()
        self.inter_string_unhappiness = self.calculate_inter_string_unhappiness()
        self.total_unhappiness = self.calculate_total_unhappiness()
        self.intra_string_salience = self.calculate_intra_string_salience()
        self.inter_string_salience = self.calculate_inter_string_salience()
        self.total_salience = self.calculate_total_salience()

    def spans_whole_string(self) -> bool:
        return self.letter_span() == len(self.string.letters)

    def is_distinguished_by(self, descriptor: "Slipnode") -> bool:
        """True if no other object of the same type has the same descriptor."""
        if descriptor.name in [
            "letter",
            "group",
            "one",
            "two",
            "three",
            "four",
            "five",
        ]:
            return False
        return self._is_distinguished_by(descriptor)

    def _is_distinguished_by(self, descriptor: "Slipnode") -> bool:
        raise NotImplementedError

    def choose_neighbour(self) -> Union[WorkspaceObject, None]:
        saliences = [o.intra_string_salience for o in self.neighbours]
        try:
            return select_item_from_list(self.neighbours, saliences)
        except ValueError:
            return None

    def choose_left_neighbour(self) -> Union[WorkspaceObject, None]:
        """Returns a left-neighbour probabilistically, based on intra-string-salience."""
        saliences = [o.intra_string_salience for o in self.left_neighbours]
        try:
            return select_item_from_list(self.left_neighbours, saliences)
        except ValueError:
            return None

    def choose_right_neighbour(self) -> Union[WorkspaceObject, None]:
        """Returns a right-neighbour probabilistically, based on intra-string-salience."""
        saliences = [o.intra_string_salience for o in self.right_neighbours]
        try:
            return select_item_from_list(self.right_neighbours, saliences)
        except ValueError:
            return None

    def choose_relevant_description_by_activation(self) -> Union["Description", None]:
        relevant_descriptions = self.get_relevant_descriptions()
        if len(relevant_descriptions) == 0:
            return None
        activations = [d.descriptor.activation for d in relevant_descriptions]
        return select_item_from_list(relevant_descriptions, activations)

    def choose_relevant_description_by_conceptual_depth(
        self,
    ) -> Union["Description", None]:
        relevant_descriptions = self.get_relevant_descriptions()
        if len(relevant_descriptions) == 0:
            return None
        conceptual_depths = [
            d.descriptor.conceptual_depth for d in relevant_descriptions
        ]
        return select_item_from_list(relevant_descriptions, conceptual_depths)

    def choose_relevant_distinguishing_description_by_conceptual_depth(
        self,
    ) -> Union["Description", None]:
        relevant_descriptions = self.get_relevant_distinguishing_descriptions()
        if len(relevant_descriptions) == 0:
            return None
        conceptual_depths = [
            d.descriptor.conceptual_depth for d in relevant_descriptions
        ]
        return select_item_from_list(relevant_descriptions, conceptual_depths)

    def get_correspondee(self) -> Optional[WorkspaceObject]:
        """Returns the object in the other string that corresponds to this one, if any."""
        if self.correspondence is None:
            return None
        return self.correspondence.get_other_object(self)

    def calculate_raw_importance(self) -> float:
        """Returns raw (not relative) importance of the object.
        A function of the number and activation of relevant descriptions.
        Importance of changed objects is enhanced.
        Importance of grouped objects is diminished."""
        result = min(
            3,
            sum(
                [
                    description.descriptor.activation
                    for description in self.get_relevant_descriptions()
                ]
            ),
        )
        if self.is_changed_letter:
            result *= 2
        if self.group is not None:
            result *= 2 / 3
        return result

    def calculate_total_unhappiness(self) -> float:
        return 1 - self.calculate_total_happiness()

    def calculate_total_happiness(self) -> float:
        return (
            self.calculate_intra_string_happiness()
            + self.calculate_inter_string_happiness()
        ) / 2

    def calculate_intra_string_unhappiness(self) -> float:
        return 1 - self.calculate_intra_string_happiness()

    def calculate_intra_string_happiness(self) -> float:
        """Represents how well the object fits into the structure of its string.
        It is a function of the strength of the bonds/group involving the object.
        Bonds have a third the weight of groups."""
        if self.spans_whole_string():
            return 1.0
        if self.group is not None:
            return self.group.total_strength
        bonds = self.incoming_bonds + self.outgoing_bonds
        if not bonds:
            return 0.0
        if self.is_leftmost_in_string() or self.is_rightmost_in_string():
            return bonds[0].total_strength / 3
        return sum(bond.total_strength for bond in bonds) / 6

    def calculate_inter_string_unhappiness(self) -> float:
        return 1 - self.calculate_inter_string_happiness()

    def calculate_inter_string_happiness(self) -> float:
        """Represents how well the object fits into a mapping
        from the initial-string to the target-string.
        It is a function of the strength of its correspondence, if any."""
        return self.correspondence.total_strength if self.correspondence else 0.0

    def calculate_total_salience(self) -> float:
        return (self.intra_string_salience + self.inter_string_salience) / 2

    def calculate_intra_string_salience(self) -> float:
        """How much the object is crying out for attention from codelets
        that build structures inside a single string (bonds and groups).
        It is a function of the object's relative importance in its string
        and its intra-string unhappiness.
        Greater weight placed on unhappiness than importance
        may be domain dependent."""
        if self.salience_is_clamped:
            return 1.0
        return self.relative_importance * 0.2 + self.intra_string_unhappiness * 0.8

    def calculate_inter_string_salience(self) -> float:
        """How much the object is crying out for attention from codelets
        that build structures between strings (correspondences).
        It is a function of the object's relative importance in its string
        and its inter-string unhappiness.
        Importance counts more than inter-string unhappiness
        to pressure the program to map important objects,
        and to pay less attention to mapping unimportant ones."""
        if self.salience_is_clamped:
            return 1.0
        return self.relative_importance * 0.8 + self.inter_string_unhappiness * 0.2
