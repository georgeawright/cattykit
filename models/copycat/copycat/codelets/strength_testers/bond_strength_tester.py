import random

from copycat.codelets.builders import BondBuilder
from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.codelets.strength_tester import StrengthTester
from copycat.tools import temperature_adjust
from copycat.workspace_structures.bond import Bond


class BondStrengthTester(StrengthTester):
    """A bond strength tester calculates the strength of a bond.
    It probabilistically posts a bond builder with urgency a function of strength.
    """

    def __init__(
        self,
        urgency_bin: int,
        coderack: "Coderack",
        slipnet: "Slipnet",
        workspace: "Workspace",
        proposed_bond: Bond,
    ):
        super().__init__(
            urgency_bin=urgency_bin,
            coderack=coderack,
            slipnet=slipnet,
            workspace=workspace,
            proposed_structure=proposed_bond,
        )
        self.proposed_bond = proposed_bond

    def run(self, temperature: float) -> CodeletResult:
        self.proposed_bond.update_strength_values()
        build_probability = temperature_adjust(
            self.proposed_bond.total_strength, temperature
        )
        if build_probability < random.random():
            self.proposed_bond.string.delete_proposed_bond(self.proposed_bond)
            return Fizzle(FizzleReason.PROPOSED_STRUCTURE_TOO_WEAK)
        self.slipnet.activate_node_from_workspace(
            self.proposed_bond.source_descriptor.name
        )
        self.slipnet.activate_node_from_workspace(
            self.proposed_bond.target_descriptor.name
        )
        self.slipnet.activate_node_from_workspace(self.proposed_bond.bond_facet.name)
        urgency = self.coderack.get_urgency_level_from_activation(
            self.proposed_bond.total_strength
        )
        self.coderack.post(
            BondBuilder(
                urgency_bin=urgency,
                coderack=self.coderack,
                slipnet=self.slipnet,
                workspace=self.workspace,
                proposed_bond=self.proposed_bond,
            ),
            temperature=temperature,
        )
        return Finish()
