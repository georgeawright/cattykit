from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
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
        to_object_flipped: bool = False,
    ):
        super().__init__(
            urgency_bin=urgency_bin,
            coderack=coderack,
            workspace=workspace,
            slipnet=slipnet,
            proposed_structure=proposed_correspondence,
        )
        self.proposed_correspondence = proposed_correspondence
        self.to_object_flipped = to_object_flipped

    def run(self, temperature: float) -> "CodeletResult":
        if self.proposed_correspondence.from_object not in self.workspace.objects:
            return Fizzle(FizzleReason.OBJECTS_NO_LONGER_EXIST)
        if (
            self.proposed_correspondence.to_object not in self.workspace.objects
            and not (
                self.to_object_flipped
                and self.proposed_correspondence.to_object.get_flipped_version()
                in self.workspace.objects
            )
        ):
            return Fizzle(FizzleReason.OBJECTS_NO_LONGER_EXIST)
