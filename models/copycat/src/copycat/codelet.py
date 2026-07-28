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

    def run(self, temperature: float) -> CodeletResult:
        raise NotImplementedError
