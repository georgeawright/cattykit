import random

from copycat.codelets.builders import DescriptionBuilder
from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.codelets.strength_tester import StrengthTester
from copycat.tools import temperature_adjust
from copycat.workspace_structures import Description


class DescriptionStrengthTester(StrengthTester):
    """A description strength tester calculates the strength of a proposed description.
    It probabilistically posts a description builder with urgency a function of strength.
    """

    def __init__(
        self,
        urgency_bin: int,
        coderack: "Coderack",
        slipnet: "Slipnet",
        workspace: "Workspace",
        proposed_description: Description,
    ):
        super().__init__(
            urgency_bin=urgency_bin,
            coderack=coderack,
            slipnet=slipnet,
            workspace=workspace,
            proposed_structure=proposed_description,
        )
        self.proposed_description = proposed_description

    def run(self, temperature: float) -> CodeletResult:
        self.slipnet.activate_node_from_workspace(
            self.proposed_description.descriptor.name
        )
        self.proposed_description.update_strength_values()
        build_probability = temperature_adjust(
            self.proposed_description.total_strength, temperature
        )
        if build_probability < random.random():
            return Fizzle(FizzleReason.PROPOSED_STRUCTURE_TOO_WEAK)
        urgency = self.coderack.get_urgency_level_from_activation(
            self.proposed_description.total_strength
        )
        self.coderack.post(
            DescriptionBuilder(
                urgency_bin=urgency,
                coderack=self.coderack,
                slipnet=self.slipnet,
                workspace=self.workspace,
                proposed_description=self.proposed_description,
            )
        )
        return Finish()
