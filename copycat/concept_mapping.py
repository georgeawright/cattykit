from __future__ import annotations
from typing import Optional

from .slipnode import Slipnode
from .workspace_object import WorkspaceObject


class ConceptMapping:
    def __init__(
        self,
        description_type_1: Slipnode,
        description_type_2: Slipnode,
        descriptor_1: Slipnode,
        descriptor_2: Slipnode,
        label: Optional[Slipnode],
        object_1: Optional[WorkspaceObject],
        object_2: Optional[WorkspaceObject],
    ):
        self.description_type_1 = description_type_1
        self.description_type_2 = description_type_2
        self.descriptor_1 = descriptor_1
        self.descriptor_2 = descriptor_2
        self.label = label
        self.object_1 = object_1
        self.object_2 = object_2

    @property
    def degree_of_assocation(self) -> float:
        """assumes both descriptors in the mapping are connected in the slipnet
        by at most one slip link. Requires generalization."""
        if self.descriptor_1 == self.descriptor_2:
            return 1.0
        for link in self.descriptor_1.lateral_sliplinks:
            if link.to_node == self.descriptor_2:
                return link.degree_of_association
        return 0.0

    @property
    def conceptual_depth(self) -> float:
        return (
            self.descriptor_1.conceptual_depth + self.descriptor_2.conceptual_depth
        ) / 2

    @property
    def strength(self) -> float:
        return (
            1.0
            if self.degree_of_assocation == 1.0
            else self.degree_of_assocation * max(0.01, self.conceptual_depth**2)
        )

    def is_relevant(self) -> bool:
        return (
            self.description_type_1.is_active() and self.description_type_2.is_active()
        )

    def is_distinguishing(self) -> bool:
        # in Copycat a "whole -> whole" mapping is not distinguishing,
        # the original source code states that a more general definition is desirable
        if self.descriptor_1.name == "whole" and self.descriptor_2.name == "whole":
            return False
        descriptor_1_is_distinguishing = self.object_1.is_distinguished_by(
            self.descriptor_1
        )
        descriptor_2_is_distinguishing = self.object_2.is_distinguished_by(
            self.descriptor_2
        )
        return descriptor_1_is_distinguishing and descriptor_2_is_distinguishing

    def supports(self, other: ConceptMapping) -> bool:
        """Concept-mappings (a -> b) and (c -> d) support each other
        if a is related to c and if b is related to d
        and the a -> b relationship is the same as the c -> d relationship.
        E.g.:
        rightmost->rightmost supports right->right and leftmost->leftmost.
        Slipnet distances are not considered, only links.
        According to original source, this should be changed eventually."""
        if (
            self.descriptor_1 == other.descriptor_1
            and self.descriptor_2 == other.descriptor_2
        ):
            return True
        if not (
            self.descriptor_1.is_related_to(other.descriptor_1)
            or self.descriptor_2.is_related_to(other.descriptor_2)
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
            self.descriptor_1.is_related_to(other.descriptor_1)
            or self.descriptor_2.is_related_to(other.descriptor_2)
        ):
            return False
        if self.label is None or other.label is None:
            return False
        return self.label != other.label
