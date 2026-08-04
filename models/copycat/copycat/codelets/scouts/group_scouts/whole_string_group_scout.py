import random
from typing import List, Optional, Tuple

from copycat.codelets.scouts.group_scout import GroupScout
from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.slipnode import Slipnode


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
        required_number_of_bonds = len(workspace_string) - 1
        bonds, objects = self._get_bonds_and_objects(
            direction=self.slipnet["right"],
            first_bond=first_bond,
            number_of_bonds=required_number_of_bonds,
        )
        if len(bonds) < required_number_of_bonds:
            return Fizzle(FizzleReason.BONDS_DO_NOT_SPAN_STRING)
        chosen_bond = random.choices(bonds)[0]
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
            bonds=list(bonds),
            group_category=group_category,
            direction=direction_category,
            bond_category=bond_category,
            temperature=temperature,
        )
        return Finish()

    def _get_bonds_and_objects(
        self, direction: "Slipnode", first_bond: "Bond", number_of_bonds: int
    ) -> Tuple[List["Bond"], List["WorkspaceObject"]]:
        objects = [first_bond.left_object, first_bond.right_object]
        bonds = [first_bond]
        next_bond = first_bond
        for i in range(2, number_of_bonds + 1):
            next_bond = next_bond.choose_neighbour(direction)
            if next_bond is None:
                break
            next_object = next_bond.get_object(direction)
            bonds.append(next_bond)
            objects.append(next_object)
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
