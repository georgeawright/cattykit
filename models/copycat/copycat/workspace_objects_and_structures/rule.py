from __future__ import annotations
import itertools
from typing import List, Optional

import numpy as np

from copycat.concept_mapping import ConceptMapping
from copycat.slipnode import Slipnode

from .workspace_structure import WorkspaceStructure


class Rule(WorkspaceStructure):
    _next_id = itertools.count(1)

    def __init__(
        self,
        workspace: "Workspace",
        source_object_category: Optional[Slipnode] = None,
        source_facet: Optional[Slipnode] = None,
        source_descriptor: Optional[Slipnode] = None,
        target_object_category: Optional[Slipnode] = None,
        target_descriptor: Optional[Slipnode] = None,
        replaced_facet: Optional[Slipnode] = None,
        relation: Optional[Slipnode] = None,
    ):
        super().__init__()
        self.workspace = workspace
        self.source_object_category = source_object_category
        self.source_facet = source_facet
        self.source_descriptor = source_descriptor
        self.target_object_category = target_object_category
        self.target_descriptor = target_descriptor
        self.replaced_facet = replaced_facet
        self.relation = relation
        self.hash_id = next(Rule._next_id)

    def __repr__(self):
        rule_second_half = self.relation if self.relation else self.target_descriptor
        return (
            f"Replace "
            f"{self.replaced_facet} of "
            f"{self.source_descriptor} {self.source_object_category}"
            f" by {rule_second_half}"
        )

    def equates_to(self, other) -> bool:
        if not isinstance(other, Rule):
            return False
        return (
            self.source_object_category,
            self.source_facet,
            self.source_descriptor,
            self.target_object_category,
            self.target_descriptor,
            self.replaced_facet,
            self.relation,
        ) == (
            other.source_object_category,
            other.source_facet,
            other.source_descriptor,
            other.target_object_category,
            other.target_descriptor,
            other.replaced_facet,
            other.relation,
        )

    def expresses_relation(self) -> bool:
        return self.relation is not None

    def specifies_change(self) -> bool:
        return self.source_descriptor is not None

    def apply_slippages(self, slippages: List[ConceptMapping]) -> Rule:
        def _slip(slipnode):
            return None if slipnode is None else slipnode.apply_slippages(slippages)

        return Rule(
            self.workspace,
            _slip(self.source_object_category),
            _slip(self.source_facet),
            _slip(self.source_descriptor),
            _slip(self.target_object_category),
            _slip(self.target_descriptor),
            _slip(self.replaced_facet),
            _slip(self.relation),
        )

    def calculate_internal_strength(self) -> float:
        if not self.specifies_change():
            return 1.0
        source_depth = self.source_descriptor.conceptual_depth
        target_depth = (
            self.relation.conceptual_depth
            if self.expresses_relation()
            else self.target_descriptor.conceptual_depth
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
            if self.source_descriptor not in slipped_descriptors:
                # rule cannot be made
                return 0.0
            shared_descriptor_term = 1.0
        shared_descriptor_weight = (
            (1 - self.source_descriptor.conceptual_depth) * 10
        ) ** 1.4
        depth_diff = abs(source_depth - target_depth)
        depth_mean = (source_depth + target_depth) / 2
        depth_term = 100**0.1 * depth_mean**1.1
        # depth term is rescaled to 0-1.58 to match copycat depth term in 0-158
        diff_term = 1 - depth_diff
        rule_strength = np.average(
            [depth_term, diff_term, shared_descriptor_term],
            weights=[18, 12, shared_descriptor_weight],
        )
        return min(rule_strength, 1.0)

    def calculate_external_strength(self) -> float:
        return self.internal_strength
