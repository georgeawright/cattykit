from __future__ import annotations
import itertools
from typing import List, Optional

from .slipnode import Slipnode
from .workspace_objects_and_structures.workspace_object import WorkspaceObject


class ConceptMapping:
    _next_id = itertools.count(1)

    def __init__(
        self,
        source_facet: Slipnode,
        target_facet: Slipnode,
        source_descriptor: Slipnode,
        target_descriptor: Slipnode,
        label: Optional[Slipnode],
        source: Optional[WorkspaceObject] = None,
        target: Optional[WorkspaceObject] = None,
    ):
        self.source_facet = source_facet
        self.target_facet = target_facet
        self.source_descriptor = source_descriptor
        self.target_descriptor = target_descriptor
        self.label = label
        self.source = source
        self.target = target
        self.hash_id = next(ConceptMapping._next_id)

    def __repr__(self):
        return (
            f"{self.source_facet}-{self.source_descriptor}"
            f"++{self.label}++>"
            f"{self.target_facet}-{self.target_descriptor}"
        )

    def __eq__(self, other):
        if not isinstance(other, ConceptMapping):
            return NotImplemented
        return (
            self.source_facet,
            self.target_facet,
            self.source_descriptor,
            self.target_descriptor,
            self.label,
            self.source,
            self.target,
        ) == (
            other.source_facet,
            other.target_facet,
            other.source_descriptor,
            other.target_descriptor,
            other.label,
            other.source,
            other.target,
        )

    @property
    def degree_of_assocation(self) -> float:
        """assumes both descriptors in the mapping are connected in the slipnet
        by at most one slip link. Requires generalization."""
        if self.source_descriptor == self.target_descriptor:
            return 1.0
        for link in self.source_descriptor.lateral_sliplinks:
            if link.target == self.target_descriptor:
                return link.degree_of_association
        return 0.0

    @property
    def conceptual_depth(self) -> float:
        return (
            self.source_descriptor.conceptual_depth
            + self.target_descriptor.conceptual_depth
        ) / 2

    @property
    def strength(self) -> float:
        return (
            1.0
            if self.degree_of_assocation == 1.0
            else self.degree_of_assocation * max(0.01, 1 + self.conceptual_depth**2)
        )

    @property
    def slippability(self) -> float:
        degree_of_association = self.degree_of_assocation
        return (
            1.0
            if degree_of_association == 1.0
            else degree_of_association * max(0.01, 1 - self.conceptual_depth**2)
        )

    @property
    def is_slippage(self) -> bool:
        return self.label is None or self.label.name != "identity"

    @property
    def is_opposite(self) -> bool:
        return self.label is not None and self.label.name == "opposite"

    @property
    def is_relevant(self) -> bool:
        return self.source_facet.is_active and self.target_facet.is_active

    @property
    def is_distinguishing(self) -> bool:
        # in Copycat a "whole -> whole" mapping is not distinguishing,
        # the original source code states that a more general definition is desirable
        if (
            self.source_descriptor.name == "whole"
            and self.target_descriptor.name == "whole"
        ):
            return False
        source_descriptor_is_distinguishing = self.source.is_distinguished_by(
            self.source_descriptor
        )
        target_descriptor_is_distinguishing = self.target.is_distinguished_by(
            self.target_descriptor
        )
        return (
            source_descriptor_is_distinguishing and target_descriptor_is_distinguishing
        )

    def supports(self, other: ConceptMapping) -> bool:
        """Concept-mappings (a -> b) and (c -> d) support each other
        if a is related to c and if b is related to d
        and the a -> b relationship is the same as the c -> d relationship.
        E.g.:
        rightmost->rightmost supports right->right and leftmost->leftmost.
        Slipnet distances are not considered, only links.
        According to original source, this should be changed eventually."""
        if (
            self.source_descriptor == other.source_descriptor
            and self.target_descriptor == other.target_descriptor
        ):
            return True
        if not (
            self.source_descriptor.is_related_to(other.source_descriptor)
            or self.target_descriptor.is_related_to(other.target_descriptor)
        ):
            return False
        if self.label is None or other.label is None:
            return False
        return self.label == other.label

    def is_incompatible_with(self, other: ConceptMapping) -> bool:
        """Concept-mappings (a -> b) and (c -> d) are incompatible
        if a is related to c or if b is related to d,
        and the relationships a -> b and c -> d are different.
        E.g., rightmost -> leftmost is incompatible with right -> right,
        since rightmost is linked to right,
        but the relationships (opposite and identity) are different.
        Slipnet distances are not considered, only slipnet links.
        According to original source, this should be changed eventually."""
        if not (
            self.source_descriptor.is_related_to(other.source_descriptor)
            or self.target_descriptor.is_related_to(other.target_descriptor)
        ):
            return False
        if self.label is None or other.label is None:
            return False
        return self.label != other.label

    def contradicts(self, other: ConceptMapping) -> bool:
        return (
            self.source_descriptor == other.source_descriptor
            and self.target_descriptor != other.target_descriptor
        ) or (
            self.target_descriptor == other.target_descriptor
            and self.source_descriptor != other.source_descriptor
        )

    def get_symmetric_version(self) -> Optional[ConceptMapping]:
        if self.label is not None and self.label.name == "identity":
            return self
        reverse_label = None
        for link in self.target_descriptor.outgoing_links:
            if link.target == self.source_descriptor:
                reverse_label = link.label
                break
        if reverse_label != self.label:
            return None
        return ConceptMapping(
            source_facet=self.target_facet,
            target_facet=self.source_facet,
            source_descriptor=self.target_descriptor,
            target_descriptor=self.source_descriptor,
            label=reverse_label,
            source=self.source,
            target=self.target,
        )
