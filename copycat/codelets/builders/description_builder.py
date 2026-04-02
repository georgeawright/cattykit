from copycat.codelets.builder import Builder
from copycat.workspace_structures import Description


class DescriptionBuilder(Builder):
    """A description builder tries to build the proposed description.
    It fizzles if the object no longer exists or the description already exists."""

    def __init__(
        self,
        urgency_bin: int,
        coderack: "Coderack",
        workspace: "Workspace",
        slipnet: "Slipnet",
        proposed_description: Description,
    ):
        super().__init__(
            urgency_bin=urgency_bin,
            coderack=coderack,
            workspace=workspace,
            slipnet=slipnet,
            proposed_structure=proposed_description,
        )
        self.proposed_description = proposed_description
