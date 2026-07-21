import random

from copycat.codelets.builders import GroupBuilder
from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.codelets.strength_tester import StrengthTester
from copycat.tools import temperature_adjust
from copycat.workspace_objects.group import Group


class GroupStrengthTester(StrengthTester):
    """A group strength tester calculates the strength of a group.
    It probabilistically posts a group builder with urgency a function of strength.
    """

    def __init__(
        self,
        urgency_bin: int,
        coderack: "Coderack",
        slipnet: "Slipnet",
        workspace: "Workspace",
        proposed_group: Group,
    ):
        super().__init__(
            urgency_bin=urgency_bin,
            coderack=coderack,
            slipnet=slipnet,
            workspace=workspace,
            proposed_structure=proposed_group,
        )
        self.proposed_group = proposed_group

    def run(self, temperature: float) -> CodeletResult:
        self.proposed_group.update_strength_values()
        build_probability = temperature_adjust(
            self.proposed_group.total_strength, temperature
        )
        if build_probability < random.random():
            self.proposed_group.string.delete_proposed_group(self.proposed_group)
            return Fizzle(FizzleReason.PROPOSED_STRUCTURE_TOO_WEAK)
        self.slipnet.activate_node_from_workspace(
            self.proposed_group.bond_category.name
        )
        if self.proposed_group.direction_category is not None:
            self.slipnet.activate_node_from_workspace(
                self.proposed_group.direction_category.name
            )
        urgency = self.coderack.get_urgency_level_from_activation(
            self.proposed_group.total_strength
        )
        self.coderack.post(
            GroupBuilder(
                urgency_bin=urgency,
                coderack=self.coderack,
                slipnet=self.slipnet,
                workspace=self.workspace,
                proposed_group=self.proposed_group,
            )
        )
        return Finish()
