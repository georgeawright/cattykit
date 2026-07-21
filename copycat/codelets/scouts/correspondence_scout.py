import random
from typing import List

from copycat.workspace_structures import Correspondence
from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.codelets.scout import Scout
from copycat.codelets.strength_testers import CorrespondenceStrengthTester
from copycat.concept_mapping import ConceptMapping
from copycat.tools import temperature_adjust


class CorrespondenceScout(Scout):
    """A correspondence scout codelet looks for evidence of a correspondence.
    If possible, it makes a proposed correspondence and posts a
    correspondence strength tester."""

    def __init__(
        self,
        urgency_bin: int,
        coderack: "Coderack",
        workspace: "Workspace",
        slipnet: "Slipnet",
    ):
        super().__init__(urgency_bin, coderack, workspace, slipnet)
        self.object_1 = None
        self.object_2 = None

    def run(self, temperature: float) -> CodeletResult:
        objects_or_fizzle = self._get_objects_or_fizzle()
        if isinstance(objects_or_fizzle, Fizzle):
            return objects_or_fizzle
        # According to original code, this probably isn't right.
        if (
            self.object_1.spans_whole_string()
            and not self.object_2.spans_whole_string()
        ) or (
            self.object_2.spans_whole_string()
            and not self.object_1.spans_whole_string()
        ):
            return Fizzle(FizzleReason.INCOMPATIBLE_OBJECT_SPANS)
        concept_mappings = self._get_concept_mappings(self.object_1, self.object_2)
        concept_mappings_possible = any(
            random.random() < temperature_adjust(mapping.slippability, temperature)
            for mapping in concept_mappings
        )
        if not concept_mappings_possible:
            return Fizzle(FizzleReason.NO_CONCEPT_MAPPINGS)
        distinguishing_concept_mappings = [
            mapping for mapping in concept_mappings if mapping.is_distinguishing()
        ]
        if not distinguishing_concept_mappings:
            return Fizzle(FizzleReason.NO_DISTINGUISHING_CONCEPT_MAPPINGS)

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
            self.object_1.spans_whole_string()
            and self.object_2.spans_whole_string()
            and any(
                mapping.description_type_1.name == "direction_category"
                for mapping in possible_opposite_concept_mappings
            )
            and all(
                mapping.is_opposite() for mapping in possible_opposite_concept_mappings
            )
            and not self.slipnet.get_node("opposite").is_active()
        ):
            self.object_2 = self.object_2.get_flipped_version()
            concept_mappings = self._get_concept_mappings(self.object_1, self.object_2)
            object_2_flipped = True
        self.propose_correspondence(
            self.object_1, self.object_2, concept_mappings, object_2_flipped
        )
        return Finish()

    def propose_correspondence(
        self,
        object_1: "WorkspaceObject",
        object_2: "WorkspaceObject",
        concept_mappings: List[ConceptMapping],
        object_2_flipped: bool,
    ):
        proposed_correspondence = Correspondence(
            self.workspace, object_1, object_2, concept_mappings
        )
        proposed_correspondence.proposal_level = 1
        distinguishing_mappings = proposed_correspondence.get_distinguishing_mappings()
        for mapping in distinguishing_mappings:
            self.slipnet.activate_node_from_workspace(mapping.description_type_1.name)
            self.slipnet.activate_node_from_workspace(mapping.descriptor_1.name)
            self.slipnet.activate_node_from_workspace(mapping.description_type_2.name)
            self.slipnet.activate_node_from_workspace(mapping.descriptor_2.name)
        self.workspace.add_proposed_correspondence(proposed_correspondence)
        urgency = sum(mapping.strength for mapping in distinguishing_mappings) / len(
            distinguishing_mappings
        )
        urgency_bin = self.coderack.get_urgency_level_from_activation(urgency)
        self.coderack.post(
            CorrespondenceStrengthTester(
                urgency_bin=urgency_bin,
                coderack=self.coderack,
                slipnet=self.slipnet,
                workspace=self.workspace,
                proposed_correspondence=proposed_correspondence,
                object_2_flipped=object_2_flipped,
            )
        )
