import random

from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.codelet import Codelet
from copycat.workspace_objects_and_structures import (
    ExtrinsicDescription,
    Letter,
    Replacement,
)


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
        self.initial_letter = random.choice(self.workspace.initial_string.letters)
        if self.initial_letter.replacement is not None:
            return Fizzle(FizzleReason.LETTER_ALREADY_HAS_REPLACEMENT)
        self.modified_letter = self.workspace.modified_string.letters[
            self.initial_letter.left_position
        ]
        self.initial_letter_category = self.initial_letter.get_descriptor(
            self.slipnet["letter_category"]
        )
        self.modified_letter_category = self.modified_letter.get_descriptor(
            self.slipnet["letter_category"]
        )
        if self.initial_letter_category != self.modified_letter_category:
            self.initial_letter.is_changed_letter = True
            self.change_relation = self.slipnet.get_label_node(
                self.initial_letter_category, self.modified_letter_category
            )
            if self.change_relation is not None:
                self.modified_letter.extrinsic_descriptions.append(
                    ExtrinsicDescription(
                        self.change_relation,
                        self.slipnet["letter_category"],
                        self.initial_letter,
                    )
                )
        self.replacement = Replacement(self.initial_letter, self.modified_letter)
        self.workspace.add_replacement(self.replacement)
        self.initial_letter.replacement = self.replacement
        return Finish()
