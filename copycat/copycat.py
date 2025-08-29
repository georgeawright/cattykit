class Copycat:
    def __init__(self):
        pass

    def run(self):
        pass

    def update(self):
        """Update values of workspace structures and slipnet activations."""
        pass

    def step(self):
        """Run a single codelet."""

    def handle_snag(self):
        """If there is a snag in building the answer:
        - delete all proposed structures,
        - empty coderack,
        - raise and clamp temperature,
        - clamp activation of all descriptions of the offending object."""

    def delete_answer(self):
        pass
