from typing import List

from copycat.slipnet import Slipnet
from copycat.slipnode import Slipnode
from copycat.snag_exception import SnagException
from copycat.workspace import Workspace
from copycat.workspace_object import WorkspaceObject
from copycat.workspace_objects import Letter


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

    def _get_modified_letters(
        self, obj: WorkspaceObject, description_type: Slipnode
    ) -> List[Letter]:
        pass

    def _get_unmodified_letters(
        self, objects_to_change: List[WorkspaceObject]
    ) -> List[Letter]:
        pass

    def _adjust_letter_positions(self, answer_letters: List[Letter]) -> List[Letter]:
        pass
