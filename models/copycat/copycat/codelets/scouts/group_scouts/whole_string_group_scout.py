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
        workspace_string = self.workspace.get_random_string()
        if not workspace_string.bonds:
            return Fizzle(FizzleReason.NO_BONDS)
        chosen_object = workspace_string.choose_from_leftmost_objects()
        first_bond = chosen_object.right_bond
        if first_bond is None:
            return Fizzle(FizzleReason.BONDS_DO_NOT_SPAN_STRING)
        bonds, objects = self._get_bonds_and_objects(
            direction=self.slipnet["right"], first_bond=first_bond
        )
        if not (
            objects[0].is_leftmost_in_string() and objects[-1].is_rightmost_in_string()
        ):
            return Fizzle(FizzleReason.BONDS_DO_NOT_SPAN_STRING)
        chosen_bond = select_item_from_list(bonds, [1] * len(bonds))
        bond_category = chosen_bond.bond_category
        direction_category = chosen_bond.direction_category
        bond_facet = chosen_bond.bond_facet
        possible_group_bonds = self._get_possible_group_bonds(
            bond_category=bond_category,
            direction=direction_category,
            bond_facet=bond_facet,
            bonds=bonds,
        )
        if not possible_group_bonds:
            return Fizzle(FizzleReason.NO_COMPATIBLE_GROUP_BONDS)
        group_category = bond_category.get_related_node("group_category")
        self.propose_group(
            objects=list(objects),
            bonds=possible_group_bonds,
            group_category=group_category,
            direction=direction_category,
            bond_category=bond_category,
            temperature=temperature,
        )
        return Finish()

    def _get_bonds_and_objects(
        self, direction: "Slipnode", first_bond: "Bond"
    ) -> Tuple[List["Bond"], List["WorkspaceObject"]]:
        objects = [first_bond.left_object]
        bonds = []
        next_bond = first_bond
        next_object = first_bond.get_object(direction)
        while next_bond is not None:
            next_object = next_bond.get_object(direction)
            bonds.append(next_bond)
            objects.append(next_object)
            next_bond = next_bond.choose_neighbour(direction)
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
