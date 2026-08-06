class Sliplink:
    def __init__(
        self,
        source,
        target,
        label,
        fixed_length: int = None,
        is_category_link: bool = False,
        is_instance_link: bool = False,
        is_has_property_link: bool = False,
        is_lateral_sliplink: bool = False,
        is_lateral_non_sliplink: bool = False,
    ):
        self.source = source
        self.target = target
        self.label = label
        self.fixed_length = fixed_length
        self._intrinsic_degree_of_association = (
            1 - fixed_length if fixed_length is not None else None
        )
        self.is_category_link = is_category_link
        self.is_instance_link = is_instance_link
        self.is_has_property_link = is_has_property_link
        self.is_lateral_sliplink = is_lateral_sliplink
        self.is_lateral_non_sliplink = is_lateral_non_sliplink

    def __repr__(self):
        if self.label is None:
            return f"{self.source} ~~~~> {self.target}"
        return f"{self.source} ~~ {self.label} ~~> {self.target}"

    @property
    def degree_of_association(self):
        return (
            1 - self.fixed_length
            if self.fixed_length is not None
            else self.label.degree_of_association
        )

    @property
    def intrinsic_degree_of_association(self):
        return (
            self._intrinsic_degree_of_association
            if self._intrinsic_degree_of_association is not None
            else self.label.intrinsic_degree_of_association
        )
