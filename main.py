import json

from copycat import Sliplink, Slipnet, Slipnode
from copycat.structures import Group, Letter

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


def main():
    with open("slipnet.json") as f:
        slipnet_json = json.load(f)
    slipnet = Slipnet.from_json(slipnet_json, DESCRIPTION_TESTERS)


if __name__ == "__main__":
    main()
