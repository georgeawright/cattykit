import json

from .codelets import (
    BottomUpBondScout,
    BottomUpCorrespondenceScout,
    ReplacementFinder,
)
from .coderack import Coderack
from .coderack_bin import CoderackBin
from .slipnet import Slipnet
from .workspace import Workspace
from .workspace_string import WorkspaceString
from .structures import Description, Group, Letter

DESCRIPTION_TESTERS = {
    # LENGTH
    "length_is_one": lambda x: isinstance(x, Group) and len(x) == 1,
    "length_is_two": lambda x: isinstance(x, Group) and len(x) == 2,
    "length_is_three": lambda x: isinstance(x, Group) and len(x) == 3,
    "length_is_four": lambda x: isinstance(x, Group) and len(x) == 4,
    "length_is_five": lambda x: isinstance(x, Group) and len(x) == 5,
    # STRING POSITION
    "is_leftmost": lambda x: not x.spans_whole_string and x.leftmost_in_string,
    "is_rightmost": lambda x: not x.spans_whole_string and x.rightmost_in_string,
    "is_middle": lambda x: (
        x.ungrouped_left_neighbor is not None
        and x.ungrouped_right_neighbor is not None
        and x.ungrouped_left_neighbor.leftmost_in_string
        and x.ungrouped_right_neighbor.rightmost_in_string
    ),
    "is_single": lambda x: isinstance(x, Letter) and x.spans_whole_string,
    "is_whole": lambda x: isinstance(x, Group) and x.spans_whole_string,
    # ALPHABETIC POSITION
    "is_first": lambda x: x.get_descriptor("letter_category") == "a",
    "is_last": lambda x: x.get_descriptor("letter_category") == "z",
    # OBJECT TYPE
    "is_letter_object": lambda x: isinstance(x, Letter),
    "is_group_object": lambda x: isinstance(x, Group),
}


class Copycat:
    def __init__(
        self,
        slipnet: Slipnet,
        coderack: Coderack,
        workspace: Workspace,
    ):
        self.slipnet = slipnet
        self.coderack = coderack
        self.workspace = workspace
        self.temperature = 1.0

    @classmethod
    def from_json(cls, slipnet_json_file: str, coderack_json_file: str):
        with open(slipnet_json_file) as f:
            slipnet_json = json.load(f)
        slipnet = Slipnet.from_json(slipnet_json, DESCRIPTION_TESTERS)
        with open(coderack_json_file) as f:
            coderack_json = json.load(f)
        coderack = Coderack.from_json(coderack_json)
        workspace = Workspace.setup()
        return cls(slipnet, coderack=coderack, workspace=workspace)

    def solve(self, string: str):
        """
        Solve a string analogy problem (e.g. "abc -> abd ==> ijk -> ?")
        """
        self._add_letters_to_workspace(string)
        self._add_initial_descriptions_to_workspace()
        self._post_intial_codelets()
        self.run()

    def _add_letters_to_workspace(self, string: str):
        """
        Initialize workspace with a problem (e.g. "abc -> abd ==> ijk -> ?")
        """
        initial_and_modified, target_and_answer = string.split("==>")
        initial_string, modified_string = initial_and_modified.split("->")
        target_string, answer_string = target_and_answer.split("->")
        answer_string = answer_string.split("?")[0]
        self.workspace.initial_string.letters = [
            Letter(
                string=self.workspace.initial_string,
                letter_category=self.slipnet[char],
                string_position=i,
            )
            for i, char in enumerate(initial_string.strip())
        ]
        self.workspace.modified_string.letters = [
            Letter(
                string=self.workspace.modified_string,
                letter_category=self.slipnet[char],
                string_position=i,
            )
            for i, char in enumerate(modified_string.strip())
        ]
        self.workspace.target_string.letters = [
            Letter(
                string=self.workspace.target_string,
                letter_category=self.slipnet[char],
                string_position=i,
            )
            for i, char in enumerate(target_string.strip())
        ]
        self.workspace.answer_string.letters = [
            Letter(
                string=self.workspace.answer_string,
                letter_category=self.slipnet[char],
                string_position=i,
            )
            for i, char in enumerate(answer_string.strip())
        ]

    def _add_initial_descriptions_to_workspace(self):
        for string in [
            self.workspace.initial_string,
            self.workspace.modified_string,
            self.workspace.target_string,
        ]:
            for letter in string.letters:
                letter.add_description(
                    Description(
                        letter,
                        self.slipnet["object_category"],
                        self.slipnet["letter"],
                    )
                )
                letter.add_description(
                    Description(
                        letter,
                        self.slipnet["letter_category"],
                        letter.letter_category,
                    )
                )
            if len(string) > 1:
                string.letters[0].add_description(
                    Description(
                        string.letters[0],
                        self.slipnet["string_position_category"],
                        self.slipnet["leftmost"],
                    )
                )
                string.letters[-1].add_description(
                    Description(
                        string.letters[-1],
                        self.slipnet["string_position_category"],
                        self.slipnet["rightmost"],
                    )
                )
            else:
                string.letters[0].add_description(
                    Description(
                        string.letters[0],
                        self.slipnet["string_position_category"],
                        self.slipnet["single"],
                    )
                )
            if len(string) == 3:
                string.letters[1].add_description(
                    Description(
                        letter,
                        self.slipnet["string_position_category"],
                        self.slipnet["middle"],
                    )
                )

    def _post_intial_codelets(self):
        for _ in range(2 * len(self.workspace.objects)):
            self.coderack.post(
                BottomUpBondScout(urgency_bin=2),
                self.temperature,
            )
            self.coderack.post(
                ReplacementFinder(urgency_bin=2),
                self.temperature,
            )
            self.coderack.post(
                BottomUpCorrespondenceScout(urgency_bin=2),
                self.temperature,
            )

    def run(self):
        pass

    def update(self):
        """Update values of workspace structures and slipnet activations."""
        pass

    def step(self):
        """Run a single codelet."""

    def handle_snag(self):
        """If there is a snag in building the answer:
        - delete all proposed structures,
        - empty coderack,
        - raise and clamp temperature,
        - clamp activation of all descriptions of the offending object."""

    def delete_answer(self):
        pass
