import json

from .coderack import Coderack
from .coderack_bin import CoderackBin
from .slipnet import Slipnet
from .workspace import Workspace
from .workspace_string import WorkspaceString
from .structures import Group, Letter

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

    @classmethod
    def from_json(cls, slipnet_json_file: str, coderack_json_file: str):
        with open("slipnet.json") as f:
            slipnet_json = json.load(f)
        slipnet = Slipnet.from_json(slipnet_json, DESCRIPTION_TESTERS)
        with open("coderack.json") as f:
            coderack_json = json.load(f)
        coderack = Coderack.from_json(coderack_json)
        workspace = Workspace.setup()
        return cls(slipnet, coderack=coderack, workspace=workspace)

    def solve(self, string: str):
        """
        Initialize workspace with a problem (e.g. "abc -> abd ==> ijk -> ?")
        """
        initial_string, rest = string.split("->")
        modified_string, rest = rest.split("==>")
        target_string, rest = rest.split("->")
        answer_string, _ = rest.split("?")
        raise NotImplementedError

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
