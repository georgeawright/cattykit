from collections import defaultdict
import itertools
import random
from typing import Dict, List, Optional

from .codelets import (
    BottomUpBondScout,
    BottomUpCorrespondenceScout,
    BottomUpDescriptionScout,
    Breaker,
    ImportantObjectCorrespondenceScout,
    ReplacementFinder,
    RuleScout,
    RuleTranslator,
    WholeStringGroupScout,
)
from .tools import describe_count
from .workspace_string import WorkspaceString
from .workspace_object import WorkspaceObject
from .workspace_structure import WorkspaceStructure
from .workspace_structures import Correspondence, Replacement, Rule


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
        self.unreplaced_objects: List[WorkspaceObject] = []
        self.replacements: List[Replacement] = []
        self.rule: Optional[Rule] = None
        self.snag_structure_list: List[WorkspaceStructure] = []

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
        return self.initial_string.bonds + self.target_string.bonds

    @property
    def proposed_groups(self):
        return self.initial_string.proposed_groups + self.target_string.proposed_groups

    @property
    def groups(self):
        return self.initial_string.groups + self.target_string.groups

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

    def update(self):
        """Update values for structures and objects."""
        self._update_strength_values()
        self._update_object_values()
        self.initial_string.update_relative_importances()
        self.target_string.update_relative_importances()
        self.initial_string.update_intra_string_unhappiness()
        self.target_string.update_intra_string_unhappiness()

    def _update_strength_values(self):
        for structure in self.structures:
            structure.update_strength_values()

    def _update_object_values(self):
        for obj in self.objects:
            obj.update_values()

    def add_proposed_correspondence(self, correspondence):
        """Add to a maintained list of proposed correspondences between two objects."""
        from_id = correspondence.from_object.id
        to_id = correspondence.to_object.id
        self._proposed_correspondences[from_id][to_id].append(correspondence)

    def delete_proposed_correspondence(self, correspondence):
        """Delete from a maintained list of proposed correspondences between two objects."""
        from_id = correspondence.from_object.id
        to_id = correspondence.to_object.id
        self._proposed_correspondences[from_id][to_id].remove(correspondence)

    def add_correspondence(self, correspondence):
        """Add the only correspondence between two objects."""
        self._correspondences[correspondence.from_object.id] = correspondence

    def break_correspondence(self, correspondence):
        correspondence.from_object.correspondence = None
        correspondence.to_object.correspondence = None
        self.delete_correspondence(correspondence)

    def delete_correspondence(self, correspondence):
        """Delete the only correspondence between two objects."""
        self._correspondences[correspondence.from_object.id] = None

    def contains_correspondence(self, correspondence) -> bool:
        """Returns True if the workspace contains the correspondence."""
        try:
            existing_correspondence = self._correspondences[
                correspondence.from_object.id
            ]
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
            if bond.from_object.group is None or bond.to_object.group is None
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

    def get_bottom_up_codelets(self, temperature: float) -> List["Codelet"]:
        codelets = []
        if self._post_codelet_probability("description", temperature) > random.random():
            for i in range(self._number_of_codelets_to_post("description")):
                codelets.append(BottomUpDescriptionScout(urgency_bin=2))
        if self._post_codelet_probability("bond", temperature) > random.random():
            for _ in range(self._number_of_codelets_to_post("bond")):
                codelets.append(BottomUpBondScout(urgency_bin=2))
        if self._post_codelet_probability("group", temperature) > random.random():
            for _ in range(self._number_of_codelets_to_post("group")):
                codelets.append(WholeStringGroupScout(urgency_bin=2))
        if self._post_codelet_probability("replacement", temperature) > random.random():
            for _ in range(self._number_of_codelets_to_post("replacement")):
                codelets.append(ReplacementFinder(urgency_bin=2))
        if (
            self._post_codelet_probability("correspondence", temperature)
            > random.random()
        ):
            for _ in range(self._number_of_codelets_to_post("correspondence")):
                codelets.append(BottomUpCorrespondenceScout(urgency_bin=2))
                codelets.append(ImportantObjectCorrespondenceScout(urgency_bin=2))
        if self._post_codelet_probability("rule", temperature) > random.random():
            for _ in range(self._number_of_codelets_to_post("rule")):
                codelets.append(RuleScout(urgency_bin=2))
        if (
            self._post_codelet_probability("translated-rule", temperature)
            > random.random()
        ):
            for _ in range(self._number_of_codelets_to_post("translated-rule")):
                urgency_bin = 2 if self.temperature > 25 else 7
                codelets.append(RuleTranslator(urgency_bin=urgency_bin))
        codelets.append(Breaker(urgency_bin=0))
        return codelets

    def _post_codelet_probability(
        self, structure_category: str, temperature: float
    ) -> float:
        """For a given structure-category (e.g., description, or bond),
        returns a probability to use in deciding whether codelets looking
        for this type of structure should be posted.
        """
        if structure_category == "description":
            probability = temperature**2
        elif structure_category == "bond":
            probability = self.intra_string_unhappiness()
        elif structure_category == "group":
            probability = self.intra_string_unhappiness()
        elif structure_category == "replacement":
            probability = 1 if self.unreplaced_objects else 0
        elif structure_category == "correspondence":
            probability = self.inter_string_unhappiness()
        elif structure_category == "rule":
            probability = 1 if self.rule is None else self.rule.total_weakness
        elif structure_category == "translated-rule":
            probability = 1 if self.rule else 0
        return probability

    def _number_of_codelets_to_post(self, structure_category: str) -> int:
        """For a given structure-category (e.g., description, or bond),
        returns the number of codelets looking for this type of structure
        that should be posted.
        """
        if structure_category == "description":
            number = 1
        elif structure_category == "bond":
            number = {
                "few": 1,
                "medium": 2,
                "many": 3,
            }[self.rough_number_of_unrelated_objects]
        elif structure_category == "group":
            if not self.bonds:
                number = 0
            else:
                number = {
                    "few": 1,
                    "medium": 2,
                    "many": 3,
                }[self.rough_number_of_ungrouped_objects]
        elif structure_category == "replacement":
            if self.rule:
                number = 0
            else:
                number = {
                    "few": 1,
                    "medium": 2,
                    "many": 3,
                }[self.rough_number_of_unreplaced_objects]
        elif structure_category == "correspondence":
            number = {
                "few": 1,
                "medium": 3,
                "many": 3,
            }[self.rough_number_of_uncorresponded_objects]
        elif structure_category == "rule":
            number = 2
        elif structure_category == "translated-rule":
            number = 0 if not self.rule else 1
        return number
