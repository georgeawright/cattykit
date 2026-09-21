from copycat.codelets.scouts.bond_scout import BondScout
from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.slipnode import Slipnode
from copycat.tools import select_item_from_list


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
        initial_string_score = (
            initial_string_relevance + initial_string_unhappiness
        ) / 2
        target_string_score = (target_string_relevance + target_string_unhappiness) / 2
        self.string = select_item_from_list(
            [self.workspace.initial_string, self.workspace.target_string],
            [initial_string_score, target_string_score],
        )
        self.source = self.string.choose_object(
            temperature, lambda x: x.intra_string_salience
        )
        if self.source is None:
            return Fizzle(FizzleReason.NO_OBJECTS)
        self.target = (
            self.source.choose_left_neighbour()
            if self.direction_category.name == "left"
            else self.source.choose_right_neighbour()
        )
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
        if self.bond_category is None or not self.bond_category.is_directed:
            return Fizzle(FizzleReason.NO_DIRECTED_BOND_CATEGORY)
        self.propose_bond(temperature)
        return Finish()
