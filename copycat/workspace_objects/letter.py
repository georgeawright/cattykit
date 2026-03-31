from copycat.workspace_object import WorkspaceObject


class Letter(WorkspaceObject):
    def __init__(self, string, letter_category, string_position):
        super().__init__(string, string_position, string_position)
        self.letter_category = letter_category

    def __len__(self):
        return 1

    @property
    def letters(self):
        return [self]

    def _is_distinguished_by(self, descriptor: "Slipnode") -> bool:
        other_objects = [o for o in self.string.letters if o != self]
        other_descriptors = []
        for o in other_objects:
            other_descriptors += [d.descriptor for d in o.descriptions]
        return descriptor not in other_descriptors
