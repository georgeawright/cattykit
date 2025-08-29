from copycat.structures.object import Object


class Letter(Object):
    def __init__(self, string, letter_category, string_position):
        super.__init__(object_id, string, string_position, string_position)
        self.letter_category = letter_category

    def __len__(self):
        return 1

    @property
    def letters(self):
        return [self]
