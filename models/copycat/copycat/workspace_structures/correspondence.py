from __future__ import annotations
import itertools
from typing import List, Optional

from copycat.concept_mapping import ConceptMapping
from copycat.workspace_objects import Letter
from copycat.workspace_structure import WorkspaceStructure


class Correspondence(WorkspaceStructure):
    _next_id = itertools.count(1)

    def __init__(
        self,
        workspace: "Workspace",
        source: "WorkspaceObject",
        target: "WorkspaceObject",
        concept_mappings: List[ConceptMapping],
    ):
        super().__init__()
        self.workspace = workspace
        self.source = source
        self.target = target
        self.concept_mappings = concept_mappings
        # accessory mappings includes:
        # - mappings symmetric to those in concept mappings
        # - bond category and bond facet equivalents to group concept mappings
        self.accessory_concept_mappings: List[ConceptMapping] = []
        self.hash_id = next(Correspondence._next_id)

    def __repr__(self):
        return f"{self.source} ==> {self.target}\n" + "\n".join(
            [f"  {mapping}" for mapping in self.concept_mappings]
        )

    @property
    def direction_mapping(self) -> Optional["Slipnode"]:
        return next(
            (
                mapping.label
                for mapping in self.concept_mappings
                if mapping.description_type_1.name == "direction_category"
                and mapping.description_type_2.name == "direction_category"
            ),
            None,
        )

    @property
    def slippages(self) -> List[ConceptMapping]:
        """Slippages are non-identity concept mappings."""
        return [
            mapping
            for mapping in self.concept_mappings + self.accessory_concept_mappings
            if mapping.is_slippage
        ]

    def letter_span(self):
        """Returns the number of letters spanned by the objects."""
        return self.source.letter_span() + self.target.letter_span()

    def equates_to(self, other) -> bool:
        if not isinstance(other, Correspondence):
            return False
        return (
            self.source,
            self.target,
            self.concept_mappings,
        ) == (
            other.source,
            other.target,
            other.concept_mappings,
        )

    def get_other_object(self, obj):
        """Returns the other object in the correspondence."""
        if obj == self.source:
            return self.target
        elif obj == self.target:
            return self.source
        else:
            raise ValueError("Object not in correspondence.")

    def supports(self, other: Correspondence) -> bool:
        """Returns True if self and other are not incompatible
        and self has s concept mapping that supports other's concept mappings.
        """
        if self.is_incompatible_argumentwise_with(other):
            return False
        if self.is_incompatible_conceptually_with(other):
            return False
        for mapping_1 in self.get_distinguishing_mappings():
            for mapping_2 in other.get_distinguishing_mappings():
                if mapping_1.supports(mapping_2):
                    return True
        return False

    def is_incompatible_argumentwise_with(self, other: Correspondence) -> bool:
        """Self and other share objects."""
        return self.source is other.source or self.target is other.target

    def is_incompatible_conceptually_with(self, other: Correspondence) -> bool:
        """Self has a concept mapping incompatible with other's concept mappings."""
        for mapping_1 in self.concept_mappings:
            for mapping_2 in other.concept_mappings:
                if mapping_1.is_incompatible_with(mapping_2):
                    return True
        return False

    def is_incompatible_structurally_with(self, other: Correspondence) -> bool:
        """Return whether group membership makes ``other`` incompatible with self."""
        from copycat.workspace_objects import Group, Letter

        def _is_member(obj, group: Group) -> bool:
            return any(obj is member for member in group.objects)

        if isinstance(self.source, Group):
            for member in self.source.objects:
                if member.correspondence is not other:
                    continue
                if isinstance(self.target, Letter) or not _is_member(
                    other.target, self.target
                ):
                    return True

        if isinstance(self.target, Group):
            for member in self.target.objects:
                if member.correspondence is not other:
                    continue
                if isinstance(self.source, Letter) or not _is_member(
                    other.source, self.source
                ):
                    return True

        source_group = self.source.group
        if source_group is not None and source_group.correspondence is other:
            if self.target.group is None or self.target.group is not other.target:
                return True

        target_group = self.target.group
        if target_group is not None and target_group.correspondence is other:
            if self.source.group is None or self.source.group is not other.source:
                return True

        return False

    def is_incompatible_boundarywise_with(self, other: Correspondence) -> bool:
        """Self is between string-spanning groups and other is between member objects
        from the boundaries of the groups with incompatible directions."""
        if not (
            self.source.is_string_spanning_group()
            and self.target.is_string_spanning_group()
            and self.direction_mapping is not None
            and other is not None
        ):
            return False
        left_correspondence = self.source.left_object.correspondence
        right_correspondence = self.source.right_object.correspondence
        if self.direction_mapping.name == "identity":
            if other is left_correspondence:
                return other.target is not self.target.left_object
            if other is right_correspondence:
                return other.target is not self.target.right_object
        elif self.direction_mapping.name == "opposite":
            if other is left_correspondence:
                return other.target is not self.target.right_object
            if other is right_correspondence:
                return other.target is not self.target.left_object
        return False

    def calculate_internal_strength(self) -> float:
        relevant_distinguishing_mappings = self.get_relevant_distinguishing_mappings()
        if not relevant_distinguishing_mappings:
            return 0.0
        average_strength = sum(
            [mapping.strength for mapping in relevant_distinguishing_mappings]
        ) / len(relevant_distinguishing_mappings)
        number_of_mappings_factor = {
            1: 0.8,
            2: 1.2,
        }.get(len(relevant_distinguishing_mappings), 1.6)
        internal_coherence_factor = 2.5 if self.is_internally_coherent() else 1.0
        return min(
            1.0,
            average_strength * internal_coherence_factor * number_of_mappings_factor,
        )

    def get_relevant_mappings(self) -> List[ConceptMapping]:
        return [m for m in self.concept_mappings if m.is_relevant()]

    def get_distinguishing_mappings(self) -> List[ConceptMapping]:
        return [m for m in self.concept_mappings if m.is_distinguishing()]

    def get_relevant_distinguishing_mappings(self) -> List[ConceptMapping]:
        return [
            m
            for m in self.concept_mappings
            if m.is_relevant() and m.is_distinguishing()
        ]

    def is_internally_coherent(self) -> bool:
        """Returns True if there is any pair of relevant-distinguishing mappings
        that support each other.
        According to original source code, this isn't quite right."""
        relevant_distinguishing_mappings = self.get_relevant_distinguishing_mappings()
        for i, mapping in enumerate(relevant_distinguishing_mappings):
            for other_mapping in relevant_distinguishing_mappings[i + 1 :]:
                if mapping.supports(other_mapping):
                    return True
        return False

    def calculate_external_strength(self) -> float:
        return self._support()

    def _support(self) -> float:
        """There are three levels of compatibility:
        - supporting;
        - not incompatible but not supporting;
        - incompatible.
        This returns the sum of the strengths of supporting correspondences up to 1.
        If one of the objects is the single letter in its string, then the support is 1.
        """
        if (isinstance(self.source, Letter) and self.source.spans_whole_string()) or (
            isinstance(self.target, Letter) and self.target.spans_whole_string()
        ):
            return 1.0
        support_sum = 0.0
        for c in self.workspace.correspondences:
            if c is not self and self.supports(c):
                support_sum += c.total_strength
        return min(1.0, support_sum)
