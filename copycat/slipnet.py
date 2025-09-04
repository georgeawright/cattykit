import torch


class Slipnet:
    def __init__(
        self,
        nodes: list,  # a list of the nodes in the slipnet
        adjacency_table: torch.Tensor,  # 3D adjacency table (from, to, link-type)
        node_index_lookup: dict,  # mapping of node_id to index in adjacency table
        node_activations: torch.Tensor,  # the activation value of each node
        clamped_nodes: torch.Tensor,  # nodes which should be clamped at full activation
        node_depth_factors: torch.Tensor,  # the reciprocal of nodes' conceptual depth
        # nodes with activation above threshold probabilistically jump to full activation
        full_activation_threshold: float,
        # probability(jumping to full activation) = activation ** exponent
        full_activation_probability_exponent: int,
    ):
        self.nodes = nodes
        self.adjacency_table = adjacency_table
        self.number_of_nodes = len(nodes)
        self.node_index_lookup = node_index_lookup
        self.node_activations = node_activations
        self.clamped_nodes = clamped_nodes
        self.node_depth_factors = node_depth_factors
        self.full_activation_threshold = full_activation_threshold
        self.full_activation_probability_exponent = full_activation_probability_exponent

    @classmethod
    def create(
        cls,
        nodes: list,
        links: list,
        full_activation_threshold: float = 0.55,
        full_activation_probability_exponent: int = 3,
        device: str = "cpu",
    ):
        number_of_nodes = len(nodes)
        node_index_lookup = {node.name: index for index, node in enumerate(nodes)}
        node_activations = torch.zeros(number_of_nodes, device=device)
        clamped_nodes = torch.tensor([False for node in nodes], device=device)
        node_depth_factors = torch.tensor(
            [node.depth_factor for node in nodes], device=device
        )
        adjacency_table = torch.zeros(
            number_of_nodes, number_of_nodes, number_of_nodes, device=device
        )
        for link in links:
            i = node_index_lookup[link.from_node.name]
            j = node_index_lookup[link.to_node.name]
            k = node_index_lookup[link.type_node.name]
            adjacency_table[i, j, k] = link.intrinsic_degree_of_association
        return cls(
            nodes,
            adjacency_table,
            node_index_lookup,
            node_activations,
            clamped_nodes,
            node_depth_factors,
            full_activation_threshold,
            full_activation_probability_exponent,
        )

    def get_node_activation(self, node_id):
        return self.node_activations[self.node_index_lookup[node_id]]

    def update_activations(self):
        """Recomputes activations according to:
        - activation spread in the slipnet
        - activation boosts from the workspace
        - activation decay according to nodes' conceptual depth
        - probabilistic jumping of node activations
        - clamped nodes remain active."""
        # here clamp() limits activation to no more than max=1
        self.node_activations = (
            self.node_activations
            + self._spread_activations()
            # + self._boost_activations()
            + self._decay_activations()
        ).clamp(max=1)
        # here "clamp" is copycat terminology meaning to keep activation held at 1
        self.node_activations[self.clamped_nodes] = 1.0
        self._probabilistically_activate_nodes()

    def _spread_activations(self):
        """calculates how much activation nodes should receive
        from active related nodes in the slipnet."""
        active_source_nodes = (
            self.node_activations.view(self.number_of_nodes, 1, 1) >= 1
        ).int()
        return (active_source_nodes * self.adjacency_table).sum(dim=0).sum(dim=1)

    def _boost_activations(self):
        """calculates how much activation nodes should receive
        from workspace structures."""
        raise NotImplementedError

    def _decay_activations(self):
        """calculates how much nodes' activation should decay
        according to their conceptual depth."""
        return -self.node_activations * self.node_depth_factors

    def _probabilistically_activate_nodes(self):
        """Probabilistically fully boost nodes with activation above threshold."""
        nodes_above_threshold = self.node_activations >= self.full_activation_threshold
        full_activation_probabilities = (
            self.node_activations**self.full_activation_probability_exponent
        )
        random_values = torch.rand_like(self.node_activations)
        nodes_to_fully_activate = nodes_above_threshold & (
            random_values < full_activation_probabilities
        )
        self.node_activations[nodes_to_fully_activate] = 1.0
