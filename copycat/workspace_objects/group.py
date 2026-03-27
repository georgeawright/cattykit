from copycat.workspace_object import WorkspaceObject


class Group(WorkspaceObject):
    def __init__(self):
        self.bond_descriptions = []
        self.objects = []

    def __len__(self):
        return len(self.objects)

    def __eq__(self, other):
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
        pass

    @property
    def rightmost_letter(self):
        pass

    def is_leftmost_in_string(self) -> bool:
        pass

    def is_rightmost_in_string(self) -> bool:
        pass

    def get_left_neighbour(self):
        pass

    def get_right_neighbour(self):
        pass
