from copycat.codelets.scouts.correspondence_scout import CorrespondenceScout


class ImportantObjectCorrespondenceScout(CorrespondenceScout):
    """Chooses an object from the intial string probabilistically by importance.
    Probabilistically picks a description of the object and looks for an object
    in the target string with the same description modulo the appropriate slippage
    if any of the slippages currently in the workspace apply.
    If an object is found, it finds all the concept mappings between nodes at most
    one link away.
    If any are found, proposes a correspondence between the objects with all the
    concept mappings and posts a correspondence strength tester with urgency a
    function of the average strength of the distinguishing concept mappings."""

    pass
