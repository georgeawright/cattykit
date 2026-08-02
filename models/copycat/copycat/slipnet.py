from typing import Callable, Dict, List, Optional

import numpy as np

from .sliplink import Sliplink
from .slipnode import Slipnode


class Slipnet:
    """A network of concepts and their relationships."""

    def __init__(
        self,
        nodes: List[Slipnode],  # a list of the nodes in the slipnet
        adjacency_table: np.ndarray,  # 2D adjacency table (from-node, to-node)
        node_index_lookup: Dict[str, int],  # maps node_id to index in adjacency table
        node_activations: np.ndarray,  # the activation value of each node
        activation_buffers: np.ndarray,  # buffers for pending updates
        clamped_nodes: np.ndarray,  # nodes which should be clamped at full activation
        node_depth_factors: np.ndarray,  # the reciprocal of nodes' conceptual depth
        # the amount of activation to add to nodes from the workspace
        workspace_activation: float,
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
        self.activation_buffers = activation_buffers
        self.clamped_nodes = clamped_nodes
        self.node_depth_factors = node_depth_factors
        self.workspace_activation = workspace_activation
        self.full_activation_threshold = full_activation_threshold
        self.full_activation_probability_exponent = full_activation_probability_exponent

    @classmethod
    def create(
        cls,
        nodes: List[Slipnode],
        links: List[Sliplink],
        workspace_activation: float = 1.0,
        full_activation_threshold: float = 0.50,
        full_activation_probability_exponent: int = 3,
    ):
        number_of_nodes = len(nodes)
        node_index_lookup = {node.name: index for index, node in enumerate(nodes)}
        node_activations = np.zeros(number_of_nodes, dtype=np.float32)
        activation_buffers = np.zeros(number_of_nodes, dtype=np.float32)
        clamped_nodes = np.array([False for node in nodes])
        node_depth_factors = np.array([node.depth_factor for node in nodes])
        adjacency_table = np.zeros((number_of_nodes, number_of_nodes))
        for link in links:
            i = node_index_lookup[link.source.name]
            j = node_index_lookup[link.target.name]
            adjacency_table[i, j] = link.intrinsic_degree_of_association
        return cls(
            nodes,
            adjacency_table,
            node_index_lookup,
            node_activations,
            activation_buffers,
            clamped_nodes,
            node_depth_factors,
            workspace_activation,
            full_activation_threshold,
            full_activation_probability_exponent,
        )

    @classmethod
    def from_json(
        cls,
        json_data: dict,
        description_testers: Dict[str, Callable],
        workspace_activation: float,
        full_activation_threshold: float,
        full_activation_probability_exponent: int,
        initially_clamped_nodes: List[str],
    ):
        nodes = {
            node_data["name"]: Slipnode(
                name=node_data["name"],
                conceptual_depth=node_data["conceptual_depth"],
                intrinsic_link_length=node_data.get("intrinsic_link_length"),
                shrunk_link_length=node_data.get("shrunk_link_length"),
                description_tester=description_testers[
                    node_data.get("description_tester")
                ]
                if node_data.get("description_tester") is not None
                else None,
            )
            for node_data in json_data["nodes"]
        }
        links = [
            Sliplink(
                source=nodes[link_data["source"]],
                target=nodes[link_data["target"]],
                type_node=nodes[link_data.get("type_node")]
                if link_data.get("type_node") is not None
                else None,
                fixed_length=link_data.get("fixed_length"),
            )
            for link_data in json_data["links"]
        ]
        slipnet = cls.create(
            list(nodes.values()),
            links,
            workspace_activation,
            full_activation_threshold,
            full_activation_probability_exponent,
        )
        for node in initially_clamped_nodes:
            slipnet.clamp_node(node)
        return slipnet

    def __getitem__(self, node_id):
        return self.nodes[self.node_index_lookup[node_id]]

    @property
    def numbers(self) -> List[Slipnode]:
        return [self["one"], self["two"], self["three"], self["four"], self["five"]]

    def get_label_node(self, source: Slipnode, target: Slipnode) -> Optional[Slipnode]:
        """Returns the node representing the label of the link from source to target.
        Returns None if there is no such link or the link is unlabelled.
        Assumes only one link can exist from source to target."""
        if source == target:
            return self["identity"]
        for link in source.outgoing_links:
            if link.target == target:
                return link.label
        return None

    def get_node_activation(self, node_id):
        return self.node_activations[self.node_index_lookup[node_id]]

    def update_activations(self):
        """Recomputes activations according to:
        - activation spread in the slipnet
        - activation boosts from the workspace
        - activation decay according to nodes' conceptual depth
        - probabilistic jumping of node activations
        - clamped nodes remain active."""
        # TODO: activation buffers need to be added
        self.node_activations = (
            self.node_activations
            + self._spread_activations()
            + self._decay_activations()
        ).clip(0, 1)
        # here "clamp" is copycat terminology meaning to keep activation held at 1
        self.node_activations[self.clamped_nodes] = 1.0
        self._probabilistically_activate_nodes()
        for node in self.nodes:
            node.activation = self.node_activations[self.node_index_lookup[node.name]]

    def clamp_node(self, node_id: str):
        """Clamp a node at full activation."""
        index = self.node_index_lookup[node_id]
        self.clamped_nodes[index] = True
        self.node_activations[index] = 1.0

    def unclamp_node(self, node_id: str):
        """Unclamp a node so that its activation can decay."""
        index = self.node_index_lookup[node_id]
        self.clamped_nodes[index] = False

    def activate_node_from_workspace(self, node_id: str):
        index = self.node_index_lookup[node_id]
        self.activation_buffers[index] += self.workspace_activation

    def get_top_down_codelets(self) -> List["Codelet"]:
        top_down_codelets = []
        for node in self.nodes:
            if node.activation > self.full_activation_threshold:
                top_down_codelets.extend(node.get_top_down_codelets())
        return top_down_codelets

    def _spread_activations(self):
        """calculates how much activation nodes should receive
        from active related nodes in the slipnet."""
        active_source_nodes = (self.node_activations == 1.0).astype(int)
        new_activations = (active_source_nodes @ self.adjacency_table).ravel()
        return new_activations

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
        random_values = np.random.rand(*self.node_activations.shape)
        nodes_to_fully_activate = nodes_above_threshold & (
            random_values < full_activation_probabilities
        )
        self.node_activations[nodes_to_fully_activate] = 1.0
