from copycat.codelets.builder import Builder
from copycat.workspace_structures import Rule


class RuleBuilder(Builder):
    """A rule builder tries to build the proposed rule.
    It fights with competitors if necessary.
    """

    def __init__(
        self,
        urgency_bin: int,
        coderack: "Coderack",
        workspace: "Workspace",
        slipnet: "Slipnet",
        proposed_rule: Rule,
    ):
        super().__init__(
            urgency_bin=urgency_bin,
            coderack=coderack,
            workspace=workspace,
            slipnet=slipnet,
            proposed_structure=proposed_rule,
        )
        self.proposed_rule = proposed_rule
