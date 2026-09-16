from typing import List, Optional, Tuple

from copycat.codelets.scouts.group_scout import GroupScout
from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.slipnode import Slipnode


class TopDownDirectionGroupScout(GroupScout):
    def __init__(
        self,
        urgency_bin: int,
        coderack: "Coderack",
        slipnet: "Slipnet",
        workspace: "Workspace",
        direction_category: Slipnode,
    ):
        super().__init__(
            urgency_bin=urgency_bin,
            coderack=coderack,
            workspace=workspace,
            slipnet=slipnet,
        )
        self.direction_category = direction_category

    def run(self, temperature: float) -> CodeletResult:
        self.workspace_string = self.choose_workspace_string()
        self.chosen_object = self.workspace_string.choose_object(
            temperature, lambda x: x.intra_string_salience
        )
        if self.chosen_object.spans_whole_string:
            return Fizzle(FizzleReason.OBJECT_SPANS_WHOLE_STRING)
        self.direction = self._choose_direction(self.chosen_object)
        self.number_of_bonds = self._choose_number_of_bonds(self.workspace_string)
        self.first_bond = self._get_first_bond(self.direction, self.chosen_object)
        if self.first_bond is None:
            return Fizzle(FizzleReason.NO_FIRST_BOND)
        if self.first_bond.direction_category != self.direction_category:
            return Fizzle(FizzleReason.BOND_DIRECTION_DOES_NOT_MATCH)
        self.bond_category = self.first_bond.bond_category
        self.group_category = self.bond_category.get_related_node("group_category")
        self.bonds, self.objects = self._get_bonds_and_objects(
            self.direction, self.first_bond, self.number_of_bonds
        )
        self.propose_group(temperature)
        return Finish()

    def choose_workspace_string(self):
        initial_string_relevance = (
            self.workspace.initial_string.get_local_direction_category_relevance(
                self.direction_category
            )
        )
        target_string_relevance = (
            self.workspace.target_string.get_local_direction_category_relevance(
                self.direction_category
            )
        )
        return self._choose_workspace_string(
            initial_string_relevance, target_string_relevance
        )
