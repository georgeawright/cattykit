class Sliplink:
    def __init__(
        self,
        from_node,
        to_node,
        type_node,
        fixed_length: int = None,
    ):
        self.from_node = from_node
        self.to_node = to_node
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
