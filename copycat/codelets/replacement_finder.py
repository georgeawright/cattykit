from copycat.codelet import Codelet


class ReplacementFinder(Codelet):
    """Chooses a letter at random in the the initial string.
    If it is the changed letter, it marks it as such
    and adds a description of the change if there is one."""

    def __init__(
        self,
        urgency_bin: int,
        coderack: "Coderack",
        workspace: "Workspace",
        slipnet: "Slipnet",
    ):
        super().__init__(
            urgency_bin=urgency_bin,
            coderack=coderack,
            workspace=workspace,
            slipnet=slipnet,
        )
