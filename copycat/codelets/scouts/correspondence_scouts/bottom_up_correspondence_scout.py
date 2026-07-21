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
        self.object_1 = self.workspace.initial_string.choose_object(
            selection_method=lambda x: x.inter_string_salience
        )
        self.object_2 = self.workspace.target_string.choose_object(
            selection_method=lambda x: x.inter_string_salience
        )
        if self.object_1 is None or self.object_2 is None:
            return Fizzle(FizzleReason.NO_OBJECTS)
        return None

    def _get_concept_mappings(
        self, object_1: "WorkspaceObject", object_2: "WorkspaceObject"
    ) -> List[ConceptMapping]:
        return [
            ConceptMapping(
                description_type_1=desc_1.facet,
                description_type_2=desc_2.facet,
                descriptor_1=desc_1.descriptor,
                descriptor_2=desc_2.descriptor,
                object_1=object_1,
                object_2=object_2,
            )
            for desc_1 in object_1.descriptions
            for desc_2 in object_2.descriptions
            if desc_1.facet == desc_2.facet
            and (
                desc_1.descriptor == desc_2.descriptor
                or desc_1.descriptor.is_linked_to(desc_2.descriptor)
            )
        ]
