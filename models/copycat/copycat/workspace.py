from collections import defaultdict
import itertools
import random
from typing import Dict, List, Optional

from cattykit.logging import ModelEvent, ModelLogger

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
from .tools import describe_count, select_item_from_list, temperature_adjust
from .workspace_string import WorkspaceString
from .workspace_object import WorkspaceObject
from .workspace_objects import Group
from .workspace_structure import WorkspaceStructure
from .workspace_structures import Bond, Correspondence, Description, Replacement, Rule


def _object_id(obj: object) -> str:
    return f"{type(obj).__name__.lower()}:{obj.hash_id}"


class Workspace:
    def __init__(
        self,
        initial_string: WorkspaceString,
        modified_string: WorkspaceString,
        target_string: WorkspaceString,
        answer_string: WorkspaceString,
        logger: ModelLogger | None = None,
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
        self.logger = logger
        for workspace_string in (
            initial_string,
            modified_string,
            target_string,
            answer_string,
        ):
            if workspace_string is not None:
                workspace_string.logger = logger
        self._proposed_correspondences: Dict[
            WorkspaceObject,
            Dict[WorkspaceObject, List[Optional[Correspondence]]],
        ] = defaultdict(lambda: defaultdict(list))
        self._correspondences: Dict[WorkspaceObject, Optional[Correspondence]] = {}
        self.replacements: List[Replacement] = []
        self.rule: Optional[Rule] = None
        self.translated_rule: Optional[Rule] = None
        self.snag_object: Optional[WorkspaceObject] = None

    def set_logger(self, logger: ModelLogger) -> None:
        """Attach the logger used to record workspace mutations."""
        self.logger = logger
        for workspace_string in (
            self.initial_string,
            self.modified_string,
            self.target_string,
            self.answer_string,
        ):
            if workspace_string is not None:
                workspace_string.logger = logger

    @classmethod
    def setup(cls):
        initial_string = WorkspaceString("initial")
        modified_string = WorkspaceString("modified")
        target_string = WorkspaceString("target")
        answer_string = WorkspaceString("answer")
        return cls(initial_string, modified_string, target_string, answer_string)

    @property
    def letters(self):
        return self.initial_string.letters + self.target_string.letters

    @property
    def objects(self):
        return self.initial_string.objects + self.target_string.objects

    @property
    def unreplaced_objects(self):
        """A list of all letters in the initial string that don't have a replacement."""
        return [
            letter for letter in self.initial_string.letters if not letter.replacement
        ]

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
        for source_index, correspondences in self._proposed_correspondences.items():
            for target_index, correspondence_list in correspondences.items():
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

    def all_replacements_found(self) -> bool:
        """True if all letters in the initial string have a replacement."""
        for letter in self.initial_string.letters:
            if letter.replacement is None:
                return False
        return True

    def update(self):
        """Update values for structures and objects."""
        self._update_strength_values()
        self._update_object_values()
        self.initial_string.update_relative_importances()
        self.target_string.update_relative_importances()
        self.initial_string.update_intra_string_unhappiness()
        self.target_string.update_intra_string_unhappiness()
        if self.logger is not None:
            for attribute, value in (
                ("intra_string_unhappiness", self.intra_string_unhappiness()),
                ("inter_string_unhappiness", self.inter_string_unhappiness()),
                ("total_unhappiness", self.total_unhappiness),
            ):
                self.logger.log(
                    ModelEvent.create(
                        "copycat",
                        "attribute_updated",
                        object_id="workspace",
                        attribute=attribute,
                        value=value,
                    )
                )

    def _update_strength_values(self):
        for structure in self.structures:
            structure.update_strength_values()
            if self.logger is not None:
                for attribute in (
                    "internal_strength",
                    "external_strength",
                    "total_strength",
                    "total_weakness",
                ):
                    self.logger.log(
                        ModelEvent.create(
                            "copycat",
                            "attribute_updated",
                            object_id=_object_id(structure),
                            attribute=attribute,
                            value=getattr(structure, attribute),
                        )
                    )

    def _update_object_values(self):
        for obj in self.objects:
            obj.update_values()
            if self.logger is not None:
                for attribute in (
                    "raw_importance",
                    "intra_string_unhappiness",
                    "inter_string_unhappiness",
                    "total_unhappiness",
                    "intra_string_salience",
                    "inter_string_salience",
                    "total_salience",
                ):
                    self.logger.log(
                        ModelEvent.create(
                            "copycat",
                            "attribute_updated",
                            object_id=_object_id(obj),
                            attribute=attribute,
                            value=getattr(obj, attribute),
                        )
                    )

    def add_proposed_correspondence(self, c: Correspondence):
        """Add to a maintained list of proposed correspondences between two objects."""
        self._proposed_correspondences[c.source][c.target].append(c)
        self._log_correspondence("correspondence_proposed", c)

    def delete_proposed_correspondence(self, c: Correspondence):
        """Delete from a maintained list of proposed correspondences between two objects."""
        self._proposed_correspondences[c.source][c.target].remove(c)
        self._log_correspondence("correspondence_destroyed", c)

    def add_correspondence(self, c: Correspondence):
        """Add the only correspondence between two objects."""
        self._correspondences[c.source] = c
        self._log_correspondence("correspondence_created", c)
        if self.logger is not None:
            for index, mapping in enumerate(c.concept_mappings):
                self._log(
                    "concept_mapping_created",
                    concept_mapping_id=f"correspondence:{c.hash_id}:mapping:{index}",
                    correspondence_id=f"correspondence:{c.hash_id}",
                    description_type_1=mapping.description_type_1.name,
                    description_type_2=mapping.description_type_2.name,
                    initial_descriptor=mapping.descriptor_1.name,
                    target_descriptor=mapping.descriptor_2.name,
                    label=None if mapping.label is None else mapping.label.name,
                )

    def break_correspondence(self, c: Correspondence):
        c.source.correspondence = None
        c.target.correspondence = None
        self.delete_correspondence(c)

    def delete_correspondence(self, c: Correspondence):
        """Delete the only correspondence between two objects."""
        self._correspondences[c.source] = None
        self._log_correspondence("correspondence_destroyed", c)

    def add_replacement(self, replacement: Replacement) -> None:
        """Add a replacement discovered between the initial and modified strings."""
        self.replacements.append(replacement)
        self._log(
            "replacement_created",
            replacement_id=f"replacement:{replacement.hash_id}",
            source_id=_object_id(replacement.source),
            target_id=_object_id(replacement.target),
        )

    def delete_translated_rule(self):
        self.translated_rule = None

    def delete_proposed_structures(self):
        for bond in self.proposed_bonds:
            bond.string.delete_proposed_bond(bond)
        for group in self.proposed_groups:
            group.string.delete_proposed_group(group)
        for correspondence in self.proposed_correspondences:
            self.delete_proposed_correspondence(correspondence)

    def _log_correspondence(self, kind: str, correspondence: Correspondence) -> None:
        if self.logger is None:
            return
        self._log(
            kind,
            correspondence_id=f"correspondence:{correspondence.hash_id}",
            source_id=_object_id(correspondence.source),
            target_id=_object_id(correspondence.target),
        )

    def _log(self, kind: str, **data: object) -> None:
        if self.logger is not None:
            self.logger.log(ModelEvent.create("copycat", kind, **data))

    def contains_group(self, g: Group) -> bool:
        """Returns True if the workspace contains an equivalent group."""
        for group in self.groups:
            if g.equates_to(group):
                return True
        return False

    def contains_correspondence(self, c: Correspondence) -> bool:
        """Returns True if the workspace contains the correspondence."""
        try:
            existing_correspondence = self._correspondences[c.source]
        except KeyError:
            return False
        if not existing_correspondence:
            return False
        return (
            existing_correspondence.source == c.source
            and existing_correspondence.target == c.target
        )

    def get_existing_correspondence(
        self, c: Correspondence
    ) -> Optional[Correspondence]:
        """Returns the existing correspondence between two objects if it exists."""
        try:
            existing_correspondence = self._correspondences[c.source]
        except KeyError:
            return None
        if (
            existing_correspondence
            and existing_correspondence.source == c.source
            and existing_correspondence.target == c.target
        ):
            return existing_correspondence
        return None

    def break_bond(self, bond):
        bond.source.string.delete_bond(bond)
        bond.source.outgoing_bonds.remove(bond)
        bond.target.incoming_bonds.remove(bond)
        if bond.is_sameness_bond:
            bond.target.outgoing_bonds.remove(bond)
            bond.source.incoming_bonds.remove(bond)
        bond.left_object.right_bond = None
        bond.right_object.left_bond = None

    def break_group(self, group):
        if group.group is not None:
            self.break_group(group.group)
        group.string.delete_group(group)
        for obj in group.objects:
            obj.group = None
        for bond in group.bonds:
            bond.group = None
        for bond in group.string.proposed_bonds:
            if bond.left_object == group or bond.right_object == group:
                group.string.delete_proposed_bond(bond)
        for bond in group.outgoing_and_incoming_bonds:
            self.break_bond(bond)
        for correspondence in self.proposed_correspondences:
            if correspondence.source is group or correspondence.target is group:
                self.delete_proposed_correspondence(correspondence)
        if group.correspondence is not None:
            self.break_correspondence(group.correspondence)

    def contains_slippage(self, slippage) -> bool:
        """Returns True if the workspace contains the slippage."""
        return slippage in self.slippages

    def get_random_string(self):
        return random.choice([self.initial_string, self.target_string])

    def choose_object(self, temperature, method) -> WorkspaceObject:
        """Return an object probabilistically according to temperature and method."""
        weights = [temperature_adjust(method(obj), temperature) for obj in self.objects]
        return select_item_from_list(self.objects, weights)

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
            if not obj.spans_whole_string() and obj.group is None
        ]

    @property
    def unbonded_objects(self) -> list:
        return [
            obj
            for obj in self.ungrouped_objects
            if (
                (obj.is_at_edge_of_string() and len(obj.bonds) == 0)
                or (not obj.is_at_edge_of_string() and len(obj.bonds) < 2)
            )
        ]

    @property
    def ungrouped_bonds(self) -> list:
        return [
            bond
            for bond in self.bonds
            if bond.source.group is None or bond.target.group is None
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

    @property
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

    def get_bottom_up_codelets(
        self, slipnet: "Slipnet", coderack: "Coderack", temperature: float
    ) -> List["Codelet"]:
        codelets: List["Codelet"] = []
        if (
            coderack.post_codelet_probability(
                "description", temperature, workspace=self
            )
            > random.random()
        ):
            for i in range(
                coderack.number_of_codelets_to_post("description", workspace=self)
            ):
                codelets.append(
                    BottomUpDescriptionScout(
                        urgency_bin=2,
                        coderack=coderack,
                        slipnet=slipnet,
                        workspace=self,
                    )
                )
        if (
            coderack.post_codelet_probability("bond", temperature, workspace=self)
            > random.random()
        ):
            for _ in range(coderack.number_of_codelets_to_post("bond", workspace=self)):
                codelets.append(
                    BottomUpBondScout(
                        urgency_bin=2,
                        coderack=coderack,
                        slipnet=slipnet,
                        workspace=self,
                    )
                )
        if (
            coderack.post_codelet_probability("group", temperature, workspace=self)
            > random.random()
        ):
            for _ in range(
                coderack.number_of_codelets_to_post("group", workspace=self)
            ):
                codelets.append(
                    WholeStringGroupScout(
                        urgency_bin=2,
                        coderack=coderack,
                        slipnet=slipnet,
                        workspace=self,
                    )
                )
        if (
            coderack.post_codelet_probability(
                "replacement", temperature, workspace=self
            )
            > random.random()
        ):
            for _ in range(
                coderack.number_of_codelets_to_post("replacement", workspace=self)
            ):
                codelets.append(
                    ReplacementFinder(
                        urgency_bin=2,
                        coderack=coderack,
                        slipnet=slipnet,
                        workspace=self,
                    )
                )
        if (
            coderack.post_codelet_probability(
                "correspondence", temperature, workspace=self
            )
            > random.random()
        ):
            for _ in range(
                coderack.number_of_codelets_to_post("correspondence", workspace=self)
            ):
                codelets.append(
                    BottomUpCorrespondenceScout(
                        urgency_bin=2,
                        coderack=coderack,
                        slipnet=slipnet,
                        workspace=self,
                    )
                )
                codelets.append(
                    ImportantObjectCorrespondenceScout(
                        urgency_bin=2,
                        coderack=coderack,
                        slipnet=slipnet,
                        workspace=self,
                    )
                )
        if (
            coderack.post_codelet_probability("rule", temperature, workspace=self)
            > random.random()
        ):
            for _ in range(coderack.number_of_codelets_to_post("rule", workspace=self)):
                codelets.append(
                    RuleScout(
                        urgency_bin=2,
                        coderack=coderack,
                        slipnet=slipnet,
                        workspace=self,
                    )
                )
        if (
            coderack.post_codelet_probability(
                "translated-rule", temperature, workspace=self
            )
            > random.random()
        ):
            for _ in range(
                coderack.number_of_codelets_to_post("translated-rule", workspace=self)
            ):
                urgency_bin = 2 if temperature > 0.25 else 6
                codelets.append(
                    RuleTranslator(
                        urgency_bin=urgency_bin,
                        coderack=coderack,
                        slipnet=slipnet,
                        workspace=self,
                    )
                )
        codelets.append(
            Breaker(
                urgency_bin=0,
                coderack=coderack,
                slipnet=slipnet,
                workspace=self,
            )
        )
        return codelets
