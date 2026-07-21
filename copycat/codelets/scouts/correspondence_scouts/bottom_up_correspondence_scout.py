import random
from typing import List

from copycat.codelets.scouts.correspondence_scout import CorrespondenceScout
from copycat.concept_mapping import ConceptMapping
from copycat.tools import temperature_adjust


class BottomUpCorrespondenceScout(CorrespondenceScout):
    """Chooses an object each from the initial and target strings
    probabilistically by inter-string-salience.
    Finds all concept mappings between nodes at most one link away.
    If any concept mappings can be made between distinguishing descriptors,
    makes a proposed correspondence between the two objects including all the concept mappings
    and posts a correspondence strength tester with urgency a function of the average strength
    of the distinguishing concept mappings."""

    def __init__(
        self,
        urgency_bin: int,
        coderack: "Coderack",
        workspace: "Workspace",
        slipnet: "Slipnet",
    ):
        super().__init__(urgency_bin, coderack, workspace, slipnet)

    def run(self, temperature: float):
        object_1 = self.workspace.initial_string.choose_object(
            selection_method=lambda x: x.inter_string_salience
        )
        object_2 = self.workspace.target_string.choose_object(
            selection_method=lambda x: x.inter_string_salience
        )
        # According to original code, this probably isn't right.
        if (object_1.spans_whole_string() and not object_2.spans_whole_string()) or (
            object_2.spans_whole_string() and not object_1.spans_whole_string()
        ):
            return
        concept_mappings = self._get_concept_mappings(object_1, object_2)
        concept_mappings_possible = any(
            random.random() < temperature_adjust(mapping.slippability, temperature)
            for mapping in concept_mappings
        )
        if not concept_mappings_possible:
            return
        distinguishing_concept_mappings = [
            mapping for mapping in concept_mappings if mapping.is_distinguishing()
        ]
        if not distinguishing_concept_mappings:
            return

        # COMMENT FROM ORIGINAL SOURCE CODE:
        # If both objects span the string, and if all the distinguishing
        # concept-mappings (except string-position-category concept-mappings),
        # are opposites, and plato-opposite isn't active, then consider a
        # correspondence with the target-string group flipped.
        # E.g., suppose in the problem "abc -> abd, pqrs -> ?"
        # that "abc" has been described as an left-to-right succgrp and
        # "pqrs" has been described as a right-to-left predgrp.  This puts
        # top-down pressure on the program to flip "pqrs" so that it has
        # the same description as "abc".  Notice that this can only happen
        # at the time that the two strings are explicitly compared by a
        # correspondence-scout codelet.
        possible_opposite_concept_mappings = [
            mapping
            for mapping in distinguishing_concept_mappings
            if mapping.description_type_1.name
            not in ["string_position_category", "bond_facet"]
        ]
        object_2_flipped = False
        if (
            object_1.spans_whole_string()
            and object_2.spans_whole_string()
            and any(
                mapping.description_type_1.name == "direction_category"
                for mapping in possible_opposite_concept_mappings
            )
            and all(
                mapping.is_opposite() for mapping in possible_opposite_concept_mappings
            )
            and not self.slipnet.get_node("opposite").is_active()
        ):
            object_2 = object_2.get_flipped_version()
            concept_mappings = self._get_concept_mappings(object_1, object_2)
            object_2_flipped = True
        self.propose_correspondence(
            object_1, object_2, concept_mappings, object_2_flipped
        )

    def _get_concept_mappings(
        self, object_1: "WorkspaceObject", object_2: "WorkspaceObject"
    ) -> List[ConceptMapping]:
        return [
            ConceptMapping(
                description_type_1=desc_1.facet,
                description_type_2=desc_2.facet,
                descriptor_1=desc_1.descriptor,
                descriptor_2=desc_2.descriptor,
                object_1=object_1,
                object_2=object_2,
            )
            for desc_1 in object_1.descriptions
            for desc_2 in object_2.descriptions
            if desc_1.facet == desc_2.facet
            and (
                desc_1.descriptor == desc_2.descriptor
                or desc_1.descriptor.is_linked_to(desc_2.descriptor)
            )
        ]
