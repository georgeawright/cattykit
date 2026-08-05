import random
from typing import Optional

from copycat.codelets.scouts.bond_scout import BondScout
from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.slipnet import Slipnode
from copycat.workspace_structures.bond import Bond


class BottomUpBondScout(BondScout):
    """Chooses an object and a neighbour probabilistically by intra-string-salience.
    Chooses a bond facet (letter category or length) probabilistically by relevance in string.
    If there can be a bond between the two descriptors of this facet,
    posts a bond strength tester with urgency a function of the degree of association
    of bonds of the bond category."""

    def run(self, temperature: float) -> CodeletResult:
        source = self.workspace.choose_object(
            temperature, lambda x: x.intra_string_salience
        )
        if source is None:
            return Fizzle(FizzleReason.NO_OBJECTS)
        target = source.choose_neighbour()
        if target is None:
            return Fizzle(FizzleReason.NO_NEIGHBOUR)
        bond_facet = self._choose_bond_facet(source, target)
        if bond_facet is None:
            return Fizzle(FizzleReason.NO_COMMON_BOND_FACET)
        source_descriptor = source.get_descriptor(bond_facet)
        target_descriptor = target.get_descriptor(bond_facet)
        if source_descriptor is None or target_descriptor is None:
            return Fizzle(FizzleReason.NO_DESCRIPTORS_FOR_BOND_FACET)
        bond_category = self._get_bond_category(source_descriptor, target_descriptor)
        if bond_category is None:
            return Fizzle(FizzleReason.NO_BOND_CATEGORY)
        self.propose_bond(
            source,
            target,
            bond_category,
            bond_facet,
            source_descriptor,
            target_descriptor,
            temperature=temperature,
        )
        return Finish()
