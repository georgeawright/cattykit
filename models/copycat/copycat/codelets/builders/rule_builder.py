from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.codelets.builder import Builder
from copycat.tools import structure_beats_structures
from copycat.workspace_objects_and_structures import Rulejjj


class RuleBuilder(Builder):
    """A rule builder tries to build the proposed rule.
    It fights with competitors if necessary.
    """

    def __init__(
        self,
        urgency_bin: int,
        coderack: "Coderack",
        workspace: "Workspace",
        slipnet: "Slipnet",
        proposed_rule: Rule,
    ):
        super().__init__(
            urgency_bin=urgency_bin,
            coderack=coderack,
            workspace=workspace,
            slipnet=slipnet,
            proposed_structure=proposed_rule,
        )
        self.proposed_rule = proposed_rule

    def run(self, temperature: float) -> CodeletResult:
        if self.workspace.rule is not None and self.workspace.rule.equates_to(
            self.proposed_rule
        ):
            self._activate_rule_description_nodes()
            return Fizzle(FizzleReason.RULE_ALREADY_EXISTS)
        if self.workspace.rule:
            fight_result = structure_beats_structures(
                self.proposed_rule, 1, [self.workspace.rule], 1, temperature
            )
            if not fight_result:
                return Fizzle(FizzleReason.INCOMPATIBLE_STRUCTURES_WON)
        self.workspace.rule = self.proposed_rule
        self._activate_rule_description_nodes()
        return Finish()

    def _activate_rule_description_nodes(self):
        if self.proposed_rule.source_descriptor is not None:
            self.slipnet.activate_node_from_workspace(
                self.proposed_rule.source_descriptor.name
            )
        if self.proposed_rule.relation is not None:
            self.slipnet.activate_node_from_workspace(self.proposed_rule.relation.name)
        if self.proposed_rule.target_descriptor is not None:
            self.slipnet.activate_node_from_workspace(
                self.proposed_rule.target_descriptor.name
            )
