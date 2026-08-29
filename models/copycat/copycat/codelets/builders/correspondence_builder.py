from typing import Optional

from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.codelets.builder import Builder
from copycat.concept_mapping import ConceptMapping
from copycat.tools import structure_beats_structures
from copycat.workspace_objects import Group, Letter
from copycat.workspace_structures import Bond, Correspondence


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
        target_flipped: bool = False,
    ):
        super().__init__(
            urgency_bin=urgency_bin,
            coderack=coderack,
            workspace=workspace,
            slipnet=slipnet,
            proposed_structure=proposed_correspondence,
        )
        self.proposed_correspondence = proposed_correspondence
        self.target_flipped = target_flipped

    def run(self, temperature: float) -> "CodeletResult":
        if self.target_flipped:
            existing_target = self.workspace.target_string.get_group_if_present(
                self.proposed_correspondence.target.get_flipped_version()
            )
        if self.proposed_correspondence.source not in self.workspace.objects:
            return Fizzle(FizzleReason.OBJECTS_NO_LONGER_EXIST)
        if self.proposed_correspondence.target not in self.workspace.objects:
            if self.target_flipped and not existing_target:
                return Fizzle(FizzleReason.OBJECTS_NO_LONGER_EXIST)
            if not self.target_flipped:
                return Fizzle(FizzleReason.OBJECTS_NO_LONGER_EXIST)
        self.workspace.delete_proposed_correspondence(self.proposed_correspondence)
        if self._augment_existing_correspondence_if_exists():
            return Fizzle(FizzleReason.STRUCTURE_ALREADY_EXISTS)
        if self._not_all_concept_mappings_relevant():
            return Fizzle(FizzleReason.NOT_ALL_CONCEPT_MAPPINGS_RELEVANT)
        incompatible_correspondences = self._get_incompatible_correspondences()
        for incompatible_correspondence in incompatible_correspondences:
            # correspondences between large groups preferred over
            # correspondences between small groups or letters
            fight_result = structure_beats_structures(
                self.proposed_correspondence,
                self.proposed_correspondence.letter_span(),
                [incompatible_correspondence],
                incompatible_correspondence.letter_span(),
                temperature=temperature,
            )
            if not fight_result:
                return Fizzle(FizzleReason.INCOMPATIBLE_STRUCTURES_WON)
        incompatible_bond = self._get_incompatible_bond()
        if incompatible_bond:
            fight_result = structure_beats_structures(
                self.proposed_correspondence,
                3,
                [incompatible_bond],
                2,
                temperature=temperature,
            )
            if not fight_result:
                return Fizzle(FizzleReason.INCOMPATIBLE_STRUCTURES_WON)
        incompatible_group = incompatible_bond.group if incompatible_bond else None
        if incompatible_group:
            fight_result = structure_beats_structures(
                self.proposed_correspondence,
                1,
                [incompatible_group],
                1,
                temperature=temperature,
            )
            if not fight_result:
                return Fizzle(FizzleReason.INCOMPATIBLE_STRUCTURES_WON)
        if self.target_flipped:
            fight_result = structure_beats_structures(
                self.proposed_correspondence,
                1,
                [existing_target],
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
        if incompatible_group:
            self.workspace.break_group(incompatible_group)
        if incompatible_bond:
            self.workspace.break_bond(incompatible_bond)
        for correspondence in incompatible_correspondences:
            self.workspace.break_correspondence(correspondence)
        if self.target_flipped:
            self.workspace.break_group(existing_target)
            for bond in existing_target.bonds:
                self.workspace.break_bond(bond)
            for bond in self.proposed_correspondence.target.bonds:
                self.workspace.target_string.add_bond(bond)
                bond.source.outgoing_bonds.append(bond)
                bond.target.incoming_bonds.append(bond)
                if bond.bond_category == self.slipnet["sameness"]:
                    bond.target.outgoing_bonds.append(bond)
                    bond.source.incoming_bonds.append(bond)
                bond.left_object.right_bond = bond
                bond.right_object.left_bond = bond
                self.slipnet.activate_node_from_workspace(bond.bond_category.name)
                self.slipnet.activate_node_from_workspace(bond.direction_category.name)
            self.workspace.target_string.add_group(self.proposed_correspondence.target)
            for obj in self.proposed_correspondence.target.objects:
                obj.group = self.proposed_correspondence.target
            for bond in self.proposed_correspondence.target.bonds:
                bond.group = self.proposed_correspondence.target
            for description in self.proposed_correspondence.target.descriptions:
                self.slipnet.activate_node_from_workspace(description.descriptor.name)
        if incompatible_rule:
            self.workspace.rule = None
        self._build_correspondence()
        return Finish()

    def _augment_existing_correspondence_if_exists(self) -> bool:
        existing_correspondence = self.workspace.get_existing_correspondence(
            self.proposed_correspondence
        )
        if existing_correspondence is None:
            return False
        for mapping in self.proposed_correspondence.concept_mappings:
            if mapping.label is not None:
                self.slipnet.activate_node_from_workspace(mapping.label.name)
            if mapping in existing_correspondence.concept_mappings:
                continue
            existing_correspondence.concept_mappings.append(mapping)
        return True

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

    def _get_incompatible_bond(self) -> Optional[Bond]:
        source_bond = (
            self.proposed_correspondence.source.right_bond
            if self.proposed_correspondence.source.is_leftmost_in_string()
            else self.proposed_correspondence.source.left_bond
            if self.proposed_correspondence.source.is_rightmost_in_string()
            else None
        )
        target_bond = (
            self.proposed_correspondence.target.right_bond
            if self.proposed_correspondence.target.is_leftmost_in_string()
            else self.proposed_correspondence.target.left_bond
            if self.proposed_correspondence.target.is_rightmost_in_string()
            else None
        )
        if not (
            source_bond
            and target_bond
            and source_bond.direction_category
            and target_bond.direction_category
        ):
            return None
        bond_concept_mapping = ConceptMapping(
            description_type_1=self.slipnet["direction_category"],
            description_type_2=self.slipnet["direction_category"],
            descriptor_1=source_bond.direction_category,
            descriptor_2=target_bond.direction_category,
            label=self.slipnet.get_label_node(
                source_bond.direction_category, target_bond.direction_category
            ),
        )
        for mapping in self.proposed_correspondence.concept_mappings:
            if mapping.is_incompatible_with(bond_concept_mapping):
                return target_bond
        return None

    def _get_incompatible_rule(self):
        if not self.proposed_correspondence.source.is_changed_letter:
            return None
        if not self.workspace.rule:
            return None
        proposed_mapping_descriptors = [
            m.descriptor_1 for m in self.proposed_correspondence.concept_mappings
        ]
        if self.workspace.rule.descriptor_1 in proposed_mapping_descriptors:
            return None
        slippages = [
            d.apply_slippages(self.workspace.slippages)
            for d in [
                d.descriptor
                for d in self.proposed_correspondence.target.get_relevant_descriptions()
            ]
        ]
        if self.workspace.rule.descriptor_1 in slippages:
            return None
        return self.workspace.rule

    def _build_correspondence(self):
        self.proposed_correspondence.source.correspondence = (
            self.proposed_correspondence
        )
        self.proposed_correspondence.target.correspondence = (
            self.proposed_correspondence
        )
        self.workspace.add_correspondence(self.proposed_correspondence)
        for mapping in (
            self.proposed_correspondence.get_relevant_distinguishing_mappings()
            + self.proposed_correspondence.accessory_concept_mappings
        ):
            if not mapping.is_slippage:
                continue
            self.proposed_correspondence.accessory_concept_mappings.append(
                mapping.get_symmetric_version()
            )
        if isinstance(self.proposed_correspondence.source, Group) and isinstance(
            self.proposed_correspondence.target, Group
        ):
            for mapping in self.slipnet.get_concept_mappings(
                self.proposed_correspondence.source,
                self.proposed_correspondence.target,
                self.proposed_correspondence.source.bond_descriptions,
                self.proposed_correspondence.target.bond_descriptions,
            ):
                self.proposed_correspondence.accessory_concept_mappings.append(mapping)
                if mapping.is_slippage:
                    self.proposed_correspondence.accessory_concept_mappings.append(
                        mapping.get_symmetric_version()
                    )
        for mapping in self.proposed_correspondence.concept_mappings:
            if mapping.label:
                self.slipnet.activate_node_from_workspace(mapping.label.name)
