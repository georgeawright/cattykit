import random
from typing import Optional

from copycat.codelets.scout import Scout
from copycat.codelets.strength_testers import BondStrengthTester
from copycat.slipnode import Slipnode
from copycat.workspace_structures.bond import Bond


class BondScout(Scout):
    """A bond scout codelet looks for evidence of a bond.
    If possible, it makes a proposed bond and posts a bond strength tester.
    """

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
        direction_category = (
            self.slipnet["right"]
            if from_obj.left_position < to_obj.left_position
            else self.slipnet["left"]
        )
        proposed_bond = Bond(
            from_object=from_obj,
            to_object=to_obj,
            bond_category=bond_category,
            direction_category=direction_category,
            bond_facet=bond_facet,
            from_object_descriptor=from_obj_descriptor,
            to_object_descriptor=to_obj_descriptor,
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
