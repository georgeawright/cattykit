from copycat.codelets.strength_tester import StrengthTester
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
