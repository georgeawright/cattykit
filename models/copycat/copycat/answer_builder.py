from typing import List

from copycat.slipnet import Slipnet
from copycat.slipnode import Slipnode
from copycat.snag_exception import SnagException
from copycat.workspace import Workspace
from copycat.workspace_object import WorkspaceObject
from copycat.workspace_objects import Group, Letter
from copycat.workspace_structures import Description


class AnswerBuilder:
    def __init__(self, slipnet: Slipnet, workspace: Workspace):
        self.slipnet = slipnet
        self.workspace = workspace

    def build(self):
        objects_to_change = self._get_objects_to_change()
        description_type = self.workspace.translated_rule.replaced_description_type
        answer_letters = [
            self._get_modified_letters(obj, description_type)
            for obj in self.workspace.target_string.objects
            if obj in objects_to_change
        ] + self._get_unmodified_letters(objects_to_change)
        if self.workspace.changed_length_group:
            answer_letters = self._adjust_letter_positions(answer_letters)
        self.workspace.answer_string.letters = answer_letters

    def _get_objects_to_change(self) -> List[WorkspaceObject]:
        if not self.workspace.translated_rule.specifies_change():
            return []
        objects_to_change = []
        rule_facet = self.workspace.translated_rule.descriptor_1_facet
        rule_descriptor = self.workspace.translated_rule.descriptor_1
        rule_obj_category = self.workspace.translated_rule.object_category_1
        for obj in self.workspace.target_string.objects:
            if obj.get_descriptor(self.slipnet["object_category"]) != rule_obj_category:
                continue
            if obj.get_descriptor(rule_facet) == rule_descriptor:
                objects_to_change.append(obj)
                continue
            tester = self.workspace.translated_rule.descriptor_1.description_tester
            if tester is not None and tester(obj):
                description = Description(obj, rule_facet, rule_descriptor)
                obj.add_description()
                objects_to_change.append(obj)
        if (
            rule_facet != self.slipnet["string_position_category"]
            and len(objects_to_change) <= 1
        ):
            return objects_to_change
        changed_object_correspondence = next(
            obj for obj in self.workspace.initial_string.objects if obj.is_changed
        ).correspondence
        if (
            changed_object_correspondence is not None
            and changed_object_correspondence.target in objects_to_change
        ):
            return [changed_object_correspondence.target]
        return next(
            obj
            for obj in objects_to_change
            if (
                obj.group is None
                or obj.group.get_descriptor(self.slipnet["string_position_category"])
                != rule_descriptor
            )
        )

    def _get_modified_letters(
        self, obj: WorkspaceObject, description_type: Slipnode
    ) -> List[Letter]:
        if isinstance(obj, Letter):
            return self._get_modified_letters_from_letter(obj, description_type)
        return self._get_modified_letters_from_group(obj, description_type)

    def _get_modified_letters_from_letter(
        self, letter: Letter, description_type: Slipnode
    ) -> List[Letter]:
        modified_letters = []
        new_descriptor = self._get_new_descriptor(letter, description_type)
        if new_descriptor is None:
            self.workspace.snag_objects.append(letter)
            raise SnagException
        if description_type == self.slipnet["letter_category"]:
            new_letter = Letter(
                self.workspace.answer_string, new_descriptor, letter.left_position
            )
            modified_letters.append(new_letter)
        else:
            self.workspace.snag_objects.append(letter)
            raise SnagException
        return modified_letters

    def _get_modified_letters_from_group(
        self, group: Group, description_type: Slipnode
    ) -> List[Letter]:
        """If letter category is directed, modify all letters.
        If length is directed, add or subtract letters."""
        modified_letters = []
        if description_type == self.slipnet["letter_category"]:
            return self._get_modified_letters_from_letter_group(group)
        return self._get_modified_letters_from_length_group(group)

    def _get_modified_letters_from_letter_group(self, group: Group) -> List[Letter]:
        pass

    def _get_modified_letters_from_length_group(self, group: Group) -> List[Letter]:
        """Original source notes this may not work if group contains groups."""
        pass

    def _get_unmodified_letters(
        self, objects_to_change: List[WorkspaceObject]
    ) -> List[Letter]:
        pass

    def _adjust_letter_positions(self, answer_letters: List[Letter]) -> List[Letter]:
        pass
