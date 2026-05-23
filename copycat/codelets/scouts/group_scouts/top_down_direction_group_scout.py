import random
from typing import List, Optional, Tuple

from copycat.codelets.scouts.group_scout import GroupScout
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

    def run(self, temperature: float):
        workspace_string = self.choose_workspace_string()

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
