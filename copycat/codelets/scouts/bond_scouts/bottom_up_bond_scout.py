from copycat.codelets.scouts.bond_scout import BondScout


class BottomUpBondScout(BondScout):
    """Chooses an object and a neighbour probabilistically by intra-string-salience.
    Chooses a bond facet (letter category or length) probabilistically by relevance in string.
    If there can be a bond between the two descriptors of this facet,
    posts a bond strength tester with urgency a function of the degree of association
    of bonds of the bond category."""

    def __init__(self, urgency_bin: int):
        self.urgency_bin = urgency_bin
