from copycat.codelet_result import CodeletResult


class Codelet:
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

    def __repr__(self):
        return f"<{type(self).__name__} in bin {self.urgency_bin}>"

    def run(self, temperature: float) -> CodeletResult:
        raise NotImplementedError
