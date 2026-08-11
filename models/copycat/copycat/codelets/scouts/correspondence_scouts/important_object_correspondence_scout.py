import random
from typing import List, Optional

from copycat.codelets.scouts.correspondence_scout import CorrespondenceScout
from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.concept_mapping import ConceptMapping
from copycat.tools import temperature_adjust


class ImportantObjectCorrespondenceScout(CorrespondenceScout):
    """Chooses an object from the intial string probabilistically by importance.
    Probabilistically picks a description of the object and looks for an object
    in the target string with the same description modulo the appropriate slippage
    if any of the slippages currently in the workspace apply.
    If an object is found, it finds all the concept mappings between nodes at most
    one link away.
    If any are found, proposes a correspondence between the objects with all the
    concept mappings and posts a correspondence strength tester with urgency a
    function of the average strength of the distinguishing concept mappings."""

    def _get_objects_or_fizzle(self, temperature: float) -> Optional[CodeletResult]:
        self.source = self.workspace.initial_string.choose_object(
            temperature=temperature, method=lambda x: x.relative_importance
        )
        if self.source is None:
            return Fizzle(FizzleReason.NO_OBJECTS)
        source_description = (
            self.source.choose_relevant_description_by_conceptual_depth()
        )
        if source_description is None:
            return Fizzle(FizzleReason.NO_RELEVANT_DESCRIPTIONS)
        source_descriptor = source_description.descriptor
        target_descriptor = next(
            (
                slippage.descriptor_2
                for slippage in self.workspace.slippages
                if slippage.descriptor_1 == source_descriptor
            ),
            source_descriptor,
        )
        target_candidates = [
            obj
            for obj in self.workspace.target_string.objects
            if any(d.descriptor == target_descriptor for d in obj.relevant_descriptions)
        ]
        if not target_candidates:
            return Fizzle(FizzleReason.NO_OBJECTS_WITH_DESCRIPTOR)
        self.target = random.choices(
            target_candidates,
            weights=[obj.inter_string_salience for obj in target_candidates],
        )[0]
