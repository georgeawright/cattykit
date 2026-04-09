from copycat.codelets import Builder
from copycat.workspace_structures.bond import Bond


class BondBuilder(Builder):
    """A bond builder tries to build the proposed bond.
    It fights with competitors if necessary.
    """

    def __init__(
        self,
        urgency_bin: int,
        coderack: "Coderack",
        workspace: "Workspace",
        slipnet: "Slipnet",
        proposed_bond: Bond,
    ):
        super().__init__(
            urgency_bin=urgency_bin,
            coderack=coderack,
            workspace=workspace,
            slipnet=slipnet,
            proposed_structure=proposed_bond,
        )
        self.proposed_bond = proposed_bond

    def run(self, temperature: float):
        raise NotImplementedError
