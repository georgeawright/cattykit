from typing import List

from copycat.workspace_structures import Correspondence
from copycat.codelets.scout import Scout
from copycat.codelets.strength_testers import CorrespondenceStrengthTester
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
        proposed_correspondence = Correspondence(
            self.workspace, object_1, object_2, concept_mappings
        )
        proposed_correspondence.proposal_level = 1
        distinguishing_mappings = proposed_correspondence.get_distinguishing_mappings()
        for mapping in distinguishing_mappings:
            self.slipnet.activate_node_from_workspace(mapping.description_type_1.name)
            self.slipnet.activate_node_from_workspace(mapping.descriptor_1.name)
            self.slipnet.activate_node_from_workspace(mapping.description_type_2.name)
            self.slipnet.activate_node_from_workspace(mapping.descriptor_2.name)
        self.workspace.add_proposed_correspondence(proposed_correspondence)
        urgency = sum(mapping.strength for mapping in distinguishing_mappings) / len(
            distinguishing_mappings
        )
        urgency_bin = self.coderack.get_urgency_level_from_activation(urgency)
        self.coderack.post(
            CorrespondenceStrengthTester(
                urgency_bin=urgency_bin,
                coderack=self.coderack,
                slipnet=self.slipnet,
                workspace=self.workspace,
                proposed_correspondence=proposed_correspondence,
                object_2_flipped=object_2_flipped,
            )
        )
