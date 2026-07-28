from copycat.codelet import Codelet


class Builder(Codelet):
    """A builder codelet tries to build the proposed structure.
    It fights with competitors if necessary.
    """

    def __init__(
        self,
        urgency_bin: int,
        coderack: "Coderack",
        workspace: "Workspace",
        slipnet: "Slipnet",
        proposed_structure: "WorkspaceStructure",
    ):
        super().__init__(
            urgency_bin=urgency_bin,
            coderack=coderack,
            workspace=workspace,
            slipnet=slipnet,
        )
        self.proposed_structure = proposed_structure
