from collections import defaultdict
import random

from .formulas import temperature_adjust


class WorkspaceString:
    def __init__(self):
        self.letters = []
        self.object_positions = defaultdict(list)

        self.proposed_bonds_by_role = defaultdict(lambda: defaultdict(list))
        self.bonds_by_role = defaultdict(lambda: defaultdict(list))
        self.bonds_by_position = defaultdict(lambda: defaultdict(list))

        self._proposed_groups = defaultdict(lambda: defaultdict(list))
        self._groups = {}

    @property
    def proposed_bonds(self):
        print(self.proposed_bonds_by_role)
        unique_bonds = []
        added = set()
        for from_index, bonds in self.proposed_bonds_by_role.items():
            for to_index, bond_list in bonds.items():
                for bond in bond_list:
                    if bond in added:
                        continue
                    unique_bonds.append(bond)
                    added.add(bond)
        return unique_bonds

    @property
    def bonds(self):
        unique_bonds = []
        added = set()
        for from_index, bonds in self.bonds_by_role.items():
            for to_index, bond in bonds.items():
                if bond is None:
                    continue
                if bond in added:
                    continue
                unique_bonds.append(bond)
                added.add(bond)
        return unique_bonds

    @property
    def proposed_groups(self):
        return [
            group
            for left_index, groups in self._proposed_groups.items()
            for right_index, group_list in groups.items()
            for group in group_list
        ]

    @property
    def groups(self):
        return [
            group for left_index, group in self._groups.items() if group is not None
        ]

    @property
    def objects(self):
        return self.letters + self.groups

    @property
    def non_string_spanning_objects(self):
        pass

    def add_letter(self, letter):
        self.letters.append(letter)

    def add_proposed_bond(self, bond):
        """Add to a maintained list of proposed bonds between two nodes."""
        self.proposed_bonds_by_role[bond.from_node.id][bond.to_node.id].append(bond)

    def delete_proposed_bond(self, bond):
        """Delete from a maintained list of proposed bonds between two nodes."""
        self.proposed_bonds_by_role[bond.from_node.id][bond.to_node.id].remove(bond)

    def add_bond(self, bond):
        """Add the only bond between two nodes."""
        self.bonds_by_role[bond.from_node.id][bond.to_node.id] = bond
        self.bonds_by_position[bond.left_node.id][bond.right_node.id] = bond
        if bond.is_sameness_bond:
            self.bonds_by_role[bond.to_node.id][bond.from_node.id] = bond
            self.bonds_by_position[bond.left_node.id][bond.right_node.id] = bond

    def delete_bond(self, bond):
        """Delete the only bond between two nodes."""
        self.bonds_by_role[bond.from_node.id][bond.to_node.id] = None
        self.bonds_by_position[bond.left_node.id][bond.right_node.id] = None
        if bond.is_sameness_bond:
            self.bonds_by_role[bond.to_node.id][bond.from_node.id] = None
            self.bonds_by_position[bond.left_node.id][bond.right_node.id] = None

    def add_proposed_group(self, group):
        """Add to a list of proposed groups spanning from one node to another."""
        self._proposed_groups[group.left_node.id][group.right_node.id].append(group)

    def delete_proposed_group(self, group):
        """Delete from a list of proposed bonds spanning from one node to another."""
        self._proposed_groups[group.left_node.id][group.right_node.id].remove(group)

    def add_group(self, group):
        """Add the only group spanning from one node to another."""
        self._groups[group.left_node.id] = group
        self.object_positions[group.left_position].append(group)
        self.object_positions[group.right_position].append(group)

    def delete_group(self, group):
        """Delete the only group spanning from one node to another."""
        self._groups[group.left_node.id] = None
        self.object_positions[group.left_position].remove(group)
        self.object_positions[group.right_position].remove(group)

    def choose_object(self, temperature, method):
        """Return an object probabilistically according to temperature and method."""
        weights = [temperature_adjust(method(obj), temperature) for obj in self.objects]
        return random.choices(self.objects, weights=weights, k=1)

    def choose_leftmost_object(self):
        """Returns one of the leftmost objects probabilistically."""
        pass
