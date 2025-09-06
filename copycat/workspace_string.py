class WorkspaceString:
    def __init__(self):
        self.letters = []
        self.object_positions = {}

        self.proposed_bonds_by_role = {}
        self.bonds_by_role = {}
        self.bonds_by_position = {}

        self.proposed_groups = {}
        self.groups = {}

    @property
    def proposed_bonds(self):
        unique_bonds = []
        added = set()
        for from_index, bonds in self.proposed_bonds_by_role.items():
            for to_index, bond in bonds:
                if bond in added:
                    continue
                unique_bonds.append(bond)
        return unique_bonds

    @property
    def bonds(self):
        unique_bonds = []
        added = set()
        for from_index, bonds in self.bonds_by_role.items():
            for to_index, bond in bonds:
                if bond in added:
                    continue
                unique_bonds.append(bond)
        return unique_bonds

    @property
    def proposed_groups(self):
        return [
            group
            for left_index, groups in self.proposed_groups.items()
            for right_index, group in groups
        ]

    @property
    def groups(self):
        return [
            group
            for left_index, groups in self.groups.items()
            for right_index, group in groups
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
        self.proposed_bonds_by_role[bond.from_node.id][bond.to_node.id].append(bond)

    def delete_proposed_bond(self, bond):
        self.proposed_bonds_by_role[bond.from_node.id][bond.to_node.id].remove(bond)

    def add_bond(self, bond):
        self.bonds_by_role[bond.from_node.id][bond.to_node.id] = bond
        self.bonds_by_position[bond.left_node.id][bond.right_node.id] = bond
        if bond.is_sameness_bond:
            self.bonds_by_role[bond.to_node.id][bond.from_node.id] = bond
            self.bonds_by_position[bond.left_node.id][bond.right_node.id] = bond

    def delete_bond(self, bond):
        self.bonds_by_role[bond.from_node.id][bond.to_node.id] = None
        self.bonds_by_position[bond.left_node.id][bond.right_node.id] = None
        if bond.is_sameness_bond:
            self.bonds_by_role[bond.to_node.id][bond.from_node.id] = None
            self.bonds_by_position[bond.left_node.id][bond.right_node.id] = None

    def add_proposed_group(self, group):
        self.proposed_group[group.left_node.id][group.right_node.id].append(group)

    def delete_proposed_group(self, group):
        self.proposed_group[group.left_node.id][group.right_node.id].remove(group)

    def add_group(self, group):
        self.groups[group.left_node.id] = group
        self.object_positions[group.left_position].append(group)
        self.object_positions[group.right_position].append(group)

    def delete_group(self, group):
        self.groups[group.left_node.id] = None
        self.object_positions[group.left_position].remove(group)
        self.object_positions[group.right_position].remove(group)

    def choose_object(self, temperature, method):
        """Return an object probabilistically according to temperature and method."""
        pass

    def choose_leftmost_object(self):
        """Returns one of the leftmost objects probabilistically."""
        pass
