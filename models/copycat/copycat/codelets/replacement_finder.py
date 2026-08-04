import random

from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.codelet import Codelet
from copycat.workspace_objects import Letter
from copycat.workspace_structures import ExtrinsicDescription, Replacement


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

    def run(self, temperature: float) -> CodeletResult:
        initial_letter = random.choice(self.workspace.initial_string.letters)
        if initial_letter.replacement is not None:
            return Fizzle(FizzleReason.LETTER_ALREADY_HAS_REPLACEMENT)
        modified_letter = self.workspace.modified_string.letters[
            initial_letter.left_position
        ]
        initial_letter_category = initial_letter.get_descriptor(
            self.slipnet["letter_category"]
        )
        modified_letter_category = modified_letter.get_descriptor(
            self.slipnet["letter_category"]
        )
        if initial_letter_category != modified_letter_category:
            initial_letter.is_changed_letter = True
            change_relation = self.slipnet.get_label_node(
                initial_letter_category, modified_letter_category
            )
            if change_relation is not None:
                modified_letter.extrinsic_descriptions.append(
                    ExtrinsicDescription(
                        change_relation, self.slipnet["letter_category"], initial_letter
                    )
                )
        replacement = Replacement(initial_letter, modified_letter)
        self.workspace.replacements.append(replacement)
        initial_letter.replacement = replacement
        return Finish()
