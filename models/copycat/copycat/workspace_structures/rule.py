from __future__ import annotations
import itertools
from typing import List, Optional

import numpy as np

from copycat.concept_mapping import ConceptMapping
from copycat.slipnode import Slipnode
from copycat.workspace_structure import WorkspaceStructure


class Rule(WorkspaceStructure):
    _next_id = itertools.count(1)

    def __init__(
        self,
        workspace: "Workspace",
        object_category_1: Optional[Slipnode] = None,
        descriptor_1_facet: Optional[Slipnode] = None,
        descriptor_1: Optional[Slipnode] = None,
        object_category_2: Optional[Slipnode] = None,
        descriptor_2: Optional[Slipnode] = None,
        replaced_description_type: Optional[Slipnode] = None,
        relation: Optional[Slipnode] = None,
    ):
        self.workspace = workspace
        self.object_category_1 = object_category_1
        self.descriptor_1_facet = descriptor_1_facet
        self.descriptor_1 = descriptor_1
        self.object_category_2 = object_category_2
        self.descriptor_2 = descriptor_2
        self.replaced_description_type = replaced_description_type
        self.relation = relation
        self.hash_id = next(Rule._next_id)

    def __repr__(self):
        rule_second_half = self.relation if self.relation else self.descriptor_2
        return (
            f"Replace "
            f"{self.descriptor_1_facet} of {self.descriptor_1} {self.object_category_1}"
            f" by {rule_second_half}"
        )

    def equates_to(self, other) -> bool:
        return (
            self.object_category_1,
            self.descriptor_1_facet,
            self.descriptor_1,
            self.object_category_2,
            self.descriptor_2,
            self.replaced_description_type,
            self.relation,
        ) == (
            other.object_category_1,
            other.descriptor_1_facet,
            other.descriptor_1,
            other.object_category_2,
            other.descriptor_2,
            other.replaced_description_type,
            other.relation,
        )

    def expresses_relation(self) -> bool:
        return self.relation is not None

    def specifies_change(self) -> bool:
        return self.descriptor_1 is not None

    def apply_slippages(self, slippages: List[ConceptMapping]) -> Rule:
        def _slip(slipnode):
            return None if slipnode is None else slipnode.apply_slippages(slippages)

        return Rule(
            _slip(self.object_category_1),
            _slip(self.descriptor_1_facet),
            _slip(self.descriptor_1),
            _slip(self.object_category_2),
            _slip(self.descriptor_2),
            _slip(self.replaced_description_type),
            _slip(self.relation),
        )

    def calculate_internal_strength(self) -> float:
        if not self.specifies_change():
            return 1.0
        source_depth = self.descriptor_1.conceptual_depth
        target_depth = (
            self.relation.conceptual_depth
            if self.expresses_relation()
            else self.descriptor_2.conceptual_depth
        )
        source_changed_object = next(
            obj
            for obj in self.workspace.initial_string.objects
            if obj.is_changed_letter
        )
        source_correspondee = source_changed_object.get_correspondee()
        if source_correspondee is None:
            shared_descriptor_term = 0
        else:
            slipped_descriptors = [
                d.apply_slippages(
                    source_correspondee, self.workspace.slippages
                ).descriptor
                for d in source_correspondee.get_relevant_descriptions()
            ]
            shared_descriptor_term = (
                1.0 if self.descriptor_1 in slipped_descriptors else 0.0
            )
        shared_descriptor_weight = 1 - self.descriptor_1.conceptual_depth**1.4
        depth_diff = abs(source_depth - target_depth)
        depth_mean = (source_depth + target_depth) / 2
        depth_term = depth_mean**1.1
        diff_term = 1 - depth_diff
        rule_strength = np.average(
            [depth_term, diff_term, shared_descriptor_term],
            weights=[0.18, 0.12, shared_descriptor_weight],
        )
        return min(rule_strength, 1.0)

    def calculate_external_strength(self) -> float:
        return self.internal_strength
