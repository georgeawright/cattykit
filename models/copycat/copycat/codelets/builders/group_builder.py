import random
from typing import List

from copycat.codelets.builder import Builder
from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.concept_mapping import ConceptMapping
from copycat.tools import structure_beats_structures, temperature_adjust
from copycat.workspace_objects import Group
from copycat.workspace_structures import Description


class GroupBuilder(Builder):
    """A group builder tries to build the proposed group.
    It fights with competitors if necessary.
    """

    def __init__(
        self,
        urgency_bin: int,
        coderack: "Coderack",
        workspace: "Workspace",
        slipnet: "Slipnet",
        proposed_group: Group,
    ):
        super().__init__(
            urgency_bin=urgency_bin,
            coderack=coderack,
            workspace=workspace,
            slipnet=slipnet,
            proposed_structure=proposed_group,
        )
        self.proposed_group = proposed_group

    def run(self, temperature: float) -> CodeletResult:
        workspace_string = self.proposed_group.string
        existing_group = workspace_string.get_group_if_present(self.proposed_group)
        if existing_group:
            self._activate_group_descriptors(existing_group)
            self._transfer_descriptions(self.proposed_group, existing_group)
            workspace_string.delete_proposed_group(self.proposed_group)
            return Fizzle(FizzleReason.STRUCTURE_ALREADY_EXISTS)
        if not self._all_bonds_still_exist(workspace_string):
            workspace_string.delete_proposed_group(self.proposed_group)
            return Fizzle(FizzleReason.REQUIRED_BONDS_NO_LONGER_EXIST)
        workspace_string.delete_proposed_group(self.proposed_group)
        bonds_to_be_flipped = self.proposed_group.get_bonds_to_be_flipped()
        if bonds_to_be_flipped:
            fight_result = structure_beats_structures(
                self.proposed_group,
                len(self.proposed_group),
                bonds_to_be_flipped,
                1,
                temperature=temperature,
            )
            if not fight_result:
                return Fizzle(FizzleReason.INCOMPATIBLE_STRUCTURES_WON)
        incompatible_groups = self._get_incompatible_groups()
        for incompatible_group in incompatible_groups:
            if incompatible_group.group_category == self.proposed_group.group_category:
                # this is because shorter sameness groups are weaker than longer ones
                # and there is no group-extender codelet
                proposed_group_weight = len(self.proposed_group)
                incompatible_group_weight = len(incompatible_group)
            else:
                proposed_group_weight = 1
                incompatible_group_weight = 1
            fight_result = structure_beats_structures(
                self.proposed_group,
                proposed_group_weight,
                [incompatible_group],
                incompatible_group_weight,
                temperature=temperature,
            )
            if not fight_result:
                return Fizzle(FizzleReason.INCOMPATIBLE_STRUCTURES_WON)
        incompatible_correspondences = self._get_incompatible_correspondences()
        if incompatible_correspondences:
            fight_result = structure_beats_structures(
                self.proposed_group,
                1,
                incompatible_correspondences,
                1,
                temperature=temperature,
            )
            if not fight_result:
                return Fizzle(FizzleReason.INCOMPATIBLE_STRUCTURES_WON)
        self._break_incompatible_structures(
            incompatible_groups, incompatible_correspondences
        )
        self._flip_bonds(bonds_to_be_flipped)
        self._build_group(temperature)
        return Finish()

    def _activate_group_descriptors(self, group: Group):
        for description in group.descriptions:
            self.slipnet.activate_node_from_workspace(description.descriptor.name)

    def _transfer_descriptions(self, source_group: Group, target_group: Group):
        for description in source_group.descriptions:
            if target_group.has_description(description):
                continue
            new_description = description.copy()
            new_description.argument_object = target_group
            target_group.add_description(description)

    def _all_bonds_still_exist(self, workspace_string: "WorkspaceString") -> bool:
        for bond in self.proposed_group.bonds:
            if (
                bond not in workspace_string.bonds
                and bond.get_flipped_version() not in workspace_string.bonds
            ):
                return False
        return True

    def _get_incompatible_groups(self):
        return [
            obj.group
            for obj in self.proposed_group.objects
            if obj.group and not obj.group.equates_to(self.proposed_group)
        ]

    def _get_incompatible_correspondences(self):
        return [
            obj.correspondence
            for obj in self.proposed_group.objects
            if obj.correspondence
            and self._correspondence_is_incompatible(obj.correspondence, obj)
        ]

    def _correspondence_is_incompatible(self, correspondence, obj):
        """Returns True if the given correspondence is incompatible
        with the proposed group."""
        string_position_category_concept_mapping = next(
            (
                mapping
                for mapping in correspondence.concept_mappings
                if mapping.description_type_1.name == "string_position_category"
            ),
            None,
        )
        if string_position_category_concept_mapping is None:
            return False
        other_obj = correspondence.get_other_object(obj)
        other_bond = None
        if other_obj.is_leftmost_in_string():
            other_bond = other_obj.right_bond
        elif other_obj.is_rightmost_in_string():
            other_bond = other_obj.left_bond
        if other_bond is None or other_bond.direction_category is None:
            return False
        group_concept_mapping = ConceptMapping(
            description_type_1=self.slipnet.direction_category,
            description_type_2=self.slipnet.direction_category,
            descriptor_1=self.proposed_group.direction_category,
            descriptor_2=other_bond.direction_category,
            label=None,
            object_1=None,
            object_2=None,
        )
        return self.workspace.incompatible_concept_mappings(
            group_concept_mapping, string_position_category_concept_mapping
        )

    def _break_incompatible_structures(
        self, incompatible_groups, incompatible_correspondences
    ):
        for group in incompatible_groups:
            self.workspace.break_group(group)
        for correspondence in incompatible_correspondences:
            self.workspace.break_correspondence(correspondence)

    def _flip_bonds(self, bonds_to_be_flipped: List["Bond"]):
        """Flip any bonds that need flipping,
        and replace in group's bond-list any bonds that got rebuilt
        (and thus are equal but not eq to the corresponding bond
        in the group's bond list)."""
        if not bonds_to_be_flipped:
            return
        for bond in self.proposed_group.bonds:
            flipped_bond = self.proposed_group.string.get_bond_if_present(
                bond.get_flipped_version()
            )
            if flipped_bond:
                self.workspace.break_bond(flipped_bond)
                self.workspace.build_bond(bond)
            else:
                existing_bond = self.proposed_group.string.get_bond_if_present(bond)
                if existing_bond and existing_bond != bond:
                    index = self.proposed_group.bonds.index(bond)
                    self.proposed_group.bonds[index] = existing_bond

    def _build_group(self, temperature: float):
        string = self.proposed_group.string
        string.add_group(self.proposed_group)
        for obj in self.proposed_group.objects:
            obj.group = self.proposed_group
        for bond in self.proposed_group.bonds:
            bond.group = self.proposed_group
        self._add_descriptions_to_group(self.proposed_group, temperature)
        for description in self.proposed_group.descriptions:
            self.slipnet.activate_node_from_workspace(description.descriptor.name)

    def _add_descriptions_to_group(self, group: Group, temperature: float):
        self._add_description(
            group, self.slipnet["object_category"], self.slipnet["group"]
        )
        string_position = self._get_string_position(group)
        if string_position is not None:
            self._add_description(
                group, self.slipnet["string_position_category"], string_position
            )

        if group.group_category == self.slipnet["sameness_group"] and (
            not group.bonds
            or group.bonds[0].bond_facet == self.slipnet["letter_category"]
        ):
            self._add_description(
                group,
                self.slipnet["letter_category"],
                group.left_object.get_descriptor(self.slipnet["letter_category"]),
            )

        self._add_description(
            group, self.slipnet["group_category"], group.group_category
        )
        if group.direction_category is not None:
            self._add_description(
                group,
                self.slipnet["direction_category"],
                group.direction_category,
            )

        if group.bonds:
            group.bond_facet = group.bonds[0].bond_facet
            self._add_description(group, self.slipnet["bond_facet"], group.bond_facet)
        self._add_description(group, self.slipnet["bond_category"], group.bond_category)

        group_length = len(group.objects)
        if 1 <= group_length <= len(self.slipnet.numbers):
            base_probability = 0.5 ** (
                group_length**3 * (1 - self.slipnet["length"].activation)
            )
            length_description_probability = temperature_adjust(
                base_probability, temperature
            )
            if random.random() < length_description_probability:
                self._add_description(
                    group,
                    self.slipnet["length"],
                    self.slipnet.numbers[group_length - 1],
                )

    def _add_description(self, group: Group, facet, descriptor):
        if descriptor is None:
            return
        description = Description(group, facet, descriptor)
        existing_descriptions = group.descriptions + group.bond_descriptions
        if any(
            getattr(existing, "facet", None) == facet
            and getattr(existing, "descriptor", None) == descriptor
            for existing in existing_descriptions
        ):
            return
        group.add_description(description)

    def _get_string_position(self, group: Group):
        if group.spans_whole_string():
            return self.slipnet["whole"]
        if group.is_leftmost_in_string():
            return self.slipnet["leftmost"]
        if self._is_middle_in_string(group):
            return self.slipnet["middle"]
        if group.is_rightmost_in_string():
            return self.slipnet["rightmost"]
        return None

    @staticmethod
    def _is_middle_in_string(group: Group) -> bool:
        return any(
            neighbour.is_leftmost_in_string() for neighbour in group.left_neighbours
        ) and any(
            neighbour.is_rightmost_in_string() for neighbour in group.right_neighbours
        )
