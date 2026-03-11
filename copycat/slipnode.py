class Slipnode:
    def __init__(
        self,
        name: str,
        intrinsic_link_length: float,  # intrinsic length of links of this node type
        shrunk_link_length: float,
        conceptual_depth: float,
        description_tester: callable,  # tests if this node can describe an object
    ):
        self.name = name
        self.intrinsic_link_length = intrinsic_link_length
        self.shrunk_link_length = shrunk_link_length
        self.conceptual_depth = conceptual_depth
        self.description_tester = description_tester
        self.activation = 0
        self.activation_buffer = 0
        self.clamp = False
        self.codelets = []

    @property
    def depth_factor(self) -> float:
        return 1 / self.conceptual_depth if self.conceptual_depth > 0 else 0

    def is_active(self) -> bool:
        return self.activation >= 1.0
