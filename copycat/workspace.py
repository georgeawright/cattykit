import random


class Workspace:
    def __init__(self, initial_string, target_string):
        """The workspace contains an initial string and a target string.
        These each contain objects (letters and groups), and bonds between objects.
        The workspace also contains correspondences between objects in the two strings
        and can contain a rule."""
        self.initial_string = initial_string
        self.target_string = target_string
        self.proposed_bonds = []
        self.proposed_correspondences = []
        self.proposed_groups = []
        self.bonds = []
        self.correspondences = []
        self.groups = []
        self.replacements = []
        self.rule = None
        self.slippages = []
        self.snag_structure_list = []

    @property
    def letters(self):
        return self.initial_string.letters + self.target_string.letters

    @property
    def objects(self):
        """Returns a list of objects (letters and groups of letters)"""
        return self.initial_string.objects + self.target_string.objects

    @property
    def structures(self):
        """Returns a list of structures (bonds, groups, correspondences, and rules"""
        structures = self.bonds + self.correspondences + self.groups
        return structures + [self.rule] if self.rule is not None else structures

    def contains_correspondence(self, correspondence) -> bool:
        """Returns True if the workspace contains the correspondence."""
        try:
            existing_correspondence = self.correspondences[
                correspondence.object_1.string_number
            ][correspondence.object_2.string_number]
        except IndexError:
            return False
        return True

    def contains_slippage(self, slippage) -> bool:
        """Returns True if the workspace contains the slippage."""
        return slippage in self.slippages

    def get_random_string(self):
        return random.choice([self.initial_string, self.target_string])

    def intra_string_unhappiness(self):
        """Returns average of intra-string unhappiness of objects in the workspace
        weighted by the relative importance of each object in its string."""
        pass

    def inter_string_unhappiness(self):
        """Returns average of inter-string unhappiness of objects in the workspace
        weighted by the relative importance of each object in its string."""
        pass

    def total_unhappiness(self):
        """Returns average of the total unhappiness of objects in the workspace
        weighted by the relative importance of each object in its string."""
        pass
