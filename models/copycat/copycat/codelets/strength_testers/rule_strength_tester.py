from copycat.codelets.strength_tester import StrengthTester
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
