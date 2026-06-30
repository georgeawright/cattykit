from typing import List

from copycat.codelets.scout import Scout
from copycat.concept_mapping import ConceptMapping


class CorrespondenceScout(Scout):
    """A correspondence scout codelet looks for evidence of a correspondence.
    If possible, it makes a proposed correspondence and posts a
    correspondence strength tester."""

    def propose_correspondence(
        self,
        object_1: "WorkspaceObject",
        object_2: "WorkspaceObject",
        concept_mappings: List[ConceptMapping],
        object_2_flipped: bool,
    ):
        pass
