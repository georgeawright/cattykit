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
        source,
        target,
        bond_category,
        bond_facet,
        source_descriptor,
        target_descriptor,
    ):
        self.slipnet.activate_node_from_workspace(source_descriptor.name)
        self.slipnet.activate_node_from_workspace(target_descriptor.name)
        self.slipnet.activate_node_from_workspace(bond_facet.name)
        direction_category = (
            None
            if bond_category.name == "sameness"
            else self.slipnet["right"]
            if source.left_position < target.left_position
            else self.slipnet["left"]
        )
        proposed_bond = Bond(
            source=source,
            target=target,
            bond_category=bond_category,
            direction_category=direction_category,
            bond_facet=bond_facet,
            source_descriptor=source_descriptor,
            target_descriptor=target_descriptor,
        )
        proposed_bond.proposal_level = 1
        source.string.add_proposed_bond(proposed_bond)
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

    def _choose_bond_facet(self, source, target) -> Optional[Slipnode]:
        source_bond_facets = [
            d.facet
            for d in source.descriptions
            if d.facet.category.name == "bond_facet"
        ]
        target_bond_facets = [
            d.facet
            for d in target.descriptions
            if d.facet.category.name == "bond_facet"
        ]
        common_bond_facets = [
            facet for facet in source_bond_facets if facet in target_bond_facets
        ]
        if not common_bond_facets:
            return None
        supports = [
            facet.get_total_description_type_support(source.string)
            for facet in common_bond_facets
        ]
        return random.choices(common_bond_facets, weights=supports, k=1)[0]

    def _get_bond_category(
        self, source: Slipnode, target: Slipnode
    ) -> Optional[Slipnode]:
        if source == target:
            return self.slipnet.node_index_lookup["sameness"]
        for link in source.outgoing_links:
            if link.target == target:
                return link.label
        return None
