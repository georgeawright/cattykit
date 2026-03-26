from copycat.codelets.scouts.description_scout import DescriptionScout


class BottomUpDescriptionScout(DescriptionScout):
    """Chooses an object probabilistically by total salience.
    Chooses a relevant description probabilistically by activation.
    Checks if the descriptor has any "has property" links that are short enough.
    Chooses one of the properties probabilistically by degree of association and activation.
    Proposes a description based on the property and posts a description strength tester
    with urgency a function of the property's activation."""

    pass
