from copycat.codelets.scouts.bond_scout import BondScout
from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.slipnode import Slipnode
from copycat.tools import select_item_from_list


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
        initial_string_score = (
            initial_string_relevance + initial_string_unhappiness
        ) * 0.5
        target_string_score = (
            target_string_relevance + target_string_unhappiness
        ) * 0.5
        self.string = select_item_from_list(
            [self.workspace.initial_string, self.workspace.target_string],
            [initial_string_score, target_string_score],
        )
        self.object_1 = self.string.choose_object(
            temperature, lambda x: x.intra_string_salience
        )
        if self.object_1 is None:
            return Fizzle(FizzleReason.NO_OBJECTS)
        self.object_2 = self.object_1.choose_neighbour()
        if self.object_2 is None:
            return Fizzle(FizzleReason.NO_NEIGHBOUR)
        self.bond_facet = self._choose_bond_facet(self.object_1, self.object_2)
        if self.bond_facet is None:
            return Fizzle(FizzleReason.NO_COMMON_BOND_FACET)
        self.object_1_descriptor = self.object_1.get_descriptor(self.bond_facet)
        self.object_2_descriptor = self.object_2.get_descriptor(self.bond_facet)
        if self.object_1_descriptor is None or self.object_2_descriptor is None:
            return Fizzle(FizzleReason.NO_DESCRIPTORS_FOR_BOND_FACET)
        if (
            self._get_bond_category(self.object_1_descriptor, self.object_2_descriptor)
            == self.bond_category
        ):
            self.source = self.object_1
            self.target = self.object_2
            self.source_descriptor = self.object_1_descriptor
            self.target_descriptor = self.object_2_descriptor
        elif (
            self._get_bond_category(self.object_2_descriptor, self.object_1_descriptor)
            == self.bond_category
        ):
            self.source = self.object_2
            self.target = self.object_1
            self.source_descriptor = self.object_2_descriptor
            self.target_descriptor = self.object_1_descriptor
        else:
            return Fizzle(FizzleReason.BOND_CATEGORY_DOES_NOT_MATCH)
        self.propose_bond(temperature)
        return Finish()
