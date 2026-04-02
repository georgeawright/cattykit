from copycat.codelets.strength_tester import StrengthTester


class DescriptionStrengthTester(StrengthTester):
    """A description strength tester calculates the strength of a proposed description.
    It probabilistically posts a description builder with urgency a function of strength.
    """

    def __init__(
        self,
        urgency_bin: int,
        coderack,
        slipnet,
        workspace,
        proposed_description,
    ):
        super().__init__(
            urgency_bin=urgency_bin,
            coderack=coderack,
            slipnet=slipnet,
            workspace=workspace,
            proposed_structure=proposed_description,
        )
        self.proposed_description = proposed_description
