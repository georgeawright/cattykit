import random
from typing import List, Optional

from copycat.codelets.scouts.correspondence_scout import CorrespondenceScout
from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.concept_mapping import ConceptMapping


class BottomUpCorrespondenceScout(CorrespondenceScout):
    """Chooses an object each from the initial and target strings
    probabilistically by inter-string-salience.
    Finds all concept mappings between nodes at most one link away.
    If any concept mappings can be made between distinguishing descriptors,
    makes a proposed correspondence between the two objects including all the concept mappings
    and posts a correspondence strength tester with urgency a function of the average strength
    of the distinguishing concept mappings."""

    def _get_objects_or_fizzle(self) -> Optional[CodeletResult]:
        self.source = self.workspace.initial_string.choose_object(
            selection_method=lambda x: x.inter_string_salience
        )
        self.target = self.workspace.target_string.choose_object(
            selection_method=lambda x: x.inter_string_salience
        )
        if self.source is None or self.target is None:
            return Fizzle(FizzleReason.NO_OBJECTS)
        return None
