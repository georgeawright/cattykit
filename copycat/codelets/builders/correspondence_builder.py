from copycat.codelets.builder import Builder
from copycat.workspace_structures import Correspondence


class CorrespondenceBuilder(Builder):
    """A correspondence builder tries to build the proposed correspondence.
    It fights with competitors if necessary."""

    def __init__(
        self,
        urgency_bin: int,
        coderack: "Coderack",
        workspace: "Workspace",
        slipnet: "Slipnet",
        proposed_correspondence: Correspondence,
        object_2_flipped: bool = False,
    ):
        super().__init__(
            urgency_bin=urgency_bin,
            coderack=coderack,
            workspace=workspace,
            slipnet=slipnet,
            proposed_structure=proposed_correspondence,
        )
        self.proposed_correspondence = proposed_correspondence
        self.object_2_flipped = object_2_flipped
