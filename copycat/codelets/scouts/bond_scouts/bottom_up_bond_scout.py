import random
from typing import Optional

from copycat.codelets.scouts.bond_scout import BondScout
from copycat.codelets.strength_testers import BondStrengthTester
from copycat.slipnet import Slipnode
from copycat.workspace_structures.bond import Bond


class BottomUpBondScout(BondScout):
    """Chooses an object and a neighbour probabilistically by intra-string-salience.
    Chooses a bond facet (letter category or length) probabilistically by relevance in string.
    If there can be a bond between the two descriptors of this facet,
    posts a bond strength tester with urgency a function of the degree of association
    of bonds of the bond category."""

    def run(self, temperature: float):
        from_obj = self.workspace.choose_object(
            temperature, lambda x: x.intra_string_salience
        )
        if from_obj is None:
            return
        to_obj = from_obj.choose_neighbor(temperature)
        if to_obj is None:
            return
        bond_facet = self._choose_bond_facet(from_obj, to_obj)
        if bond_facet is None:
            return
        from_obj_descriptor = from_obj.get_descriptor(bond_facet)
        to_obj_descriptor = to_obj.get_descriptor(bond_facet)
        if from_obj_descriptor is None or to_obj_descriptor is None:
            return
        bond_category = self._get_bond_category(from_obj_descriptor, to_obj_descriptor)
        if bond_category is None:
            return
        self.propose_bond(
            from_obj,
            to_obj,
            bond_category,
            bond_facet,
            from_obj_descriptor,
            to_obj_descriptor,
        )

    def _choose_bond_facet(self, from_obj, to_obj) -> Optional[Slipnode]:
        from_obj_bond_facets = [
            d.facet
            for d in from_obj.descriptions
            if d.facet.category.name == "bond_facet"
        ]
        to_obj_bond_facets = [
            d.facet
            for d in to_obj.descriptions
            if d.facet.category.name == "bond_facet"
        ]
        common_bond_facets = [
            facet for facet in from_obj_bond_facets if facet in to_obj_bond_facets
        ]
        if not common_bond_facets:
            return None
        supports = [
            facet.get_total_description_type_support(from_obj.string)
            for facet in common_bond_facets
        ]
        return random.choices(common_bond_facets, weights=supports, k=1)[0]

    def _get_bond_category(
        self, from_node: Slipnode, to_node: Slipnode
    ) -> Optional[Slipnode]:
        if from_node == to_node:
            return self.slipnet.node_index_lookup["sameness"]
        for link in from_node.outgoing_links:
            if link.to_node == to_node:
                return link.label
        return None

    def propose_bond(
        self,
        from_obj,
        to_obj,
        bond_category,
        bond_facet,
        from_obj_descriptor,
        to_obj_descriptor,
    ):
        self.slipnet.activate_node_from_workspace(from_obj_descriptor.name)
        self.slipnet.activate_node_from_workspace(to_obj_descriptor.name)
        self.slipnet.activate_node_from_workspace(bond_facet.name)
        proposed_bond = Bond(
            from_obj,
            to_obj,
            bond_category,
            bond_facet,
            from_obj_descriptor,
            to_obj_descriptor,
        )
        proposed_bond.proposal_level = 1
        from_obj.string.add_proposed_bond(proposed_bond)
        urgency = bond_category.bond_degree_of_association
        urgency_bin = self.coderack.get_urgency_level_from_activation(urgency)
        self.coderack.post(
            BondStrengthTester(
                urgency_bin=urgency_bin,
                coderack=self.coderack,
                slipnet=self.slipnet,
                workspace=self.workspace,
                proposed_bond=proposed_bond,
            )
        )
