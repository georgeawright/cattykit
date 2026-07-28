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
        from_obj = self.workspace.choose_object(
            temperature, lambda x: x.intra_string_salience
        )
        if from_obj is None:
            return Fizzle(FizzleReason.NO_OBJECTS)
        to_obj = from_obj.choose_neighbor(temperature)
        if to_obj is None:
            return Fizzle(FizzleReason.NO_NEIGHBOR)
        bond_facet = self._choose_bond_facet(from_obj, to_obj)
        if bond_facet is None:
            return Fizzle(FizzleReason.NO_COMMON_BOND_FACET)
        from_obj_descriptor = from_obj.get_descriptor(bond_facet)
        to_obj_descriptor = to_obj.get_descriptor(bond_facet)
        if from_obj_descriptor is None or to_obj_descriptor is None:
            return Fizzle(FizzleReason.NO_DESCRIPTORS_FOR_BOND_FACET)
        bond_category = self._get_bond_category(from_obj_descriptor, to_obj_descriptor)
        if bond_category is None:
            return Fizzle(FizzleReason.NO_BOND_CATEGORY)
        self.propose_bond(
            from_obj,
            to_obj,
            bond_category,
            bond_facet,
            from_obj_descriptor,
            to_obj_descriptor,
        )
        return Finish()
