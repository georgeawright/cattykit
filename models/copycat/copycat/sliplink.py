class Sliplink:
    def __init__(
        self,
        source,
        target,
        type_node,
        fixed_length: int = None,
    ):
        self.source = source
        self.target = target
        self.type_node = type_node
        self.fixed_length = fixed_length
        self._intrinsic_degree_of_association = (
            1 - fixed_length if fixed_length is not None else None
        )

    @property
    def intrinsic_degree_of_association(self):
        return (
            self._intrinsic_degree_of_association
            if self._intrinsic_degree_of_association is not None
            else self.type_node.intrinsic_degree_of_association
        )
