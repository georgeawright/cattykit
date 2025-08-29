from copycat.codelets.scouts import BondScout


class BottomUpBondScount(BondScout):
    """Chooses an object and a neighbour probabilistically by intra-string-salience.
    Chooses a bond facet (letter category or length) probabilistically by relevance in string.
    If there can be a bond between the two descriptors of this facet,
    poses a bond strength tester with urgency a function of the degree of association
    of bonds of the bond category."""

    raise NotImplementedError
