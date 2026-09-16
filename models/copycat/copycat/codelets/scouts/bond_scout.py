from typing import Optional

from copycat.codelets.scout import Scout
from copycat.codelets.strength_testers import BondStrengthTester
from copycat.slipnode import Slipnode
from copycat.tools import select_item_from_list
from copycat.workspace_objects_and_structures import Bond


class BondScout(Scout):
    """A bond scout codelet looks for evidence of a bond.
    If possible, it makes a proposed bond and posts a bond strength tester.
    """

    def propose_bond(self, temperature: float) -> None:
        self.slipnet.activate_node_from_workspace(self.source_descriptor.name)
        self.slipnet.activate_node_from_workspace(self.target_descriptor.name)
        self.slipnet.activate_node_from_workspace(self.bond_facet.name)
        self.direction_category = (
            None
            if self.bond_category.name == "sameness"
            else self.slipnet["right"]
            if self.source.left_position < self.target.left_position
            else self.slipnet["left"]
        )
        self.proposed_bond = Bond(
            source=self.source,
            target=self.target,
            bond_category=self.bond_category,
            direction_category=self.direction_category,
            bond_facet=self.bond_facet,
            source_descriptor=self.source_descriptor,
            target_descriptor=self.target_descriptor,
        )
        self.source.string.add_proposed_bond(self.proposed_bond)
        urgency = self.bond_category.bond_degree_of_association
        urgency_bin = self.coderack.get_urgency_level_from_activation(urgency)
        self.coderack.post(
            BondStrengthTester(
                urgency_bin=urgency_bin,
                coderack=self.coderack,
                slipnet=self.slipnet,
                workspace=self.workspace,
                proposed_bond=self.proposed_bond,
            ),
            temperature=temperature,
        )

    def _choose_bond_facet(self, source, target) -> Optional[Slipnode]:
        source_bond_facets = [
            d.facet
            for d in source.descriptions
            if d.facet.category == self.slipnet["bond_facet"]
        ]
        target_bond_facets = [
            d.facet
            for d in target.descriptions
            if d.facet.category == self.slipnet["bond_facet"]
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
        return select_item_from_list(common_bond_facets, supports)

    def _get_bond_category(
        self, source: Slipnode, target: Slipnode
    ) -> Optional[Slipnode]:
        if source == target:
            return self.slipnet["sameness"]
        for link in source.outgoing_links:
            if link.target == target:
                return link.label
        return None
