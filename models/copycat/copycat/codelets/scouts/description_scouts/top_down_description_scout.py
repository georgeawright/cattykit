from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.codelets.scouts import DescriptionScout
from copycat.slipnode import Slipnode
from copycat.tools import select_item_from_list


class TopDownDescriptionScout(DescriptionScout):
    """Chooses an object probabilistically by total salience.
    Checks if the the object fits any descriptions in the description type's instances.
    Proposes a description based on the property and posts a description strength tester
    with urgency a function of the descriptor's activation."""

    def __init__(
        self,
        urgency_bin: int,
        coderack: "Coderack",
        slipnet: "Slipnet",
        workspace: "Workspace",
        description_type: Slipnode,
    ):
        super().__init__(
            urgency_bin=urgency_bin,
            coderack=coderack,
            workspace=workspace,
            slipnet=slipnet,
        )
        self.description_type = description_type

    def run(self, temperature: float) -> CodeletResult:
        chosen_object = self.workspace.choose_object(
            temperature, lambda x: x.total_salience
        )
        if chosen_object is None:
            return Fizzle(FizzleReason.NO_OBJECTS)
        possible_descriptors = self.description_type.get_possible_descriptors(
            chosen_object
        )
        if not possible_descriptors:
            return Fizzle(FizzleReason.NO_POSSIBLE_DESCRIPTORS)
        weights = [
            self.slipnet.get_node_activation(descriptor.name)
            for descriptor in possible_descriptors
        ]
        chosen_descriptor = select_item_from_list(
            possible_descriptors, weights
        )
        self.propose_description(
            chosen_object,
            self.description_type,
            chosen_descriptor,
            temperature=temperature,
        )
        return Finish()
