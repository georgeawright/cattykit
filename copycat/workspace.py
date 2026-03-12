from collections import defaultdict
import itertools
import random
from typing import Dict, List, Optional

from .tools import describe_count
from .workspace_string import WorkspaceString
from .structure import Structure
from .structures import Correspondence, Replacement, Rule


class Workspace:
    def __init__(
        self,
        initial_string: WorkspaceString,
        modified_string: WorkspaceString,
        target_string: WorkspaceString,
        answer_string: WorkspaceString,
    ):
        """
        The workspace contains:
        (e.g. abc -> abd ==> ijk -> ?)
        - an initial string (abc),
        - a modified string (abd),
        - a target string (ijk),
        - and an answer string (?).
        These each contain:
        - objects (letters and groups),
        - and bonds between objects.
        The workspace also contains
        - inter-string correspondences between objects
        - and can contain a rule.
        """
        self.initial_string = initial_string
        self.modified_string = modified_string
        self.target_string = target_string
        self.answer_string = answer_string
        self._proposed_correspondences: Dict[
            str, Dict[str, List[Correspondence]]
        ] = defaultdict(lambda: defaultdict(list))
        self._correspondences: Dict[str, Correspondence] = {}
        self.replacements: List[Replacement] = []
        self.rule: Optional[Rule] = None
        self.snag_structure_list: List[Structure] = []

    @classmethod
    def setup(cls):
        initial_string = WorkspaceString()
        modified_string = WorkspaceString()
        target_string = WorkspaceString()
        answer_string = WorkspaceString()
        return cls(initial_string, modified_string, target_string, answer_string)

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

    def choose_object(self, temperature, method):
        """Return an object probabilistically according to temperature and method."""
        weights = [temperature_adjust(method(obj), temperature) for obj in self.objects]
        return random.choices(self.objects, weights=weights, k=1)

    @property
    def letters_without_replacement(self) -> list:
        return [
            letter
            for letter in self.initial_string.letters
            if letter.replacement is None
        ]

    @property
    def ungrouped_objects(self) -> list:
        return [
            obj
            for obj in self.objects
            if not obj.spans_whole_string and obj.group is None
        ]

    @property
    def unbonded_objects(self) -> list:
        return [
            obj
            for obj in self.ungrouped_objects
            if (
                (obj.is_at_edge_of_string and len(obj.bonds) == 0)
                or (not obj.is_at_edge_of_string and len(obj.bonds) < 2)
            )
        ]

    @property
    def ungrouped_bonds(self) -> list:
        return [
            bond
            for bond in self.bonds
            if bond.from_node.group is None or bond.to_node.group is None
        ]

    @property
    def uncorresponded_objects(self) -> list:
        return [obj for obj in self.objects if obj.correspondence is None]

    @property
    def rough_number_of_letters_without_replacement(self):
        return describe_count(len(self.letters_without_replacement))

    @property
    def rough_number_of_ungrouped_objects(self):
        return describe_count(len(self.ungrouped_objects))

    @property
    def rough_number_of_unbonded_objects(self):
        return describe_count(len(self.unbonded_objects))

    @property
    def rough_number_of_uncorresponded_objects(self):
        return describe_count(len(self.uncorresponded_objects))

    @property
    def rough_importance_of_uncorresponded_objects(self):
        max_importance = max(
            [obj.relative_importance for obj in self.uncorresponded_objects] + [0]
        )
        return describe_count(round(max_importance * 10, 0))

    @property
    def slippages(self) -> list:
        return list(
            itertools.chain.from_iterable(
                [correspondence.slippages for correspondence in self.correspondences]
            )
        )

    def intra_string_unhappiness(self):
        """Returns average of intra-string unhappiness of objects in the workspace
        weighted by the relative importance of each object in its string."""
        return min(
            1,
            sum(
                [
                    obj.relative_importance * obj.intra_string_unhappiness
                    for obj in self.objects
                ]
            )
            # divided by 2 as there a 2 strings each with total unhappiness  1
            / 2,
        )

    def inter_string_unhappiness(self):
        """Returns average of inter-string unhappiness of objects in the workspace
        weighted by the relative importance of each object in its string."""
        return min(
            1,
            sum(
                [
                    obj.relative_importance * obj.inter_string_unhappiness
                    for obj in self.objects
                ]
            )
            # divided by 2 as there a 2 strings each with total unhappiness  1
            / 2,
        )

    def total_unhappiness(self):
        """Returns average of the total unhappiness of objects in the workspace
        weighted by the relative importance of each object in its string."""
        return min(
            1,
            sum(
                [
                    obj.relative_importance * obj.total_unhappiness
                    for obj in self.objects
                ]
            )
            # divided by 2 as there a 2 strings each with total unhappiness  1
            / 2,
        )
