import random

from copycat.codelets.scouts.bond_scout import BondScout
from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.slipnode import Slipnode


class TopDownCategoryBondScout(BondScout):
    """Chooses an object and a neighbour probabilistically by intra-string-salience.
    Chooses a bond facet (letter category or length) probabilistically by relevance in string.
    If there can be a bond of the given category between the two descriptors of this facet,
    poses a bond strength tester with urgency a function of the degree of association
    of bonds of the bond category."""

    def __init__(
        self,
        urgency_bin: int,
        coderack: "Coderack",
        slipnet: "Slipnet",
        workspace: "Workspace",
        bond_category: Slipnode,
    ):
        super().__init__(
            urgency_bin=urgency_bin,
            coderack=coderack,
            workspace=workspace,
            slipnet=slipnet,
        )
        self.bond_category = bond_category

    def run(self, temperature: float) -> CodeletResult:
        initial_string_relevance = (
            self.workspace.initial_string.get_local_bond_category_relevance(
                self.bond_category
            )
        )
        target_string_relevance = (
            self.workspace.target_string.get_local_bond_category_relevance(
                self.bond_category
            )
        )
        initial_string_unhappiness = (
            self.workspace.initial_string.intra_string_unhappiness
        )
        target_string_unhappiness = (
            self.workspace.target_string.intra_string_unhappiness
        )
        initial_string_score = round(
            (initial_string_relevance + initial_string_unhappiness) / 2
        )
        target_string_score = round(
            (target_string_relevance + target_string_unhappiness) / 2
        )
        string = random.choices(
            [self.workspace.initial_string, self.workspace.target_string],
            weights=[initial_string_score, target_string_score],
        )[0]
        object_1 = string.choose_object(temperature, lambda x: x.intra_string_salience)
        if object_1 is None:
            return Fizzle(FizzleReason.NO_OBJECTS)
        object_2 = object_1.choose_neighbor()
        if object_2 is None:
            return Fizzle(FizzleReason.NO_NEIGHBOR)
        bond_facet = self._choose_bond_facet(object_1, object_2)
        if bond_facet is None:
            return Fizzle(FizzleReason.NO_COMMON_BOND_FACET)
        object_1_descriptor = object_1.get_descriptor(bond_facet)
        object_2_descriptor = object_2.get_descriptor(bond_facet)
        if object_1_descriptor is None or object_2_descriptor is None:
            return Fizzle(FizzleReason.NO_DESCRIPTORS_FOR_BOND_FACET)
        if (
            self._get_bond_category(object_1_descriptor, object_2_descriptor)
            == self.bond_category
        ):
            source = object_1
            target = object_2
            source_descriptor = object_1_descriptor
            target_descriptor = object_2_descriptor
        elif (
            self._get_bond_category(object_2_descriptor, object_1_descriptor)
            == self.bond_category
        ):
            source = object_2
            target = object_1
            source_descriptor = object_2_descriptor
            target_descriptor = object_1_descriptor
        else:
            return Fizzle(FizzleReason.BOND_CATEGORY_DOES_NOT_MATCH)
        self.propose_bond(
            source,
            target,
            self.bond_category,
            bond_facet,
            source_descriptor,
            target_descriptor,
        )
        return Finish()
