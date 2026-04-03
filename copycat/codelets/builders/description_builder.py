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

    def run(self, temperature: float):
        argument_object = self.proposed_description.argument_object
        if argument_object not in self.workspace.objects:
            return
        descriptor = self.proposed_description.descriptor
        facet = self.proposed_description.facet
        self.slipnet.activate_node_from_workspace(descriptor.name)
        self.slipnet.activate_node_from_workspace(facet.name)
        if argument_object.has_description(self.proposed_description):
            return
        if self.proposed_description.is_bond_description():
            argument_object.bond_descriptions.append(self.proposed_description)
        else:
            argument_object.descriptions.append(self.proposed_description)
