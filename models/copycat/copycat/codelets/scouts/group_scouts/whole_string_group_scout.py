from typing import List, Optional, Tuple

from copycat.codelets.scouts.group_scout import GroupScout
from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.slipnode import Slipnode
from copycat.tools import select_item_from_list


class WholeStringGroupScout(GroupScout):
    def __init__(
        self,
        urgency_bin: int,
        coderack: "Coderack",
        slipnet: "Slipnet",
        workspace: "Workspace",
    ):
        super().__init__(
            urgency_bin=urgency_bin,
            coderack=coderack,
            workspace=workspace,
            slipnet=slipnet,
        )

    def run(self, temperature: float) -> CodeletResult:
        self.workspace_string = self.workspace.get_random_string()
        if not self.workspace_string.bonds:
            return Fizzle(FizzleReason.NO_BONDS)
        self.chosen_object = self.workspace_string.choose_from_leftmost_objects()
        self.first_bond = self.chosen_object.right_bond
        if self.first_bond is None:
            return Fizzle(FizzleReason.BONDS_DO_NOT_SPAN_STRING)
        self.bonds, self.objects = self._get_bonds_and_objects(
            direction=self.slipnet["right"], first_bond=self.first_bond
        )
        if not (
            self.objects[0].is_leftmost_in_string
            and self.objects[-1].is_rightmost_in_string
        ):
            return Fizzle(FizzleReason.BONDS_DO_NOT_SPAN_STRING)
        self.chosen_bond = select_item_from_list(self.bonds, [1] * len(self.bonds))
        self.bond_category = self.chosen_bond.bond_category
        self.direction_category = self.chosen_bond.direction_category
        self.bond_facet = self.chosen_bond.bond_facet
        self.possible_group_bonds = self._get_possible_group_bonds(
            bond_category=self.bond_category,
            direction=self.direction_category,
            bond_facet=self.bond_facet,
            bonds=self.bonds,
        )
        if not self.possible_group_bonds:
            return Fizzle(FizzleReason.NO_COMPATIBLE_GROUP_BONDS)
        self.group_category = self.bond_category.get_related_node("group_category")
        self.objects = list(self.objects)
        self.bonds = self.possible_group_bonds
        self.propose_group(temperature)
        return Finish()

    def _get_bonds_and_objects(
        self, direction: "Slipnode", first_bond: "Bond"
    ) -> Tuple[List["Bond"], List["WorkspaceObject"]]:
        objects = [first_bond.left_object]
        bonds = []
        next_bond = first_bond
        while next_bond is not None:
            next_object = next_bond.get_object(direction)
            bonds.append(next_bond)
            objects.append(next_object)
            next_bond = (
                next_object.right_bond
                if direction.name == "right"
                else next_object.left_bond
            )
        return bonds, objects

    def _get_possible_group_bonds(
        self,
        bond_category: Slipnode,
        direction: Slipnode,
        bond_facet: Slipnode,
        bonds: List["Bond"],
    ) -> List["Bond"]:
        possible_group_bonds = []
        for bond in bonds:
            if bond is None:
                return []
            elif bond.bond_facet != bond_facet:
                return []
            elif (
                bond.bond_category.get_related_node("opposite") == bond_category
                and bond.direction_category.get_related_node("opposite") == direction
            ):
                possible_group_bonds.append(bond.get_flipped_version())
            elif (
                bond.bond_category != bond_category
                or bond.direction_category != direction
            ):
                return []
            else:
                possible_group_bonds.append(bond)
        return possible_group_bonds
