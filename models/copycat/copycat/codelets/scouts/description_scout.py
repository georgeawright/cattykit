from copycat.codelets.scout import Scout
from copycat.codelets.strength_testers import DescriptionStrengthTester
from copycat.slipnode import Slipnode
from copycat.workspace_object import WorkspaceObject
from copycat.workspace_structures.description import Description


class DescriptionScout(Scout):
    """A description scout codelet looks for evidence of a description.
    If possible, it makes a proposed description and posts a description strength tester.
    """

    def propose_description(
        self,
        chosen_object: WorkspaceObject,
        description_type: Slipnode,
        descriptor: Slipnode,
        temperature: float,
    ):
        proposed_description = Description(chosen_object, description_type, descriptor)
        self.slipnet.activate_node_from_workspace(descriptor.name)
        urgency_level = self.coderack.get_urgency_level_from_activation(
            self.slipnet.get_node_activation(description_type.name)
        )
        self.coderack.post(
            DescriptionStrengthTester(
                urgency_bin=urgency_level,
                coderack=self.coderack,
                slipnet=self.slipnet,
                workspace=self.workspace,
                proposed_description=proposed_description,
            ),
            temperature=temperature,
        )
