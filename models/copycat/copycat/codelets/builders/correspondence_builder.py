from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.codelets.builder import Builder
from copycat.tools import structure_beats_structures
from copycat.workspace_objects import Group, Letter
from copycat.workspace_structures import Correspondence


class CorrespondenceBuilder(Builder):
    """A correspondence builder tries to build the proposed correspondence.
    It fights with competitors if necessary."""

    def __init__(
        self,
        urgency_bin: int,
        coderack: "Coderack",
        workspace: "Workspace",
        slipnet: "Slipnet",
        proposed_correspondence: Correspondence,
        to_object_flipped: bool = False,
    ):
        super().__init__(
            urgency_bin=urgency_bin,
            coderack=coderack,
            workspace=workspace,
            slipnet=slipnet,
            proposed_structure=proposed_correspondence,
        )
        self.proposed_correspondence = proposed_correspondence
        self.to_object_flipped = to_object_flipped

    def run(self, temperature: float) -> "CodeletResult":
        if self.proposed_correspondence.from_object not in self.workspace.objects:
            return Fizzle(FizzleReason.OBJECTS_NO_LONGER_EXIST)
        if (
            self.proposed_correspondence.to_object not in self.workspace.objects
            and not (
                self.to_object_flipped
                and self.proposed_correspondence.to_object.get_flipped_version()
                in self.workspace.objects
            )
        ):
            return Fizzle(FizzleReason.OBJECTS_NO_LONGER_EXIST)
        self.workspace.delete_proposed_correspondence(self.proposed_correspondence)
        if self._augment_existing_correspondence_if_exists():
            return Fizzle(FizzleReason.STRUCTURE_ALREADY_EXISTS)
        if self._not_all_concept_mappings_relevant():
            return Fizzle(FizzleReason.NOT_ALL_CONCEPT_MAPPINGS_RELEVANT)
        incompatible_correspondences = self._get_incompatible_correspondences()
        if incompatible_correspondences:
            fight_result = structure_beats_structures(
                self.proposed_correspondence,
                1,
                incompatible_correspondences,
                1,
                temperature=temperature,
            )
            if not fight_result:
                return Fizzle(FizzleReason.INCOMPATIBLE_STRUCTURES_WON)
        (
            incompatible_bonds,
            incompatible_groups,
        ) = self._get_incompatible_bonds_and_groups()
        if incompatible_bonds:
            fight_result = structure_beats_structures(
                self.proposed_correspondence,
                1,
                incompatible_bonds,
                1,
                temperature=temperature,
            )
            if not fight_result:
                return Fizzle(FizzleReason.INCOMPATIBLE_STRUCTURES_WON)
        if incompatible_groups:
            fight_result = structure_beats_structures(
                self.proposed_correspondence,
                1,
                incompatible_groups,
                max([g.letter_span for g in incompatible_groups]),
                temperature=temperature,
            )
            if not fight_result:
                return Fizzle(FizzleReason.INCOMPATIBLE_STRUCTURES_WON)
        existing_group = (
            self.workspace.target_string.get_group_if_present(
                self.proposed_correspondence.to_object.get_flipped_version()
            )
            if self.to_object_flipped
            else None
        )
        if self.to_object_flipped and existing_group:
            fight_result = structure_beats_structures(
                self.proposed_correspondence,
                1,
                [existing_group],
                1,
                temperature=temperature,
            )
            if not fight_result:
                return Fizzle(FizzleReason.INCOMPATIBLE_STRUCTURES_WON)
        incompatible_rule = self._get_incompatible_rule()
        if incompatible_rule:
            fight_result = structure_beats_structures(
                self.proposed_correspondence,
                1,
                [incompatible_rule],
                1,
                temperature=temperature,
            )
            if not fight_result:
                return Fizzle(FizzleReason.INCOMPATIBLE_STRUCTURES_WON)
        for group in incompatible_groups:
            self.workspace.break_group(group)
        for bond in incompatible_bonds:
            self.workspace.break_bond(bond)
        for correspondence in incompatible_correspondences:
            self.workspace.break_correspondence(correspondence)
        if existing_group:
            self.workspace.break_group(existing_group)
            for bond in existing_group.bonds:
                self.workspace.break_bond(bond)
            for bond in self.proposed_correspondence.to_object.bonds:
                self.workspace.target_string.add_bond(bond)
            self.workspace.target_string.add_group(
                self.proposed_correspondence.to_object
            )
        if incompatible_rule:
            self.workspace.break_rule(incompatible_rule)
        self._build_correspondence()
        return Finish()

    def _augment_existing_correspondence_if_exists(self):
        existing_correspondence = self.workspace.get_existing_correspondence(
            self.proposed_correspondence
        )
        if existing_correspondence is None:
            return False
        for mapping in self.proposed_correspondence.concept_mappings:
            self.slipnet.activate_node_from_workspace(mapping.label)
            if mapping not in existing_correspondence.concept_mappings:
                continue
            existing_correspondence.concept_mappings.append(mapping)

    def _not_all_concept_mappings_relevant(self):
        for mapping in self.proposed_correspondence.concept_mappings:
            if not mapping.is_relevant():
                return True
        return False

    def _get_incompatible_correspondences(self):
        return [
            c
            for c in self.workspace.correspondences
            if c.is_incompatible_argumentwise_with(self.proposed_correspondence)
            or c.is_incompatible_structurally_with(self.proposed_correspondence)
            or c.is_incompatible_conceptually_with(self.proposed_correspondence)
            or c.is_incompatible_boundarywise_with(self.proposed_correspondence)
        ]

    def _get_leftmost_and_rightmost_incompatible_correspondences(
        self, from_object, to_object, direction_category_mapping
    ):
        pass

    def _get_incompatible_bonds_and_groups(self):
        pass

    def _get_incompatible_rule(self):
        pass

    def _build_correspondence(self):
        pass
