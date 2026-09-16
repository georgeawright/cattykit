import random
from typing import List, Optional, Tuple

from copycat.codelets.scouts.group_scout import GroupScout
from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.slipnode import Slipnode
from copycat.tools import select_item_from_list, temperature_adjust_probability
from copycat.workspace_objects_and_structures import Group


class TopDownCategoryGroupScout(GroupScout):
    def __init__(
        self,
        urgency_bin: int,
        coderack: "Coderack",
        slipnet: "Slipnet",
        workspace: "Workspace",
        group_category: Slipnode,
    ):
        super().__init__(
            urgency_bin=urgency_bin,
            coderack=coderack,
            workspace=workspace,
            slipnet=slipnet,
        )
        self.group_category = group_category

    def run(self, temperature: float) -> CodeletResult:
        self.bond_category = self.group_category.get_related_node("bond_category")
        self.workspace_string = self.choose_workspace_string(self.bond_category)
        self.chosen_object = self.workspace_string.choose_object(
            temperature, lambda x: x.intra_string_salience
        )
        if self.chosen_object.spans_whole_string:
            return Fizzle(FizzleReason.OBJECT_SPANS_WHOLE_STRING)
        self.direction_to_scan = self._choose_direction(self.chosen_object)
        self.number_of_bonds = self._choose_number_of_bonds(self.workspace_string)
        self.first_bond = self._get_first_bond(
            self.direction_to_scan, self.chosen_object
        )
        if self.first_bond is None or self.first_bond.bond_category != self.bond_category:
            if isinstance(self.chosen_object, Group):
                return Fizzle(FizzleReason.CANNOT_MAKE_GROUP_FROM_SINGLE_GROUP)
            self.objects = [self.chosen_object]
            self.bonds = []
            if self.group_category == self.slipnet["sameness_group"]:
                self.possible_single_letter_group_direction = None
            else:
                directions = [self.slipnet["left"], self.slipnet["right"]]
                supports = [
                    d.get_local_descriptor_support(
                        self.workspace_string, self.slipnet["group"]
                    )
                    for d in directions
                ]
                self.possible_single_letter_group_direction = select_item_from_list(
                    directions, supports
                )
            self.left_object = min(self.objects, key=lambda o: o.left_position)
            self.right_object = max(self.objects, key=lambda o: o.right_position)
            self.possible_group = Group(
                string=self.workspace_string,
                left_position=self.left_object.left_position,
                right_position=self.right_object.right_position,
                objects=self.objects,
                bonds=self.bonds,
                group_category=self.group_category,
                direction_category=self.possible_single_letter_group_direction,
                bond_category=self.bond_category,
            )
            single_letter_group_probability = (
                self._calculate_single_letter_group_probability(
                    self.possible_group, temperature
                )
            )
            if random.random() > single_letter_group_probability:
                return Fizzle(FizzleReason.NOT_ENOUGH_SUPPORT_FOR_SINGLE_LETTER_GROUP)
            self.direction_category = self.possible_single_letter_group_direction
            self.propose_group(temperature)
            return Finish()
        self.direction_category = self.first_bond.direction_category
        self.bonds, self.objects = self._get_bonds_and_objects(
            self.direction_to_scan, self.first_bond, self.number_of_bonds
        )
        self.propose_group(temperature)
        return Finish()

    def choose_workspace_string(self, bond_category: Optional[Slipnode]):
        initial_string_relevance = (
            self.workspace.initial_string.get_local_bond_category_relevance(
                bond_category
            )
        )
        target_string_relevance = (
            self.workspace.target_string.get_local_bond_category_relevance(
                bond_category
            )
        )
        return self._choose_workspace_string(
            initial_string_relevance, target_string_relevance
        )

    def _calculate_single_letter_group_probability(
        self, group: Group, temperature: float
    ) -> float:
        exponent = {
            1: 4,
            2: 2,
        }.get(group._number_of_local_supporting_groups(), 1)
        probability = group._local_support() * self.slipnet["length"].activation
        probability **= exponent
        return temperature_adjust_probability(probability, temperature)
