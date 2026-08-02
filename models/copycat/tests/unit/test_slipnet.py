from types import SimpleNamespace

import numpy as np
import pytest

from copycat import Slipnet

np.random.seed(0)


def test_get_node_activation():
    cat_node = SimpleNamespace(name="cat", activation=1.0)
    dog_node = SimpleNamespace(name="dog", activation=0.0)
    nodes = [cat_node, dog_node]
    node_index_lookup = {node.name: index for index, node in enumerate(nodes)}
    node_activations = np.array([node.activation for node in nodes])
    slipnet = Slipnet(
        nodes, None, node_index_lookup, node_activations, None, None, None, 1.0, 0.5, 3
    )

    assert 1.0 == slipnet.get_node_activation("cat")
    assert 0.0 == slipnet.get_node_activation("dog")


@pytest.mark.parametrize(
    [
        "start_state",  # nodes and their activations
        "depth_factor",  # for the sake of these tests, all nodes will have the same depth
        "cat_is_a_animal_degree_of_association",
        "dog_is_a_animal_degree_of_association",
        "expected_end_state",
    ],
    [
        (
            # no nodes are active, so no activation is spread
            {"cat": 0.0, "dog": 0.0, "animal": 0.0},
            0.0,
            1.0,
            1.0,
            {"cat": 0.0, "dog": 0.0, "animal": 0.0},
        ),
        (
            # no nodes are fully active, so no activation is spread
            {"cat": 0.9, "dog": 0.9, "animal": 0.0},
            0.0,
            1.0,
            1.0,
            {"cat": 0.9, "dog": 0.9, "animal": 0.0},
        ),
        (
            # cat is fully active, so animal becomes fully active
            {"cat": 1.0, "dog": 0.0, "animal": 0.0},
            0.0,
            1.0,
            1.0,
            {"cat": 1.0, "dog": 0.0, "animal": 1.0},
        ),
        (
            # cat is fully active, lower association means animal becomes half active
            {"cat": 1.0, "dog": 0.0, "animal": 0.0},
            0.0,
            0.5,
            0.5,
            {"cat": 1.0, "dog": 0.0, "animal": 0.5},
        ),
        (
            # cat and dog are fully active, animal becomes fully active
            {"cat": 1.0, "dog": 1.0, "animal": 0.0},
            0.0,
            0.5,
            0.5,
            {"cat": 1.0, "dog": 1.0, "animal": 1.0},
        ),
        (
            # cat and dog decay due to a depth factor of 0.5
            {"cat": 1.0, "dog": 1.0, "animal": 0.0},
            0.5,
            0.5,
            0.5,
            {"cat": 0.5, "dog": 0.5, "animal": 1.0},
        ),
    ],
)
def test_update_activations_no_jumping(
    start_state,
    depth_factor,
    cat_is_a_animal_degree_of_association,
    dog_is_a_animal_degree_of_association,
    expected_end_state,
):
    cat_node = SimpleNamespace(name="cat", depth_factor=depth_factor)
    dog_node = SimpleNamespace(name="dog", depth_factor=depth_factor)
    animal_node = SimpleNamespace(name="animal", depth_factor=depth_factor)
    is_a_node = SimpleNamespace(name="is-a", depth_factor=depth_factor)

    cat_is_a_animal = SimpleNamespace(
        source=cat_node,
        target=animal_node,
        type_node=is_a_node,
        intrinsic_degree_of_association=cat_is_a_animal_degree_of_association,
    )
    dog_is_a_animal = SimpleNamespace(
        source=dog_node,
        target=animal_node,
        type_node=is_a_node,
        intrinsic_degree_of_association=dog_is_a_animal_degree_of_association,
    )

    nodes = [cat_node, dog_node, animal_node, is_a_node]
    links = [cat_is_a_animal, dog_is_a_animal]

    # full activation threshold is 1 so there is no probabilistic jumping
    slipnet = Slipnet.create(nodes, links, full_activation_threshold=1.0)

    slipnet.node_activations[slipnet.node_index_lookup["cat"]] = start_state["cat"]
    slipnet.node_activations[slipnet.node_index_lookup["dog"]] = start_state["dog"]
    slipnet.node_activations[slipnet.node_index_lookup["animal"]] = start_state[
        "animal"
    ]

    slipnet.update_activations()

    assert np.isclose(
        slipnet.get_node_activation("cat"),
        expected_end_state["cat"],
    )
    assert np.isclose(
        slipnet.get_node_activation("dog"),
        expected_end_state["dog"],
    )
    assert np.isclose(
        slipnet.get_node_activation("animal"),
        expected_end_state["animal"],
    )


def test_activate_node_from_workspace():
    cat_node = SimpleNamespace(name="cat", depth_factor=0.0)
    nodes = [cat_node]
    node_index_lookup = {node.name: index for index, node in enumerate(nodes)}
    node_activations = np.array([0.0 for _ in nodes])
    node_activation_buffers = np.array([0.0 for _ in nodes])
    slipnet = Slipnet(
        nodes,
        None,
        node_index_lookup,
        node_activations,
        node_activation_buffers,
        None,
        None,
        1.0,
        0.5,
        3,
    )
    slipnet.activate_node_from_workspace("cat")

    assert 0.0 == node_activations[0]
    assert 1.0 == node_activation_buffers[0]
