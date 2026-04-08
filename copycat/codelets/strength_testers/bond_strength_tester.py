from copycat.codelets.strength_tester import StrengthTester
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

    def run(self, temperature: float):
        raise NotImplementedError
