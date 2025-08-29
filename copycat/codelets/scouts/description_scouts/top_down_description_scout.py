from copycat.codelets.scouts import DescriptionScout


class TopDownDescriptionScout(DescriptionScout):
    """Chooses an object probabilistically by total salience.
    Checks if the the object fits any descriptions in the description type's instances.
    Proposes a description based on the property and posts a description strength tester
    with urgency a function of the descriptor's activation."""

    raise NotImplementedError
