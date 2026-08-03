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
        workspace_string = self.choose_workspace_string()
        chosen_object = workspace_string.choose_object(
            temperature, lambda x: x.intra_string_salience
        )
        if chosen_object.spans_whole_string():
            return Fizzle(FizzleReason.OBJECT_SPANS_WHOLE_STRING)
        direction = self._choose_direction(chosen_object)
        number_of_bonds = self._choose_number_of_bonds(workspace_string)
        first_bond = self._get_first_bond(direction, chosen_object)
        if first_bond is None:
            return Fizzle(FizzleReason.NO_FIRST_BOND)
        if first_bond.direction_category != self.direction_category:
            return Fizzle(FizzleReason.BOND_DIRECTION_DOES_NOT_MATCH)
        bond_category = first_bond.bond_category
        bond_facet = first_bond.bond_facet
        opposite_bond_category = bond_category.get_related_node("opposite")
        opposte_direction_category = direction.get_related_node("opposite")
        group_category = bond_category.get_related_node("group_category")
        bonds, objects = self._get_bonds_and_objects(
            direction, first_bond, number_of_bonds
        )
        self.propose_group(
            objects=objects,
            bonds=bonds,
            group_category=group_category,
            direction=self.direction_category,
            temperature=temperature,
        )
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
