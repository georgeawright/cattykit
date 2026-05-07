import random
from typing import Optional

from copycat.codelets.scouts.group_scout import GroupScout
from copycat.slipnode import Slipnode


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

    def run(self, temperature: float):
        bond_category = self.group_category.get_related_node("bond_category")
        workspace_string = self._choose_workspace_string(bond_category)
        chosen_object = workspace_string.choose_object(
            temperature, lambda x: x.intra_string_salience
        )
        if chosen_object.spans_whole_string():
            return
        direction = self._choose_direction(chosen_object)
        number_of_bonds = self._choose_number_of_bonds(workspace_string)
        # TODO: finish

    def _choose_workspace_string(self, bond_category: Optional[Slipnode]):
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
        initial_string_unhappiness = (
            self.workspace.initial_string.intra_string_unhappiness
        )
        target_string_unhappiness = (
            self.workspace.target_string.intra_string_unhappiness
        )
        initial_string_score = (
            initial_string_relevance + initial_string_unhappiness
        ) / 2
        target_string_score = (target_string_relevance + target_string_unhappiness) / 2
        chosen_string = random.choices(
            [self.workspace.initial_string, self.workspace.target_string],
            weights=[initial_string_score, target_string_score],
        )[0]
        return chosen_string

    def _choose_direction(self, chosen_object):
        if chosen_object.is_leftmost_in_string:
            return self.slipnet.get_node("right")
        elif chosen_object.is_rightmost_in_string:
            return self.slipnet.get_node("left")
        left = self.slipnet.get_node("left")
        right = self.slipnet.get_node("right")
        return random.choices(
            [left, right], weights=[left.activation, right.activation]
        )[0]

    def _choose_number_of_bonds(self, workspace_string):
        number_of_bonds = random.choices(
            workspace_string.distribution_of_bond_counts,
            weights=workspace_string.distribution_of_bond_counts,
        )[0]
        return number_of_bonds
