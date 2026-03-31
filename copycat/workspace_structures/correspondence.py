from __future__ import annotations
from typing import List

from copycat.concept_mapping import ConceptMapping
from copycat.workspace_objects import Letter
from copycat.workspace_structure import WorkspaceStructure


class Correspondence(WorkspaceStructure):
    def __init__(self, from_object, to_object, concept_mappings):
        self.from_object = from_object
        self.to_object = to_object
        self.concept_mappings = concept_mappings

    def __len__(self):
        """Returns the number of letters spanned by the objects."""
        return len(self.from_object) + len(self.to_object)

    def supports(self, other: Correspondence) -> bool:
        """Returns True if self and other are not incompatible and if self has a concept mapping that supports the concept mappings of other."""
        pass

    def incompatible_with(self, other: Correspondence) -> bool:
        """Returns True if self and other share objects or if self has a concept mapping that is incompatible with the concept mappings of other."""
        pass

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

    def get_relevant_distinguishing_mappings(self) -> List[ConceptMapping]:
        return [
            mapping
            for mapping in self.concept_mappings
            if mapping.is_relevant() and mapping.is_distinguishing()
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
        if (
            isinstance(self.from_object, Letter)
            and self.from_object.spans_whole_string()
        ) or (
            isinstance(self.to_object, Letter) and self.to_object.spans_whole_string()
        ):
            return 1.0
        support_sum = 0.0
        for c in self.workspace.correspondences:
            if c is not self and self.is_supported_by(c):
                support_sum += c.total_strength
        return min(1.0, support_sum)
