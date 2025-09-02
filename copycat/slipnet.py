import torch


class Slipnet:
    def __init__(
        self,
        nodes: list,  # a list of the nodes in the slipnet
        adjacency_table: torch.Tensor,  # 3D adjacency table (from, to, type)
        node_index_lookup: dict,  # mapping of node_id to index in adjacency table
        node_activations: list,  # the activation value of each node
    ):
        self.nodes = nodes
        self.adjacency_table = adjacency_table
        self.number_of_nodes = len(nodes)
        self.node_index_lookup = node_index_lookup
        self.node_activations = node_activations

    @classmethod
    def create(cls, nodes: list, links: list, device: str = "cpu"):
        number_of_nodes = len(nodes)
        node_index_lookup = {node.name: index for index, node in enumerate(nodes)}
        node_activations = torch.zeros(number_of_nodes, device=device)
        adjacency_table = torch.zeros(
            number_of_nodes, number_of_nodes, number_of_nodes, device=device
        )
        for link in links:
            i = node_index_lookup[link.from_node.name]
            j = node_index_lookup[link.to_node.name]
            k = node_index_lookup[link.type_node.name]
            adjacency_table[i, j, k] = 1
        return cls(nodes, adjacency_table, node_index_lookup, node_activations)

    def get_node_activation(self, node_id):
        return self.node_activations[self.node_index_lookup[node_id]]

    def update_activations(self):
        source_activations = self.node_activations.view(self.number_of_nodes, 1, 1)
        type_activations = self.node_activations.view(1, 1, self.number_of_nodes)
        self.node_activations += (
            (source_activations * self.adjacency_table * type_activations)
            .sum(dim=0)
            .sum(dim=1)
        )
