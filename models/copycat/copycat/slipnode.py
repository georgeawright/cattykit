from __future__ import annotations
from math import sqrt
import random
from typing import Callable, List, Optional

from .tools import temperature_adjust_probability


class Slipnode:
    def __init__(
        self,
        name: str,
        conceptual_depth: float,
        intrinsic_link_length: Optional[float] = None,
        shrunk_link_length: Optional[float] = None,
        description_tester: Optional[Callable] = None,
        codelets: Optional[List[str]] = None,
    ):
        self.name = name
        self.intrinsic_link_length = intrinsic_link_length
        self.intrinsic_degree_of_association = (
            1 - intrinsic_link_length if intrinsic_link_length is not None else None
        )
        self.shrunk_link_length = (
            shrunk_link_length
            if shrunk_link_length is not None
            else intrinsic_link_length * 0.4
            if intrinsic_link_length is not None
            else None
        )
        self.conceptual_depth = conceptual_depth
        self.description_tester = description_tester
        self.activation = 0
        self.activation_buffer = 0
        self.clamp = False
        self.category_links: List["Sliplink"] = []
        self.instance_links: List["Sliplink"] = []
        self.has_property_links: List["Sliplink"] = []
        self.lateral_sliplinks: List["Sliplink"] = []
        self.lateral_non_sliplinks: List["Sliplink"] = []
        self.incoming_links: List["Sliplink"] = []
        self.codelets = codelets if codelets is not None else []

    def __repr__(self):
        return self.name.upper()

    def __int__(self):
        try:
            return {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}[self.name]
        except KeyError:
            raise ValueError("Slipnode does not represent an integer category")

    @property
    def degree_of_association(self) -> float:
        """The degree of association encoded in the links this node labels."""
        return (
            1 - self.shrunk_link_length
            if self.is_active()
            else 1 - self.intrinsic_link_length
        )

    @property
    def bond_degree_of_association(self) -> float:
        """The degree of association bonds of this category have."""
        return min(1, sqrt(self.degree_of_association) * 1.1)

    @property
    def outgoing_links(self) -> List["Sliplink"]:
        return (
            self.category_links
            + self.instance_links
            + self.has_property_links
            + self.lateral_sliplinks
            + self.lateral_non_sliplinks
        )

    @property
    def category(self) -> Optional["Slipnode"]:
        """Assumes at most one category link per node."""
        if not self.category_links:
            return None
        return self.category_links[0].target

    def is_active(self) -> bool:
        return self.activation >= 1.0

    def get_related_node(self, relationship_name: str) -> Optional[Slipnode]:
        if relationship_name == "identity":
            return self
        for link in self.outgoing_links:
            if link.label is not None and link.label.name == relationship_name:
                return link.target
        return None

    def is_related_to(self, other: Slipnode) -> bool:
        return self == other or self.is_linked_to(other)

    def is_linked_to(self, other: Slipnode) -> bool:
        for link in self.outgoing_links:
            if link.target == other:
                return True
        return False

    def is_sliplinked_to(self, other: Slipnode) -> bool:
        for link in self.lateral_sliplinks:
            if link.target == other:
                return True
        return False

    def is_directed(self) -> bool:
        return self.name in (
            "predecessor",
            "successor",
            "predecessor_group",
            "successor_group",
        )

    def get_similar_has_property_links(self, temperature: float) -> List["Sliplink"]:
        return [
            link
            for link in self.has_property_links
            if temperature_adjust_probability(link.degree_of_association, temperature)
            > random.random()
        ]

    def get_possible_descriptors(
        self, workspace_object: "WorkspaceObject"
    ) -> List[Slipnode]:
        return [
            link.target
            for link in self.instance_links
            if link.target.description_tester
            and link.target.description_tester(workspace_object)
        ]

    def get_total_description_type_support(
        self, workspace_string: "WorkspaceString"
    ) -> float:
        return (
            self.get_local_description_type_support(workspace_string) + self.activation
        ) / 2

    def get_local_descriptor_support(
        self, workspace_string: "WorkspaceString", object_category: Slipnode
    ) -> float:
        relevant_objects = (
            workspace_string.letters
            if object_category.name == "letter"
            else workspace_string.groups
        )
        descriptor_count = sum(
            1
            for obj in relevant_objects
            if self in [d.descriptor for d in obj.descriptions]
        )
        return descriptor_count / len(relevant_objects) if relevant_objects else 0

    def get_local_description_type_support(
        self, workspace_string: "WorkspaceString"
    ) -> float:
        description_type_count = sum(
            1
            for obj in workspace_string.objects
            if self in [d.facet for d in obj.descriptions]
        )
        return (
            description_type_count / len(workspace_string.objects)
            if workspace_string.objects
            else 0
        )

    def apply_slippages(self, slippages: list) -> Slipnode:
        for slippage in slippages:
            if slippage.descriptor_1 == self:
                return slippage.descriptor_2
        return self
