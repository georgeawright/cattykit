import random
from typing import Optional

from copycat.codelets.scouts.bond_scout import BondScout
from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.slipnet import Slipnode
from copycat.workspace_objects_and_structures import Bond


class BottomUpBondScout(BondScout):
    """Chooses an object and a neighbour probabilistically by intra-string-salience.
    Chooses a bond facet (letter category or length) probabilistically by relevance in string.
    If there can be a bond between the two descriptors of this facet,
    posts a bond strength tester with urgency a function of the degree of association
    of bonds of the bond category."""

    def run(self, temperature: float) -> CodeletResult:
        self.source = self.workspace.choose_object(
            temperature, lambda x: x.intra_string_salience
        )
        if self.source is None:
            return Fizzle(FizzleReason.NO_OBJECTS)
        self.target = self.source.choose_neighbour()
        if self.target is None:
            return Fizzle(FizzleReason.NO_NEIGHBOUR)
        self.bond_facet = self._choose_bond_facet(self.source, self.target)
        if self.bond_facet is None:
            return Fizzle(FizzleReason.NO_COMMON_BOND_FACET)
        self.source_descriptor = self.source.get_descriptor(self.bond_facet)
        self.target_descriptor = self.target.get_descriptor(self.bond_facet)
        if self.source_descriptor is None or self.target_descriptor is None:
            return Fizzle(FizzleReason.NO_DESCRIPTORS_FOR_BOND_FACET)
        self.bond_category = self._get_bond_category(
            self.source_descriptor, self.target_descriptor
        )
        if self.bond_category is None:
            return Fizzle(FizzleReason.NO_BOND_CATEGORY)
        self.propose_bond(temperature)
        return Finish()
