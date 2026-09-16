import itertools
from typing import Optional

from cattykit.logging import ModelLogger

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
        self.logger: Optional[ModelLogger] = None
        self.urgency_bin = urgency_bin
        self.coderack = coderack
        self.workspace = workspace
        self.slipnet = slipnet
        self.hash_id = next(Codelet._next_id)

    def __repr__(self):
        return f"<{type(self).__name__} {self.hash_id} in bin {self.urgency_bin}>"

    def __setattr__(self, name: str, value: object) -> None:
        object.__setattr__(self, name, value)
        if name == "logger":
            return
        if self.logger is None:
            return
        self.logger.log("codelet_step", codelet=self, attribute=name)

    def run(self, temperature: float) -> CodeletResult:
        raise NotImplementedError
