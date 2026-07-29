import random
from typing import List, Optional

from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.codelets.scout import Scout
from copycat.tools import temperature_adjust_list
from copycat.workspace_object import WorkspaceObject
from copycat.workspace_structures import Description


class RuleScout(Scout):
    """Fills in the rule template "Replace ___ by ___ " by choosing descriptions of
    the changed object in the initial string and its replacement in the modified string.
    If the rule can be made, it proposes it and posts a rule strength tester
    with urgency a function of the conceptual depth of the descriptions."""

    def run(self, temperature: float) -> CodeletResult:
        if self.workspace.null_replacement:
            return Fizzle(FizzleReason.NOT_ALL_REPLACEMENTS_FOUND)
        changed_objects = self.workspace.initial_string.get_changed_objects()
        if len(changed_objects) > 1:
            raise Exception("Cannot solve problems with more than one changed letter.")
        if not changed_objects:
            self._propose_rule(None, None, None, None)
            return Finish()
        initial_object = changed_objects[0]
        initial_description = self._get_initial_description(
            initial_object,
            temperature,
        )
        if initial_description is None:
            return Fizzle(FizzleReason.NO_INITIAL_DESCRIPTIONS)
        modified_object = initial_object.replacement.target
        modified_description = self._get_modified_description(
            modified_object,
            initial_description,
            temperature,
        )
        if modified_description is None:
            return Fizzle(FizzleReason.NO_MODIFIED_DESCRIPTIONS)
        self._propose_rule(
            initial_object, initial_description, modified_object, modified_description
        )

    def _propose_rule(
        self,
        initial_object: Optional[WorkspaceObject],
        initial_description: Optional[Description],
        modified_object: Optional[WorkspaceObject],
        modified_description: Optional[Description],
    ):
        # TODO
        pass

    def _get_initial_description(
        self, initial_object: WorkspaceObject, temperature: float
    ) -> Optional[Description]:
        candidates = self._get_initial_descriptions()
        if not candidates:
            return None
        probabilities = temperature_adjust_list(
            [c.conceptual_depth for c in candidates], temperature
        )
        return random.choices(candidates, weights=probabilities, k=1)[0]

    def _get_initial_descriptions(self) -> List[Description]:
        # TODO
        pass

    def _get_modified_description(
        self,
        modified_object: WorkspaceObject,
        initial_description: Description,
        temperature: float,
    ) -> Optional[Description]:
        candidates = (
            modified_object.extrinsic_descriptions
            + modified_object.rule_modified_string_descriptions
        )
        probabilities = temperature_adjust_list(
            [c.conceptual_depth for c in candidates], temperature
        )
        choice = random.choices(candidates, weights=probabilities, k=1)[0]
        if choice.is_extrinsic_description:
            related_descriptor = initial_description.descriptor.get_related_node(
                choice.relation
            )
            if related_descriptor:
                for d in modified_object.descriptions:
                    if d.descriptor == related_descriptor:
                        return d
        return choice
