from typing import List

import numpy as np

from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.codelet import Codelet
from copycat.tools import select_item_from_list
from copycat.workspace_structures import Rule


class RuleTranslator(Codelet):
    """Translates the rule according to the workspace slippages."""

    TEMPERATURE_THRESHOLDS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    # threshold weights determine probability of setting temperature thresholds
    VERY_LOW_THRESHOLD_WEIGHTS = [5, 150, 5, 2, 1, 1, 1, 1, 1, 1]
    LOW_THRESHOLD_WEIGHTS = [2, 5, 150, 5, 2, 1, 1, 1, 1, 1]
    MEDIUM_THRESHOLD_WEIGHTS = [1, 2, 5, 150, 5, 2, 1, 1, 1, 1]
    HIGH_THRESHOLD_WEIGHTS = [1, 1, 2, 5, 150, 5, 2, 1, 1, 1]
    VERY_HIGH_THRESHOLD_WEIGHTS = [1, 1, 1, 2, 5, 150, 5, 2, 1, 1]

    def run(self, temperature: float) -> CodeletResult:
        if self.workspace.rule is None:
            return Fizzle(FizzleReason.NO_RULE_IN_WORKSPACE)
        if not self.workspace.rule.specifies_change():
            self.workspace.translated_rule = Rule(self.workspace)
            return Finish()
        answer_temperature_threshold = self._get_answer_temperature_threshold()
        if temperature > answer_temperature_threshold:
            return Fizzle(FizzleReason.TEMPERATURE_TOO_HIGH)
        try:
            changed_object = self.workspace.initial_string.get_changed_objects()[0]
        except IndexError:
            return Fizzle(FizzleReason.NO_CHANGED_OBJECT)
        if changed_object.correspondence is None:
            slippages = self.workspace.slippages
        else:
            slippages = [
                slippage
                for slippage in self.workspace.slippages
                if not any(
                    [
                        mapping.contradicts(slippage)
                        for mapping in changed_object.correspondence.concept_mappings
                    ]
                )
            ]
        self.workspace.translated_rule = self.workspace.rule.apply_slippages(slippages)
        return Finish()

    def _get_answer_temperature_threshold(self) -> float:
        """Probability distribution from which to choose a temperature threshold
        for generating an answer. Temperature should be below the threshold.
        Cases:
          - if the workspace is highly structured:
            - high quality structures => low temperatures
              => an answer can be generated
            - low quality structures => high temperatures
              => more time given to find better structures
          - if the workspace lacks structure:
            - by the time the rule translator runs,
              it is unlikely that structures will be found
              => a more lenient high temperature threshold is allowed.
        """
        bond_density = self._get_bond_density()
        if bond_density >= 0.8:
            weights = self.VERY_LOW_THRESHOLD_WEIGHTS
        elif bond_density >= 0.6:
            weights = self.LOW_THRESHOLD_WEIGHTS
        elif bond_density >= 0.4:
            weights = self.MEDIUM_THRESHOLD_WEIGHTS
        elif bond_density >= 0.2:
            weights = self.HIGH_THRESHOLD_WEIGHTS
        else:  # bond_density >= 0.0
            weights = self.VERY_HIGH_THRESHOLD_WEIGHTS
        return select_item_from_list(self.TEMPERATURE_THRESHOLDS, weights)

    def _get_bond_density(self) -> float:
        """A rough measure of how structured the workspace is."""
        initial_length = len(self.workspace.initial_string)
        target_length = len(self.workspace.target_string)
        if initial_length == target_length == 1:
            return 1
        initial_bonds = len(self.workspace.initial_string.bonds)
        target_bonds = len(self.workspace.target_string.bonds)
        possible_bonds = initial_length - 1 + target_length - 1
        return (initial_bonds + target_bonds) / possible_bonds
