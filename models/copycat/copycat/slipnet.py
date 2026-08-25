import random
from typing import Callable, Dict, List, Optional

import numpy as np

from cattykit.logging import ModelEvent, ModelLogger

from .concept_mapping import ConceptMapping
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
        node_depths: np.ndarray,  # nodes' conceptual depth
        # the amount of activation to add to nodes from the workspace
        workspace_activation: float,
        # nodes with activation above threshold probabilistically jump to full activation
        full_activation_threshold: float,
        # probability(jumping to full activation) = activation ** exponent
        full_activation_probability_exponent: int,
        logger: ModelLogger | None = None,
    ):
        self.nodes = nodes
        self.adjacency_table = adjacency_table
        self.number_of_nodes = len(nodes)
        self.node_index_lookup = node_index_lookup
        self.node_activations = node_activations
        self.activation_buffers = activation_buffers
        self.clamped_nodes = clamped_nodes
        self.node_depths = node_depths
        self.workspace_activation = workspace_activation
        self.full_activation_threshold = full_activation_threshold
        self.full_activation_probability_exponent = full_activation_probability_exponent
        self.logger = logger

    def set_logger(self, logger: ModelLogger) -> None:
        """Attach the logger used to record slipnet state changes."""
        self.logger = logger

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
        node_depths = np.array([node.conceptual_depth for node in nodes])
        adjacency_table = np.zeros((number_of_nodes, number_of_nodes))
        for link in links:
            link.target.incoming_links.append(link)
            if link.is_category_link:
                link.source.category_links.append(link)
            if link.is_instance_link:
                link.source.instance_links.append(link)
            if link.is_has_property_link:
                link.source.has_property_links.append(link)
            if link.is_lateral_sliplink:
                link.source.lateral_sliplinks.append(link)
            if link.is_lateral_non_sliplink:
                link.source.lateral_non_sliplinks.append(link)
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
            node_depths,
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
                codelets=node_data.get("codelets"),
            )
            for node_data in json_data["nodes"]
        }
        links = [
            Sliplink(
                source=nodes[link_data["source"]],
                target=nodes[link_data["target"]],
                label=nodes[link_data.get("label")]
                if link_data.get("label") is not None
                else None,
                fixed_length=link_data.get("fixed_length"),
                is_category_link=link_data.get("is_category_link", False),
                is_instance_link=link_data.get("is_instance_link", False),
                is_has_property_link=link_data.get("is_has_property_link", False),
                is_lateral_sliplink=link_data.get("is_lateral_sliplink", False),
                is_lateral_non_sliplink=link_data.get("is_lateral_non_sliplink", False),
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

    def log_definition(self) -> None:
        """Record the slipnet topology once at the beginning of a run."""
        links: list[Sliplink] = []
        for node in self.nodes:
            if self.logger is not None:
                self.logger.log(
                    ModelEvent.create(
                        "copycat",
                        "slipnode_initialized",
                        name=node.name,
                        conceptual_depth=node.conceptual_depth,
                        intrinsic_link_length=node.intrinsic_link_length,
                        shrunk_link_length=node.shrunk_link_length,
                    )
                )
            links.extend(node.outgoing_links)
        for link in links:
            if self.logger is not None:
                self.logger.log(
                    ModelEvent.create(
                        "copycat",
                        "sliplink_initialized",
                        source=link.source.name,
                        target=link.target.name,
                        label=None if link.label is None else link.label.name,
                        fixed_length=link.fixed_length,
                        is_category_link=link.is_category_link,
                        is_instance_link=link.is_instance_link,
                        is_has_property_link=link.is_has_property_link,
                        is_lateral_sliplink=link.is_lateral_sliplink,
                        is_lateral_non_sliplink=link.is_lateral_non_sliplink,
                    )
                )

    def update_activations(self) -> None:
        """Recomputes activations according to:
        - activation spread in the slipnet
        - activation boosts from the workspace
        - activation decay according to nodes' conceptual depth
        - probabilistic jumping of node activations
        - clamped nodes remain active."""
        self.node_activations = (
            self.node_activations
            + self._spread_activations()
            + self._decay_activations()
            + self.activation_buffers
        ).clip(0, 1)
        self.activation_buffers.fill(0)  # reset buffers after applying them
        # here "clamp" is copycat terminology meaning to keep activation held at 1
        self.node_activations[self.clamped_nodes] = 1.0
        self._probabilistically_activate_nodes()
        for node in self.nodes:
            node.activation = self.node_activations[self.node_index_lookup[node.name]]
            if self.logger is not None:
                self.logger.log(
                    ModelEvent.create(
                        "copycat",
                        "attribute_updated",
                        object_id=f"slipnode:{node.name}",
                        attribute="activation",
                        value=float(node.activation),
                    )
                )

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

    def get_concept_mappings(
        self,
        source: "WorkspaceObject",
        target: "WorkspaceObject",
        source_descriptions=None,
        target_descriptions=None,
    ) -> List[ConceptMapping]:
        source_descriptions = (
            source.descriptions if source_descriptions is None else source_descriptions
        )
        target_descriptions = (
            target.descriptions if target_descriptions is None else target_descriptions
        )
        mappings = []
        for m in [
            ConceptMapping(
                description_type_1=desc_1.facet,
                description_type_2=desc_2.facet,
                descriptor_1=desc_1.descriptor,
                descriptor_2=desc_2.descriptor,
                label=self.get_label_node(desc_1.descriptor, desc_2.descriptor),
                object_1=source,
                object_2=target,
            )
            for desc_1 in source_descriptions
            for desc_2 in target_descriptions
            if desc_1.facet == desc_2.facet
            and (
                desc_1.descriptor == desc_2.descriptor
                or desc_1.descriptor.is_sliplinked_to(desc_2.descriptor)
            )
        ]:
            if m in mappings:
                continue
            mappings.append(m)
        return mappings

    def get_top_down_codelets(
        self, coderack: "Coderack", workspace: "Workspace"
    ) -> List["Codelet"]:
        # Imports are deferred to avoid the codelet package importing the slipnet
        # again while this module is being initialized.
        from .codelets.scouts.bond_scouts import (
            TopDownCategoryBondScout,
            TopDownDirectionBondScout,
        )
        from .codelets.scouts.description_scouts import TopDownDescriptionScout
        from .codelets.scouts.group_scouts import (
            TopDownCategoryGroupScout,
            TopDownDirectionGroupScout,
        )

        codelet_types = {
            "TopDownCategoryBondScout": (
                TopDownCategoryBondScout,
                "bond_category",
            ),
            "TopDownCategoryGroupScout": (
                TopDownCategoryGroupScout,
                "group_category",
            ),
            "TopDownDescriptionScout": (TopDownDescriptionScout, "description_type"),
            "TopDownDirectionBondScout": (
                TopDownDirectionBondScout,
                "direction_category",
            ),
            "TopDownDirectionGroupScout": (
                TopDownDirectionGroupScout,
                "direction_category",
            ),
        }
        top_down_codelets = []
        for node in self.nodes:
            if node.activation < self.full_activation_threshold:
                continue
            for codelet_name in node.codelets:
                try:
                    codelet_class, node_argument = codelet_types[codelet_name]
                except KeyError as error:
                    raise ValueError(
                        f"Unknown top-down codelet: {codelet_name}"
                    ) from error
                top_down_codelets.append(
                    codelet_class(
                        urgency_bin=coderack.get_urgency_level_from_activation(
                            node.activation
                        ),
                        coderack=coderack,
                        workspace=workspace,
                        slipnet=self,
                        **{node_argument: node},
                    )
                )
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
        return -self.node_activations * (1 - self.node_depths)

    def _probabilistically_activate_nodes(self):
        """Probabilistically fully boost nodes with activation above threshold."""
        nodes_above_threshold = self.node_activations >= self.full_activation_threshold
        full_activation_probabilities = (
            self.node_activations**self.full_activation_probability_exponent
        )
        random_values = np.fromiter(
            (random.random() for _ in range(self.node_activations.size)),
            dtype=float,
            count=self.node_activations.size,
        ).reshape(self.node_activations.shape)
        nodes_to_fully_activate = nodes_above_threshold & (
            random_values < full_activation_probabilities
        )
        self.node_activations[nodes_to_fully_activate] = 1.0
