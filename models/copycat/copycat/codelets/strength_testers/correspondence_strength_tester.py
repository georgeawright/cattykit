import random

from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.codelets.builders.correspondence_builder import CorrespondenceBuilder
from copycat.codelets.strength_tester import StrengthTester
from copycat.tools import temperature_adjust


class CorrespondenceStrengthTester(StrengthTester):
    """A correspondence strength tester calculates the strength of a correspondence.
    It probabilistically posts a correspondence builder with urgency a function of strength.
    """

    def __init__(
        self,
        urgency_bin,
        coderack,
        slipnet,
        workspace,
        proposed_correspondence,
        target_flipped=False,
    ):
        super().__init__(
            urgency_bin, coderack, slipnet, workspace, proposed_correspondence
        )
        self.proposed_correspondence = proposed_correspondence
        self.target_flipped = target_flipped

    def run(self, temperature: float) -> CodeletResult:
        if self.proposed_correspondence.source not in self.workspace.objects:
            return Fizzle(FizzleReason.OBJECTS_NO_LONGER_EXIST)
        if (
            self.proposed_correspondence.target not in self.workspace.objects
            and not (
                self.target_flipped
                and self.proposed_correspondence.target.get_flipped_version()
                in self.workspace.objects
            )
        ):
            return Fizzle(FizzleReason.OBJECTS_NO_LONGER_EXIST)
        self.proposed_correspondence.update_strength_values()
        build_probability = temperature_adjust(
            self.proposed_correspondence.total_strength, temperature
        )
        if random.random() > build_probability:
            self.workspace.delete_proposed_correspondence(self.proposed_correspondence)
            return Fizzle(FizzleReason.PROPOSED_STRUCTURE_TOO_WEAK)
        for mapping in self.proposed_correspondence.concept_mappings:
            self.slipnet.activate_node_from_workspace(mapping.description_type_1)
            self.slipnet.activate_node_from_workspace(mapping.descriptor_1)
            self.slipnet.activate_node_from_workspace(mapping.description_type_2)
            self.slipnet.activate_node_from_workspace(mapping.descriptor_2)
        urgency = self.proposed_correspondence.total_strength
        urgency_bin = self.coderack.get_urgency_level_from_activation(urgency)
        self.coderack.post(
            CorrespondenceBuilder(
                urgency_bin=urgency_bin,
                coderack=self.coderack,
                slipnet=self.slipnet,
                workspace=self.workspace,
                proposed_correspondence=self.proposed_correspondence,
                target_flipped=self.target_flipped,
            ),
            temperature=temperature,
        )
        return Finish()
