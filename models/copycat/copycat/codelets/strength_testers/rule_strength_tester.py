import random

from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.codelets.builders import RuleBuilder
from copycat.codelets.strength_tester import StrengthTester
from copycat.tools import temperature_adjust_probability
from copycat.workspace_structures import Rule


class RuleStrengthTester(StrengthTester):
    """A rule strength tester calculates the strength of a rule.
    It probabilistically posts a rule builder with urgency a function of strength.
    """

    def __init__(
        self,
        urgency_bin: int,
        coderack: "Coderack",
        slipnet: "Slipnet",
        workspace: "Workspace",
        proposed_rule: Rule,
    ):
        super().__init__(
            urgency_bin=urgency_bin,
            coderack=coderack,
            slipnet=slipnet,
            workspace=workspace,
            proposed_structure=proposed_rule,
        )
        self.proposed_rule = proposed_rule

    def run(self, temperature: float) -> CodeletResult:
        self.proposed_rule.update_strength_values()
        build_probability = temperature_adjust_probability(
            self.proposed_rule.total_strength, temperature
        )
        if build_probability < random.random():
            return Fizzle(FizzleReason.PROPOSED_STRUCTURE_TOO_WEAK)
        urgency_bin = self.coderack.get_urgency_level_from_activation(
            self.proposed_rule.total_strength
        )
        self.coderack.post(
            RuleBuilder(
                urgency_bin=urgency_bin,
                coderack=self.coderack,
                slipnet=self.slipnet,
                workspace=self.workspace,
                proposed_rule=self.proposed_rule,
            ),
            temperature=temperature,
        )
        return Finish()
