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

    def _get_objects_or_fizzle(self) -> Optional[CodeletResult]:
        self.object_1 = self.workspace.initial_string.choose_object(
            selection_method=lambda x: x.relative_importance
        )
        if self.object_1 is None:
            return Fizzle(FizzleReason.NO_OBJECTS)
        object_1_description = (
            self.object_1.choose_relevant_description_by_conceptual_depth()
        )
        if object_1_description is None:
            return Fizzle(FizzleReason.NO_RELEVANT_DESCRIPTIONS)
        object_1_descriptor = object_1_description.descriptor
        object_2_descriptor = next(
            (
                slippage.descriptor2
                for slippage in self.workspace.slippages
                if slippage.descriptor1 == object_1_descriptor
            ),
            object_1_descriptor,
        )
        object_2_candidates = [
            obj
            for obj in self.workspace.target_string.objects
            if any(
                d.descriptor == object_2_descriptor for d in obj.relevant_descriptions
            )
        ]
        if not object_2_candidates:
            return Fizzle(FizzleReason.NO_OBJECTS_WITH_DESCRIPTOR)
        self.object_2 = random.choices(
            object_2_candidates,
            weights=[obj.inter_string_salience for obj in object_2_candidates],
        )[0]
