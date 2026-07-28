from copycat.codelet import Codelet


class StrengthTester(Codelet):
    """A strength tester codelet calculates the strength of a proposed structure.
    It probabilistically posts a builder codelet with urgency a function of strength.
    """

    def __init__(
        self,
        urgency_bin: int,
        coderack,
        slipnet,
        workspace,
        proposed_structure,
    ):
        super().__init__(
            urgency_bin=urgency_bin,
            coderack=coderack,
            slipnet=slipnet,
            workspace=workspace,
        )
        self.proposed_structure = proposed_structure
