from copycat.codelets.scout import Scout
from copycat.codelets.strength_testers import DescriptionStrengthTester
from copycat.slipnode import Slipnode
from copycat.workspace_objects_and_structures import Description, WorkspaceObject


class DescriptionScout(Scout):
    """A description scout codelet looks for evidence of a description.
    If possible, it makes a proposed description and posts a description strength tester.
    """

    def propose_description(self, temperature: float) -> None:
        self.proposed_description = Description(
            self.chosen_object, self.description_type, self.chosen_descriptor
        )
        self.chosen_object.string.add_proposed_description(self.proposed_description)
        self.slipnet.activate_node_from_workspace(self.chosen_descriptor.name)
        urgency_level = self.coderack.get_urgency_level_from_activation(
            self.slipnet.get_node_activation(self.description_type.name)
        )
        self.coderack.post(
            DescriptionStrengthTester(
                urgency_bin=urgency_level,
                coderack=self.coderack,
                slipnet=self.slipnet,
                workspace=self.workspace,
                proposed_description=self.proposed_description,
            ),
            temperature=temperature,
        )
