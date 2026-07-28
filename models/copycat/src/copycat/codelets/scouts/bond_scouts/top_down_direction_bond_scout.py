import random

from copycat.codelets.scouts.bond_scout import BondScout
from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.slipnode import Slipnode


class TopDownDirectionBondScout(BondScout):
    """Chooses an object and a neighbour probabilistically by intra-string-salience.
    Chooses a bond facet (letter category or length) probabilistically by relevance in string.
    If there can be a bond of the given direction between the two descriptors of this facet,
    poses a bond strength tester with urgency a function of the degree of association
    of bonds of the bond category."""

    def __init__(
        self,
        urgency_bin: int,
        coderack: "Coderack",
        slipnet: "Slipnet",
        workspace: "Workspace",
        direction_category: Slipnode,
    ):
        super().__init__(
            urgency_bin=urgency_bin,
            coderack=coderack,
            workspace=workspace,
            slipnet=slipnet,
        )
        self.direction_category = direction_category

    def run(self, temperature: float) -> CodeletResult:
        initial_string_relevance = (
            self.workspace.initial_string.get_local_direction_category_relevance(
                self.direction_category
            )
        )
        target_string_relevance = (
            self.workspace.target_string.get_local_direction_category_relevance(
                self.direction_category
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
        from_object = string.choose_object(
            temperature, lambda x: x.intra_string_salience
        )
        if from_object is None:
            return Fizzle(FizzleReason.NO_OBJECTS)
        to_object = (
            from_object.choose_left_neighbor()
            if self.direction_category.name == "left"
            else from_object.choose_right_neighbor()
        )
        if to_object is None:
            return Fizzle(FizzleReason.NO_NEIGHBOR)
        bond_facet = self._choose_bond_facet(from_object, to_object)
        if bond_facet is None:
            return Fizzle(FizzleReason.NO_COMMON_BOND_FACET)
        from_object_descriptor = from_object.get_descriptor(bond_facet)
        to_object_descriptor = to_object.get_descriptor(bond_facet)
        if from_object_descriptor is None or to_object_descriptor is None:
            return Fizzle(FizzleReason.NO_DESCRIPTORS_FOR_BOND_FACET)
        bond_category = self._get_bond_category(
            from_object_descriptor, to_object_descriptor
        )
        if bond_category is None or not bond_category.is_directed():
            return Fizzle(FizzleReason.NO_DIRECTED_BOND_CATEGORY)
        self.propose_bond(
            from_object,
            to_object,
            bond_category,
            bond_facet,
            from_object_descriptor,
            to_object_descriptor,
        )
        return Finish()
