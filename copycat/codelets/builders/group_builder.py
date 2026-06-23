from copycat.codelets.builder import Builder
from copycat.workspace_objects import Group


class GroupBuilder(Builder):
    """A group builder tries to build the proposed group.
    It fights with competitors if necessary.
    """

    def __init__(
        self,
        urgency_bin: int,
        coderack: "Coderack",
        workspace: "Workspace",
        slipnet: "Slipnet",
        proposed_group: Group,
    ):
        super().__init__(
            urgency_bin=urgency_bin,
            coderack=coderack,
            workspace=workspace,
            slipnet=slipnet,
            proposed_structure=proposed_group,
        )
        self.proposed_group = proposed_group
