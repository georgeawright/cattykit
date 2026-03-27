from typing import List

from copycat.slipnet import Slipnode
from copycat.workspace_object import WorkspaceObject


class Group(WorkspaceObject):
    def __init__(
        self,
        string: "WorkspaceString",
        left_position: int,
        right_position: int,
        group_category: Slipnode,
        direction_category: Slipnode,
    ):
        super().__init__(string, left_position, right_position)
        self.group_category = group_category
        self.direction_category = direction_category
        self.bond_descriptions: List = []
        self.objects: List[WorkspaceObject] = []

    def __len__(self):
        return len(self.objects)

    def __eq__(self, other):
        if not isinstance(other, Group):
            return False
        return (
            self.left_position,
            self.right_position,
            self.group_category,
            self.direction_category,
        ) == (
            other.left_position,
            other.right_position,
            other.group_category,
            other.direction_category,
        )

    def __contains__(self):
        pass

    @property
    def letters(self):
        letters = []
        for o in self.objects:
            letters += o.letters

    @property
    def leftmost_letter(self):
        # TODO
        pass

    @property
    def rightmost_letter(self):
        # TODO
        pass

    def has_recursive_group_member(self, other_object) -> bool:
        if self == other_object:
            return True
        for o in self.objects:
            if o.has_recursive_group_member(other_object):
                return True
        return False

    def is_leftmost_in_string(self) -> bool:
        # TODO
        pass

    def is_rightmost_in_string(self) -> bool:
        # TODO
        pass

    def get_left_neighbour(self):
        # TODO
        pass

    def get_right_neighbour(self):
        # TODO
        pass
