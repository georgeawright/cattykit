from collections import defaultdict
import random


class Workspace:
    def __init__(self, initial_string, target_string):
        """The workspace contains an initial string and a target string.
        These each contain objects (letters and groups), and bonds between objects.
        The workspace also contains correspondences between objects in the two strings
        and can contain a rule."""
        self.initial_string = initial_string
        self.target_string = target_string
        self._proposed_correspondences = defaultdict(lambda: defaultdict(list))
        self._correspondences = {}
        self.replacements = []
        self.rule = None
        self.slippages = []
        self.snag_structure_list = []

    @property
    def letters(self):
        return self.initial_string.letters + self.target_string.letters

    @property
    def objects(self):
        return self.initial_string.objects + self.target_string.objects

    @property
    def proposed_bonds(self):
        return self.initial_string.proposed_bonds + self.target_string.proposed_bonds

    @property
    def bonds(self):
        return self.intial_string.bonds + self.target_string.bonds

    @property
    def proposed_groups(self):
        return self.intial_string.proposed_groups + self.target_string.proposed_groups

    @property
    def groups(self):
        return self.intial_string.groups + self.target_string.groups

    @property
    def proposed_correspondences(self):
        unique_correspondences = []
        added = set()
        for from_index, correspondences in self._proposed_correspondences.items():
            for to_index, correspondence_list in correspondences.items():
                for correspondence in correspondence_list:
                    if correspondence in added:
                        continue
                    unique_correspondences.append(correspondence)
                    added.add(correspondence)
        return unique_correspondences

    @property
    def correspondences(self):
        return [
            correspondence
            for left_index, correspondence in self._correspondences.items()
            if correspondence is not None
        ]

    @property
    def structures(self):
        """Returns a list of structures (bonds, groups, correspondences, and rules"""
        structures = self.bonds + self.correspondences + self.groups
        if self.rule is not None:
            structures.append(self.rule)
        return structures

    def add_proposed_correspondence(self, correspondence):
        """Add to a maintained list of proposed correspondences between two nodes."""
        from_id = correspondence.from_node.id
        to_id = correspondence.to_node.id
        self._proposed_correspondences[from_id][to_id].append(correspondence)

    def delete_proposed_correspondence(self, correspondence):
        """Delete from a maintained list of proposed correspondences between two nodes."""
        from_id = correspondence.from_node.id
        to_id = correspondence.to_node.id
        self._proposed_correspondences[from_id][to_id].remove(correspondence)

    def add_correspondence(self, correspondence):
        """Add the only correspondence between two nodes."""
        self._correspondences[correspondence.from_node.id] = correspondence

    def delete_correspondence(self, correspondence):
        """Delete the only correspondence between two nodes."""
        self._correspondences[correspondence.from_node.id] = None

    def contains_correspondence(self, correspondence) -> bool:
        """Returns True if the workspace contains the correspondence."""
        try:
            existing_correspondence = self._correspondences[correspondence.from_node.id]
        except KeyError:
            return False
        return existing_correspondence == correspondence

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
