from __future__ import annotations
import random
from typing import Callable, List, Optional

from .tools import temperature_adjust


class Slipnode:
    def __init__(
        self,
        name: str,
        conceptual_depth: float,
        intrinsic_link_length: Optional[float] = None,
        shrunk_link_length: Optional[float] = None,
        description_tester: Optional[Callable] = None,
    ):
        self.name = name
        self.intrinsic_link_length = intrinsic_link_length
        self.intrinsic_degree_of_association = (
            1 - intrinsic_link_length if intrinsic_link_length is not None else None
        )
        self.shrunk_link_length = shrunk_link_length
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
        self.codelets: List["Codelet"] = []

    @property
    def depth_factor(self) -> float:
        return 1 / self.conceptual_depth if self.conceptual_depth > 0 else 0

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
        return self.category_links[0].to_node

    def is_active(self) -> bool:
        return self.activation >= 1.0

    def get_related_node(self, relationship_name: str) -> Optional[Slipnode]:
        if relationship_name == "identity":
            return self
        for link in self.outgoing_links:
            if link.type_node.name == relationship_name:
                return link.to_node
        return None

    def is_related_to(self, other: Slipnode) -> bool:
        return self == other or self.is_linked_to(other)

    def is_linked_to(self, other: Slipnode) -> bool:
        for link in self.outgoing_links:
            if link.to_node == other:
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
            if temperature_adjust(link.degree_of_association, temperature)
            > random.random()
        ]

    def get_possible_descriptors(
        self, workspace_object: "WorkspaceObject"
    ) -> List[Slipnode]:
        return [
            link.to_node
            for link in self.instance_links
            if link.to_node.description_tester(workspace_object)
        ]

    def total_description_type_support(
        self, workspace_string: "WorkspaceString"
    ) -> float:
        return (
            self.local_description_type_support(workspace_string) + self.activation
        ) / 2

    def local_description_type_support(
        self, workspace_string: "WorkspaceString"
    ) -> float:
        description_type_count = sum(
            1 for obj in workspace_string.objects if obj.has_description_type(self)
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
