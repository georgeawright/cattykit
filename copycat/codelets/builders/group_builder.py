from copycat.codelets.builder import Builder
from copycat.tools import structure_beats_structures
from copycat.workspace_objects import Group


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

    def run(self, temperature: float):
        workspace_string = self.proposed_group.string
        existing_group = workspace_string.get_group_if_present(self.proposed_group)
        if existing_group:
            self._activate_group_descriptors(existing_group)
            self._transfer_descriptions(self.proposed_group, existing_group)
            workspace_string.delete_proposed_group(self.proposed_group)
            return
        if not self._all_bonds_still_exist(workspace_string):
            workspace_string.delete_proposed_group(self.proposed_group)
            return
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
                return
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
                return
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
                return
        self._break_incompatible_structures(
            incompatible_groups, incompatible_correspondences
        )
        self._build_group()

    def _activate_group_descriptors(self, group: Group):
        for description in group.descriptions:
            self.slipnet.activate_node_from_workspace(description.descriptor.name)

    def _transfer_descriptions(self, from_group: Group, to_group: Group):
        for description in from_group.descriptions:
            if to_group.has_description(description):
                continue
            new_description = description.copy()
            new_description.argument_object = to_group
            to_group.add_description(description)

    def _all_bonds_still_exist(self, workspace_string: "WorkspaceString") -> bool:
        for bond in self.proposed_group.bonds:
            if (
                bond not in workspace_string.bonds
                or bond.get_flipped_version() not in workspace_string.bonds
            ):
                return False
        return True

    def _get_incompatible_groups(self):
        return [
            obj.group
            for obj in self.proposed_group.objects
            if obj.group and obj.group != self.proposed_group
        ]

    def _get_incompatible_correspondences(self):
        incompatible_correspondences = []
        for obj in self.proposed_group.objects:
            if obj.correspondence and self._is_incompatible_correspondence(
                obj.correspondence
            ):
                incompatible_correspondences.append(obj.correspondence)
        return incompatible_correspondences

    def _is_incompatible_correspondence(self, correspondence):
        # TODO
        pass

    def _break_incompatible_structures(
        self, incompatible_groups, incompatible_correspondences
    ):
        # TODO
        for group in incompatible_groups:
            self.workspace.break_group(group)
        for correspondence in incompatible_correspondences:
            self.workspace.break_correspondence(correspondence)

    def _build_group(self):
        # TODO
        pass
