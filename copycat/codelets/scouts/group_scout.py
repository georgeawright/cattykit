from typing import List

from copycat.codelets.scout import Scout
from copycat.codelets.strength_testers import GroupStrengthTester
from copycat.workspace_objects.group import Group


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
    ):
        string = objects[0].string
        left_object = min(objects, key=lambda o: o.left_position)
        right_object = max(objects, key=lambda o: o.right_position)
        bond_category = group_category.get_related_node("bond_category")
        proposed_group = Group(
            string=string,
            left_position=left_object.left_position,
            right_position=right_object.right_position,
            objects=objects,
            group_category=group_category,
            direction_category=direction,
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
            )
        )
