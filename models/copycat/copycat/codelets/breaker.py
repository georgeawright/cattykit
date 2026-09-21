import random

from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.codelet import Codelet
from copycat.workspace_objects_and_structures import Bond, Correspondence, Group, Rule
from copycat.tools import temperature_adjust_probability


class Breaker(Codelet):
    """Probabilistically fizzles or breaks weaker structures."""

    def run(self, temperature: float) -> CodeletResult:
        if temperature < random.random():
            return Fizzle(FizzleReason.TEMPERATURE_TOO_LOW)
        try:
            self.structure = random.choice(self.workspace.structures)
        except IndexError:
            return Fizzle(FizzleReason.NO_STRUCTURES)
        structures_to_break = (
            [self.structure, self.structure.group]
            if isinstance(self.structure, Bond) and self.structure.group is not None
            else [self.structure]
        )
        self.structures_to_break = structures_to_break
        for structure in self.structures_to_break:
            break_probability = temperature_adjust_probability(
                structure.total_weakness, temperature
            )
            if break_probability < random.random():
                return Fizzle(FizzleReason.STRUCTURE_TOO_STRONG)
        for structure in self.structures_to_break:
            if isinstance(structure, Bond):
                self.workspace.break_bond(structure)
            if isinstance(structure, Correspondence):
                self.workspace.break_correspondence(structure)
            if isinstance(structure, Group):
                self.workspace.break_group(structure)
            if isinstance(structure, Rule):
                self.workspace.rule = None
        return Finish()
