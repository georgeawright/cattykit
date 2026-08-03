from typing import List

from copycat.concept_mapping import ConceptMapping
from copycat.codelets.builder import Builder
from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.tools import structure_beats_structures
from copycat.workspace_structures.bond import Bond


class BondBuilder(Builder):
    """A bond builder tries to build the proposed bond.
    It fights with competitors if necessary.
    """

    def __init__(
        self,
        urgency_bin: int,
        coderack: "Coderack",
        workspace: "Workspace",
        slipnet: "Slipnet",
        proposed_bond: Bond,
    ):
        super().__init__(
            urgency_bin=urgency_bin,
            coderack=coderack,
            workspace=workspace,
            slipnet=slipnet,
            proposed_structure=proposed_bond,
        )
        self.proposed_bond = proposed_bond

    def run(self, temperature: float) -> CodeletResult:
        if (
            self.proposed_bond.source not in self.workspace.objects
            or self.proposed_bond.target not in self.workspace.objects
        ):
            return Fizzle(FizzleReason.OBJECTS_NO_LONGER_EXIST)
        if self.proposed_bond in self.proposed_bond.string.bonds:
            return Fizzle(FizzleReason.STRUCTURE_ALREADY_EXISTS)
        self.proposed_bond.string.delete_proposed_bond(self.proposed_bond)
        incompatible_bonds = self._get_incompatible_bonds()
        if incompatible_bonds:
            print(self.proposed_bond)
            print(incompatible_bonds)
            fight_result = structure_beats_structures(
                self.proposed_bond, 1, incompatible_bonds, 1, temperature=temperature
            )
            if not fight_result:
                return Fizzle(FizzleReason.INCOMPATIBLE_STRUCTURES_WON)
        incompatible_groups = self._get_incompatible_groups()
        if incompatible_groups:
            fight_result = structure_beats_structures(
                self.proposed_bond,
                1,
                incompatible_groups,
                max([g.letter_span for g in incompatible_groups]),
                temperature=temperature,
            )
            if not fight_result:
                return Fizzle(FizzleReason.INCOMPATIBLE_STRUCTURES_WON)
        incompatible_correspondences = self._get_incompatible_correspondences()
        if incompatible_correspondences:
            fight_result = structure_beats_structures(
                self.proposed_bond,
                2,
                incompatible_correspondences,
                3,
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
        self.build_bond()
        return Finish()

    def build_bond(self):
        self.proposed_bond.string.add_bond(self.proposed_bond)
        self.proposed_bond.left_object.outgoing_bonds.append(self.proposed_bond)
        self.proposed_bond.right_object.incoming_bonds.append(self.proposed_bond)
        if self.proposed_bond.is_sameness_bond:
            self.proposed_bond.right_object.outgoing_bonds.append(self.proposed_bond)
            self.proposed_bond.left_object.incoming_bonds.append(self.proposed_bond)
        self.proposed_bond.left_object.right_bond = self.proposed_bond
        self.proposed_bond.right_object.left_bond = self.proposed_bond
        self.slipnet.activate_node_from_workspace(self.proposed_bond.bond_category.name)

    def _get_incompatible_bonds(self) -> List[Bond]:
        incompatble_bonds = []
        if self.proposed_bond.left_object.right_bond is not None:
            incompatble_bonds.append(self.proposed_bond.left_object.right_bond)
        if (
            self.proposed_bond.right_object.left_bond is not None
            and self.proposed_bond.right_object.left_bond
            != self.proposed_bond.left_object.right_bond
        ):
            incompatble_bonds.append(self.proposed_bond.right_object.left_bond)
        return incompatble_bonds

    def _get_incompatible_groups(self) -> List["Group"]:
        return [
            group
            for group in self.proposed_bond.string.groups
            if group.has_recursive_member(self.proposed_bond.left_object)
            and group.has_recursive_member(self.proposed_bond.right_object)
        ]

    def _get_incompatible_correspondences(self) -> List["Correspondence"]:
        if self.proposed_bond.direction_category is None:
            return []
        incompatible_correspondences = []
        if self.proposed_bond.is_leftmost_in_string():
            correspondence = self.proposed_bond.left_object.correspondence
            if correspondence is not None and self._correspondence_is_incompatible(
                correspondence
            ):
                incompatible_correspondences.append(correspondence)
        if self.proposed_bond.is_rightmost_in_string():
            correspondence = self.proposed_bond.right_object.correspondence
            if correspondence is not None and self._correspondence_is_incompatible(
                correspondence
            ):
                incompatible_correspondences.append(correspondence)
        return incompatible_correspondences

    def _correspondence_is_incompatible(self, correspondence: "Correspondence") -> bool:
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
        other_object = correspondence.other_object(self.proposed_bond.left_object)
        if other_object.is_leftmost_in_string():
            other_bond = other_object.right_bond
        elif other_object.is_rightmost_in_string():
            other_bond = other_object.left_bond
        else:
            return False
        if other_bond is None or other_bond.direction_category is None:
            return False
        bond_concept_mapping = ConceptMapping(
            description_type_1=self.slipnet.direction_category,
            description_type_2=self.slipnet.direction_category,
            descriptor_1=self.proposed_bond.direction_category,
            descriptor_2=other_bond.direction_category,
            label=None,
            object_1=None,
            object_2=None,
        )
        if bond_concept_mapping.is_incompatible_with(
            string_position_category_concept_mapping
        ):
            return True
        else:
            return False
