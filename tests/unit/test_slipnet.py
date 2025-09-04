from types import SimpleNamespace

import pytest
import torch

from copycat import Slipnet


def test_get_node_activation():
    cat_node = SimpleNamespace(name="cat", activation=1.0)
    dog_node = SimpleNamespace(name="dog", activation=0.0)
    nodes = [cat_node, dog_node]
    node_index_lookup = {node.name: index for index, node in enumerate(nodes)}
    node_activations = torch.tensor([node.activation for node in nodes])
    slipnet = Slipnet(
        nodes, None, node_index_lookup, node_activations, None, None, 0.55, 3
    )

    assert 1.0 == slipnet.get_node_activation("cat")
    assert 0.0 == slipnet.get_node_activation("dog")


@pytest.mark.parametrize(
    [
        "start_state",
        "cat_is_a_animal_degree_of_association",
        "dog_is_a_animal_degree_of_association",
        "expected_end_state",
    ],
    [
        (
            # no nodes are active, so no activation is spread
            {"cat": 0.0, "dog": 0.0, "animal": 0.0},
            1.0,
            1.0,
            {"cat": 0.0, "dog": 0.0, "animal": 0.0},
        ),
        (
            # no nodes are fully active, so no activation is spread
            {"cat": 0.9, "dog": 0.9, "animal": 0.0},
            1.0,
            1.0,
            {"cat": 0.9, "dog": 0.9, "animal": 0.0},
        ),
        (
            # cat is fully active, so animal becomes fully active
            {"cat": 1.0, "dog": 0.0, "animal": 0.0},
            1.0,
            1.0,
            {"cat": 1.0, "dog": 0.0, "animal": 1.0},
        ),
        (
            # cat is fully active, lower association means animal becomes half active
            {"cat": 1.0, "dog": 0.0, "animal": 0.0},
            0.5,
            0.5,
            {"cat": 1.0, "dog": 0.0, "animal": 0.5},
        ),
        (
            # cat and dog are fully active, animal becomes fully active
            {"cat": 1.0, "dog": 1.0, "animal": 0.0},
            0.5,
            0.5,
            {"cat": 1.0, "dog": 1.0, "animal": 1.0},
        ),
    ],
)
def test_update_activations_no_jumping_no_decay(
    start_state,
    cat_is_a_animal_degree_of_association,
    dog_is_a_animal_degree_of_association,
    expected_end_state,
):
    # depth factors are zero so there is no decay
    cat_node = SimpleNamespace(name="cat", depth_factor=0.0)
    dog_node = SimpleNamespace(name="dog", depth_factor=0.0)
    animal_node = SimpleNamespace(name="animal", depth_factor=0.0)
    is_a_node = SimpleNamespace(name="is-a", depth_factor=0.0)

    cat_is_a_animal = SimpleNamespace(
        from_node=cat_node,
        to_node=animal_node,
        type_node=is_a_node,
        intrinsic_degree_of_association=cat_is_a_animal_degree_of_association,
    )
    dog_is_a_animal = SimpleNamespace(
        from_node=dog_node,
        to_node=animal_node,
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

    assert slipnet.get_node_activation("cat") == expected_end_state["cat"]
    assert slipnet.get_node_activation("dog") == expected_end_state["dog"]
    assert slipnet.get_node_activation("animal") == expected_end_state["animal"]
