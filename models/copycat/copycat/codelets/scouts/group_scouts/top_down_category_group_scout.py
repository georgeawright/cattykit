import random
from typing import List, Optional, Tuple

from copycat.codelets.scouts.group_scout import GroupScout
from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.slipnode import Slipnode
from copycat.tools import select_item_from_list, temperature_adjust
from copycat.workspace_objects import Group


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
        bond_category = self.group_category.get_related_node("bond_category")
        workspace_string = self.choose_workspace_string(bond_category)
        chosen_object = workspace_string.choose_object(
            temperature, lambda x: x.intra_string_salience
        )
        if chosen_object.spans_whole_string():
            return Fizzle(FizzleReason.OBJECT_SPANS_WHOLE_STRING)
        direction_to_scan = self._choose_direction(chosen_object)
        number_of_bonds = self._choose_number_of_bonds(workspace_string)
        first_bond = self._get_first_bond(direction_to_scan, chosen_object)
        if first_bond is None or first_bond.bond_category != bond_category:
            if isinstance(chosen_object, Group):
                return Fizzle(FizzleReason.CANNOT_MAKE_GROUP_FROM_SINGLE_GROUP)
            objects = [chosen_object]
            bonds = []
            if self.group_category == self.slipnet["sameness_group"]:
                possible_single_letter_group_direction = None
            else:
                directions = [self.slipnet["left"], self.slipnet["right"]]
                supports = [
                    d.get_descriptor_support(workspace_string, self.slipnet["group"])
                    for d in directions
                ]
                possible_single_letter_group_direction = select_item_from_list(
                    directions, supports
                )
            left_object = min(objects, key=lambda o: o.left_position)
            right_object = max(objects, key=lambda o: o.right_position)
            possible_group = Group(
                string=workspace_string,
                left_position=left_object.left_position,
                right_position=right_object.right_position,
                objects=objects,
                bonds=bonds,
                group_category=self.group_category,
                direction_category=possible_single_letter_group_direction,
                bond_category=bond_category,
            )
            single_letter_group_probability = (
                self._calculate_single_letter_group_probability(
                    possible_group, temperature
                )
            )
            if random.random() > single_letter_group_probability:
                return Fizzle(FizzleReason.NOT_ENOUGH_SUPPORT_FOR_SINGLE_LETTER_GROUP)
            self.propose_group(
                objects=objects,
                bonds=bonds,
                group_category=self.group_category,
                direction=possible_single_letter_group_direction,
                bond_category=bond_category,
                temperature=temperature,
            )
            return Finish()
        direction_category = first_bond.direction_category
        bonds, objects = self._get_bonds_and_objects(
            direction_to_scan, first_bond, number_of_bonds
        )
        self.propose_group(
            objects=objects,
            bonds=bonds,
            group_category=self.group_category,
            direction=direction_category,
            bond_category=bond_category,
            temperature=temperature,
        )
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
        return temperature_adjust(probability, temperature)
