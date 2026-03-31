from __future__ import annotations
from typing import List, Optional


class Slipnode:
    def __init__(
        self,
        name: str,
        conceptual_depth: float,
        intrinsic_link_length: Optional[float] = None,
        shrunk_link_length: Optional[float] = None,
        description_tester: Optional[callable] = None,
        lateral_sliplinks: Optional[List["Sliplink"]] = None,
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
        self.lateral_sliplinks = (
            lateral_sliplinks if lateral_sliplinks is not None else []
        )
        self.codelets = []
        self.outgoing_links = []

    @property
    def depth_factor(self) -> float:
        return 1 / self.conceptual_depth if self.conceptual_depth > 0 else 0

    def is_active(self) -> bool:
        return self.activation >= 1.0

    def get_related_node(self, relationship_name: str) -> Optional[Slipnode]:
        if relationship_name == "identity":
            return self
        for link in self.outgoing_links:
            if link.type_node.name == relationship_name:
                return link.to_node
        return None
