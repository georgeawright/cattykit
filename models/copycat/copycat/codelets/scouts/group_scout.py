import random
from typing import List, Optional, Tuple

from copycat.codelets.scout import Scout
from copycat.codelets.strength_testers import GroupStrengthTester
from copycat.workspace_objects import Group
from copycat.workspace_structures import Description
from copycat.tools import select_item_from_list, temperature_adjust_probability


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
        self._add_descriptions_to_group(proposed_group, temperature)
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
        description = Description(group, facet, descriptor)
        existing_descriptions = group.descriptions + group.bond_descriptions
        if any(
            getattr(existing, "facet", None) == facet
            and getattr(existing, "descriptor", None) == descriptor
            for existing in existing_descriptions
        ):
            return
        group.add_description(description)

    def _get_string_position(self, group: Group):
        if group.spans_whole_string():
            return self.slipnet["whole"]
        if group.is_leftmost_in_string():
            return self.slipnet["leftmost"]
        if self._is_middle_in_string(group):
            return self.slipnet["middle"]
        if group.is_rightmost_in_string():
            return self.slipnet["rightmost"]
        return None

    @staticmethod
    def _is_middle_in_string(group: Group) -> bool:
        return any(
            neighbour.is_leftmost_in_string() for neighbour in group.left_neighbours
        ) and any(
            neighbour.is_rightmost_in_string() for neighbour in group.right_neighbours
        )
