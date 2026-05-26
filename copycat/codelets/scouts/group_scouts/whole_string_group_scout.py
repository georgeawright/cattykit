import random
from typing import List, Optional, Tuple

from copycat.codelets.scouts.group_scout import GroupScout
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

    def run(self, temperature: float):
        workspace_string = random.choices(
            [self.workspace.initial_string, self.workspace.target_string]
        )[0]
        if not workspace_string.bonds:
            return
        chosen_object = workspace_string.choose_from_leftmost_objects()
        first_bond = chosen_object.right_bond
        bond_category = first_bond.bond_category
        direction_category = first_bond.direction_category
        bond_facet = first_bond.bond_facet
        group_category = bond_category.get_related_node("group_category")
        bonds, objects = self._get_bonds_and_objects(
            direction=self.slipnet.get_node("right"),
            first_bond=first_bond,
            number_of_bonds=len(workspace_string) - 1,
        )
        self.propose_group(
            objects=list(objects),
            bonds=list(bonds),
            group_category=group_category,
            direction=direction_category,
        )
