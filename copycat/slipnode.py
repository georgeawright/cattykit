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

    def get_similar_has_property_links(self, temperature: float) -> List["Sliplink"]:
        return [
            link
            for link in self.has_property_links
            if temperature_adjust(link.degree_of_association, temperature)
            > random.random()
        ]
