from typing import List, Optional, Tuple

from copycat.codelets.scout import Scout
from copycat.codelets.strength_testers import GroupStrengthTester
from copycat.workspace_objects.group import Group
from copycat.tools import select_item_from_list


class GroupScout(Scout):
    """A group scout codelet looks for evidence of a group.
    If possible, it makes a proposed group and posts a group strength tester.
    """

    def propose_group(
        self,
        objects: List["WorkspaceObject"],
        bonds: List["Bond"],
        group_category: "Slipnode",
        direction: "Slipnode",
        bond_category: "Slipnode",
        temperature: float,
    ):
        string = objects[0].string
        left_object = min(objects, key=lambda o: o.left_position)
        right_object = max(objects, key=lambda o: o.right_position)
        proposed_group = Group(
            string=string,
            left_position=left_object.left_position,
            right_position=right_object.right_position,
            objects=objects,
            bonds=bonds,
            group_category=group_category,
            direction_category=direction,
            bond_category=bond_category,
        )
        string.add_proposed_group(proposed_group)
        urgency = bond_category.bond_degree_of_association
        urgency_bin = self.coderack.get_urgency_level_from_activation(urgency)
        self.coderack.post(
            GroupStrengthTester(
                urgency_bin=urgency_bin,
                coderack=self.coderack,
                slipnet=self.slipnet,
                workspace=self.workspace,
                proposed_group=proposed_group,
            ),
            temperature=temperature,
        )

    def _choose_workspace_string(
        self, initial_string_relevance, target_string_relevance
    ):
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
        chosen_string = select_item_from_list(
            [self.workspace.initial_string, self.workspace.target_string],
            [initial_string_score, target_string_score],
        )
        return chosen_string

    def _choose_direction(self, chosen_object):
        if chosen_object.is_leftmost_in_string():
            return self.slipnet["right"]
        elif chosen_object.is_rightmost_in_string():
            return self.slipnet["left"]
        left = self.slipnet["left"]
        right = self.slipnet["right"]
        return select_item_from_list([left, right], [left.activation, right.activation])

    def _choose_number_of_bonds(self, workspace_string):
        number_of_bonds = select_item_from_list(
            workspace_string.distribution_of_bond_counts,
            workspace_string.distribution_of_bond_counts,
        )
        return number_of_bonds

    def _get_first_bond(self, direction, chosen_object) -> Optional["Bond"]:
        if direction.name == "left":
            return chosen_object.left_bond
        elif direction.name == "right":
            return chosen_object.right_bond

    def _get_bonds_and_objects(
        self, direction: "Slipnode", first_bond: "Bond", number_of_bonds: int
    ) -> Tuple[List["Bond"], List["WorkspaceObject"]]:
        objects = [first_bond.left_object, first_bond.right_object]
        bonds = [first_bond]
        opposite_bond_category = first_bond.bond_category.get_related_node("opposite")
        opposite_direction_category = (
            first_bond.direction_category.get_related_node("opposite")
            if first_bond.direction_category is not None
            else None
        )
        next_bond = first_bond
        for i in range(2, number_of_bonds + 1):
            next_bond = next_bond.choose_neighbour(direction)
            if next_bond is None:
                break
            next_object = next_bond.get_object(direction)
            if (
                next_bond.bond_category == first_bond.bond_category
                and next_bond.direction_category == first_bond.direction_category
                and next_bond.bond_facet == first_bond.bond_facet
            ):
                bonds.append(next_bond)
                objects.append(next_object)
            elif (
                next_bond.bond_category == opposite_bond_category
                and next_bond.direction_category == opposite_direction_category
                and next_bond.bond_facet == first_bond.bond_facet
            ):
                bonds.append(next_bond.get_flipped_version())
                objects.append(next_object)
            else:
                break
        return bonds, objects
