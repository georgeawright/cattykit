from copycat.codelets.scouts.correspondence_scout import CorrespondenceScout


class BottomUpCorrespondenceScout(CorrespondenceScout):
    """Chooses an object each from the initial and target strings
    probabilistically by inter-string-salience.
    Finds all concept mappings between nodes at most one link away.
    If any concept mappings can be made between distinguishing descriptors,
    makes a proposed correspondence between the two objects including all the concept mappings
    and posts a correspondence strength tester with urgency a function of the average strength
    of the distinguishing concept mappings."""

    def __init__(self, urgency_bin: int):
        self.urgency_bin = urgency_bin
