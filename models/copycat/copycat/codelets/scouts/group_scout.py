import random
from typing import List, Optional, Tuple

from copycat.codelets.scout import Scout
from copycat.codelets.strength_testers import GroupStrengthTester
from copycat.workspace_objects_and_structures import Description, Group
from copycat.tools import select_item_from_list, temperature_adjust_probability


class GroupScout(Scout):
    """A group scout codelet looks for evidence of a group.
    If possible, it makes a proposed group and posts a group strength tester.
    """

    def propose_group(self, temperature: float) -> None:
        self.string = self.objects[0].string
        self.left_object = min(self.objects, key=lambda o: o.left_position)
        self.right_object = max(self.objects, key=lambda o: o.right_position)
        self.proposed_group = Group(
            string=self.string,
            left_position=self.left_object.left_position,
            right_position=self.right_object.right_position,
            objects=self.objects,
            bonds=self.bonds,
            group_category=self.group_category,
            direction_category=self.direction_category,
            bond_category=self.bond_category,
        )
        self._add_descriptions_to_group(self.proposed_group, temperature)
        self.string.add_proposed_group(self.proposed_group)
        self.slipnet.activate_node_from_workspace(self.bond_category.name)
        if self.direction_category is not None:
            self.slipnet.activate_node_from_workspace(self.direction_category.name)
        urgency = self.bond_category.bond_degree_of_association
        urgency_bin = self.coderack.get_urgency_level_from_activation(urgency)
        self.coderack.post(
            GroupStrengthTester(
                urgency_bin=urgency_bin,
                coderack=self.coderack,
                slipnet=self.slipnet,
                workspace=self.workspace,
                proposed_group=self.proposed_group,
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
        self.chosen_string = select_item_from_list(
            [self.workspace.initial_string, self.workspace.target_string],
            [initial_string_score, target_string_score],
        )
        return self.chosen_string

    def _choose_direction(self, chosen_object):
        if chosen_object.is_leftmost_in_string:
            return self.slipnet["right"]
        elif chosen_object.is_rightmost_in_string:
            return self.slipnet["left"]
        left = self.slipnet["left"]
        right = self.slipnet["right"]
        return select_item_from_list([left, right], [left.activation, right.activation])

    def _choose_number_of_bonds(self, workspace_string):
        self.number_of_bonds = select_item_from_list(
            workspace_string.distribution_of_bond_counts,
            workspace_string.distribution_of_bond_counts,
        )
        return self.number_of_bonds

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
        self.next_bond = first_bond
        for i in range(2, number_of_bonds + 1):
            self.next_bond = self.next_bond.choose_neighbour(direction)
            if self.next_bond is None:
                break
            self.next_object = self.next_bond.get_object(direction)
            if (
                self.next_bond.bond_category == first_bond.bond_category
                and self.next_bond.direction_category == first_bond.direction_category
                and self.next_bond.bond_facet == first_bond.bond_facet
            ):
                bonds.append(self.next_bond)
                objects.append(self.next_object)
            elif (
                self.next_bond.bond_category == opposite_bond_category
                and self.next_bond.direction_category == opposite_direction_category
                and self.next_bond.bond_facet == first_bond.bond_facet
            ):
                bonds.append(self.next_bond.get_flipped_version())
                objects.append(self.next_object)
            else:
                break
        return bonds, objects

    def _add_descriptions_to_group(self, group: Group, temperature: float):
        self._add_description(
            group, self.slipnet["object_category"], self.slipnet["group"]
        )
        string_position = self._get_string_position(group)
        if string_position is not None:
            self._add_description(
                group, self.slipnet["string_position_category"], string_position
            )

        if group.group_category == self.slipnet["sameness_group"] and (
            not group.bonds
            or group.bonds[0].bond_facet == self.slipnet["letter_category"]
        ):
            self._add_description(
                group,
                self.slipnet["letter_category"],
                group.left_object.get_descriptor(self.slipnet["letter_category"]),
            )

        self._add_description(
            group, self.slipnet["group_category"], group.group_category
        )
        if group.direction_category is not None:
            self._add_description(
                group,
                self.slipnet["direction_category"],
                group.direction_category,
            )

        if group.bonds:
            group.bond_facet = group.bonds[0].bond_facet
            self._add_description(group, self.slipnet["bond_facet"], group.bond_facet)
        self._add_description(group, self.slipnet["bond_category"], group.bond_category)

        group_length = len(group.objects)
        if 1 <= group_length <= len(self.slipnet.numbers):
            base_probability = 0.5 ** (
                group_length**3 * (1 - self.slipnet["length"].activation)
            )
            length_description_probability = temperature_adjust_probability(
                base_probability, temperature
            )
            if random.random() < length_description_probability:
                self._add_description(
                    group,
                    self.slipnet["length"],
                    self.slipnet.numbers[group_length - 1],
                )

    def _add_description(self, group: Group, facet, descriptor):
        if descriptor is None:
            return
        self.description = Description(group, facet, descriptor)
        existing_descriptions = group.descriptions + group.bond_descriptions
        if any(
            getattr(existing, "facet", None) == facet
            and getattr(existing, "descriptor", None) == descriptor
            for existing in existing_descriptions
        ):
            return
        group.add_description(self.description)

    def _get_string_position(self, group: Group):
        if group.spans_whole_string:
            return self.slipnet["whole"]
        if group.is_leftmost_in_string:
            return self.slipnet["leftmost"]
        if group.is_middle_in_string:
            return self.slipnet["middle"]
        if group.is_rightmost_in_string:
            return self.slipnet["rightmost"]
        return None
