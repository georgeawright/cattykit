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
        self.source = None
        self.target = None

    def run(self, temperature: float) -> CodeletResult:
        objects_or_fizzle = self._get_objects_or_fizzle(temperature)
        if isinstance(objects_or_fizzle, Fizzle):
            return objects_or_fizzle
        # According to original code, this probably isn't right.
        if (
            self.source.spans_whole_string() and not self.target.spans_whole_string()
        ) or (
            self.target.spans_whole_string() and not self.source.spans_whole_string()
        ):
            return Fizzle(FizzleReason.INCOMPATIBLE_OBJECT_SPANS)
        concept_mappings = self.slipnet.get_concept_mappings(
            self.source,
            self.target,
            self.source.get_relevant_descriptions(),
            self.target.get_relevant_descriptions(),
        )
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
        target_flipped = False
        if (
            self.source.spans_whole_string()
            and self.target.spans_whole_string()
            and any(
                mapping.description_type_1.name == "direction_category"
                for mapping in possible_opposite_concept_mappings
            )
            and all(
                mapping.is_opposite for mapping in possible_opposite_concept_mappings
            )
            and not self.slipnet.get_node("opposite").is_active()
        ):
            self.target = self.target.get_flipped_version()
            concept_mappings = self.slipnet.get_concept_mappings(
                self.source, self.target
            )
            target_flipped = True
        self.propose_correspondence(
            self.source,
            self.target,
            concept_mappings,
            target_flipped,
            temperature=temperature,
        )
        return Finish()

    def propose_correspondence(
        self,
        source: "WorkspaceObject",
        target: "WorkspaceObject",
        concept_mappings: List[ConceptMapping],
        target_flipped: bool,
        temperature: float,
    ):
        proposed_correspondence = Correspondence(
            self.workspace, source, target, concept_mappings
        )
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
                target_flipped=target_flipped,
            ),
            temperature=temperature,
        )
