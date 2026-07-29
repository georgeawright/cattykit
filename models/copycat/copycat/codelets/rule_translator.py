from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.codelet import Codelet
from copycat.workspace_structures import Rule


class RuleTranslator(Codelet):
    """Translates the rule according to the workspace slippages."""

    def run(self, temperature: float) -> CodeletResult:
        if self.workspace.rule is None:
            return Fizzle(FizzleReason.NO_RULE_IN_WORKSPACE)
        if self.workspace.rule.no_change:
            self.workspace.translated_rule = Rule()
            return Finish()
        answer_temperature_threshold = self._get_answer_temperature_threshold()
        if self.workspace.temperature > answer_temperature_threshold:
            return Fizzle(FizzleReason.TEMPERATURE_TOO_HIGH)
        try:
            changed_object = self.workspace.initial_string.changed_objects[0]
        except IndexError:
            return Fizzle(FizzleReason.NO_CHANGED_OBJECT)
        if changed_object.correspondence is None:
            slippages = self.workspace.slippages
        else:
            slippages = [
                slippage
                for slippage in self.workspace.slippages
                for mapping in changed_object.correspondence.concept_mappings
                if not mapping.contradicts(slippage)
            ]
        self.workspace.translated_rule = self.workspace.rule.apply_slippages(slippages)
        return Finish()

    def _get_answer_temperature_threshold(self) -> float:
        # TODO
        pass
