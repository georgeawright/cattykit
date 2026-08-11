from math import sqrt
from typing import List, Optional

from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.codelets.scout import Scout
from copycat.codelets.strength_testers import RuleStrengthTester
from copycat.tools import select_item_from_list, temperature_adjust_list
from copycat.workspace_object import WorkspaceObject
from copycat.workspace_structures import Description, ExtrinsicDescription, Rule


class RuleScout(Scout):
    """Fills in the rule template "Replace ___ by ___ " by choosing descriptions of
    the changed object in the initial string and its replacement in the modified string.
    If the rule can be made, it proposes it and posts a rule strength tester
    with urgency a function of the conceptual depth of the descriptions."""

    def run(self, temperature: float) -> CodeletResult:
        if not self.workspace.all_replacements_found():
            return Fizzle(FizzleReason.NOT_ALL_REPLACEMENTS_FOUND)
        changed_objects = self.workspace.initial_string.get_changed_objects()
        if len(changed_objects) > 1:
            raise Exception("Cannot solve problems with more than one changed letter.")
        if not changed_objects:
            self._propose_rule(None, None, None, None, temperature=temperature)
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
            initial_object,
            initial_description,
            modified_object,
            modified_description,
            temperature=temperature,
        )
        return Finish()

    def _propose_rule(
        self,
        initial_object: Optional[WorkspaceObject],
        initial_description: Optional[Description],
        modified_object: Optional[WorkspaceObject],
        modified_description: Optional[Description],
        temperature: float,
    ):
        object_category_node = self.slipnet["object_category"]
        if (
            initial_object is None
            and initial_description is None
            and modified_object is None
            and modified_description is None
        ):
            proposed_rule = Rule(self.workspace)
        elif isinstance(modified_description, ExtrinsicDescription):
            proposed_rule = Rule(
                self.workspace,
                object_category_1=initial_object.get_descriptor(object_category_node),
                descriptor_1_facet=initial_description.facet,
                descriptor_1=initial_description.descriptor,
                object_category_2=modified_object.get_descriptor(object_category_node),
                replaced_description_type=modified_description.description_type_related,
                relation=modified_description.relation,
            )
        else:
            proposed_rule = Rule(
                self.workspace,
                object_category_1=initial_object.get_descriptor(object_category_node),
                descriptor_1_facet=initial_description.facet,
                descriptor_1=initial_description.descriptor,
                object_category_2=modified_object.get_descriptor(object_category_node),
                replaced_description_type=modified_description.facet,
                descriptor_2=modified_description.descriptor,
            )
        if initial_description is None:
            urgency = 1.0
        else:
            urgency = sqrt(
                initial_description.conceptual_depth / 2
                + modified_description.conceptual_depth / 2
            )  # square root prevents overly low urgencies for low conceptual depths
        urgency_level = self.coderack.get_urgency_level_from_activation(urgency)
        self.coderack.post(
            RuleStrengthTester(
                urgency_bin=urgency_level,
                coderack=self.coderack,
                slipnet=self.slipnet,
                workspace=self.workspace,
                proposed_rule=proposed_rule,
            ),
            temperature=temperature,
        )

    def _get_initial_description(
        self, initial_object: WorkspaceObject, temperature: float
    ) -> Optional[Description]:
        candidates = self._get_initial_descriptions(initial_object)
        if not candidates:
            return None
        probabilities = temperature_adjust_list(
            [c.conceptual_depth for c in candidates], temperature
        )
        return select_item_from_list(candidates, probabilities)

    def _get_initial_descriptions(
        self, initial_object: WorkspaceObject
    ) -> List[Description]:
        if initial_object.correspondence is None:
            return initial_object.rule_initial_string_descriptions
        initial_descriptions = []
        relevant_target_descriptions = (
            initial_object.correspondence.target.get_relevant_descriptions()
        )
        for d in initial_object.rule_initial_string_descriptions:
            slipped_d = d.apply_slippages(
                initial_object, initial_object.correspondence.slippages
            )
            if any(
                [
                    slipped_d.equates_to(target_description)
                    for target_description in relevant_target_descriptions
                ]
            ):
                initial_descriptions.append(d)
        return initial_descriptions

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
        if not candidates:
            return None
        probabilities = temperature_adjust_list(
            [c.conceptual_depth for c in candidates], temperature
        )
        choice = select_item_from_list(candidates, probabilities)
        if isinstance(choice, ExtrinsicDescription):
            related_descriptor = initial_description.descriptor.get_related_node(
                choice.relation
            )
            if related_descriptor:
                for d in modified_object.descriptions:
                    if d.descriptor == related_descriptor:
                        return d
        return choice
