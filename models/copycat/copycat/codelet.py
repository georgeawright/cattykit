import itertools

from copycat.codelet_result import CodeletResult


class Codelet:
    _next_id = itertools.count(1)

    def __init__(
        self,
        urgency_bin,
        coderack: "Coderack",
        workspace: "Workspace",
        slipnet: "Slipnet",
    ):
        self.urgency_bin = urgency_bin
        self.coderack = coderack
        self.workspace = workspace
        self.slipnet = slipnet
        self.hash_id = next(Codelet._next_id)

    def __repr__(self):
        return f"<{type(self).__name__} {self.hash_id} in bin {self.urgency_bin}>"

    def run(self, temperature: float) -> CodeletResult:
        """Perform this codelet's model-specific work."""
        raise NotImplementedError
