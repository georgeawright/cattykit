from copycat.codelets.strength_tester import StrengthTester


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
        object_2_flipped=False,
    ):
        super().__init__(
            urgency_bin, coderack, slipnet, workspace, proposed_correspondence
        )
        self.proposed_correspondence = proposed_correspondence
        self.object_2_flipped = object_2_flipped

    def run(self, temperature: float):
        pass
