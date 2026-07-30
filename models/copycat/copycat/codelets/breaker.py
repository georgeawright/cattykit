import random

from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.codelet import Codelet
from copycat.workspace_objects import Group
from copycat.workspace_structures import Bond, Correspondence, Rule
from copycat.tools import temperature_adjust


class Breaker(Codelet):
    """Probabilistically fizzles or breaks weaker structures."""

    def run(self, temperature: float) -> CodeletResult:
        if temperature < random.random():
            return Fizzle(FizzleReason.TEMPERATURE_TOO_LOW)
        try:
            structure = random.choice(self.workspace.structures)
        except IndexError:
            return Fizzle(FizzleReason.NO_STRUCTURES)
        structures_to_break = (
            [structure, structure.group]
            if isinstance(structure, Bond) and structure.group is not None
            else [structure]
        )
        for structure in structures_to_break:
            break_probability = temperature_adjust(
                structure.total_weakness, temperature
            )
            if break_probability < random.random():
                return Fizzle(FizzleReason.STRUCTURE_TOO_STRONG)
        for structure in structures_to_break:
            if isinstance(structure, Bond):
                self.workspace.break_bond(structure)
            if isinstance(structure, Correspondence):
                self.workspace.break_correspondence(structure)
            if isinstance(structure, Group):
                self.workspace.break_group(structure)
            if isinstance(structure, Rule):
                self.workspace.rule = None
        return Finish()
