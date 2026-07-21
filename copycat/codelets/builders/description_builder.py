from copycat.codelets.builder import Builder
from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
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

    def run(self, temperature: float) -> CodeletResult:
        argument_object = self.proposed_description.argument_object
        if argument_object not in self.workspace.objects:
            return Fizzle(FizzleReason.OBJECTS_NO_LONGER_EXIST)
        descriptor = self.proposed_description.descriptor
        facet = self.proposed_description.facet
        self.slipnet.activate_node_from_workspace(descriptor.name)
        self.slipnet.activate_node_from_workspace(facet.name)
        if argument_object.has_description(self.proposed_description):
            return Fizzle(FizzleReason.STRUCTURE_ALREADY_EXISTS)
        argument_object.add_description(self.proposed_description)
        return Finish()
