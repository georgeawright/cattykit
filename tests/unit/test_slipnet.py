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
    slipnet = Slipnet(nodes, None, node_index_lookup, node_activations)

    assert 1.0 == slipnet.get_node_activation("cat")
    assert 0.0 == slipnet.get_node_activation("dog")


@pytest.mark.parametrize(
    [
        "start_state",
        "expected_end_state",
    ],
    [
        (
            # no nodes are active, so no activation is spread
            {"cat": 0.0, "dog": 0.0, "animal": 0.0, "is-a": 0.0, "fears": 0.0},
            {"cat": 0.0, "dog": 0.0, "animal": 0.0, "is-a": 0.0, "fears": 0.0},
        ),
        (
            # "cat" spreads activation along the "fears" link to "dog"
            {"cat": 1.0, "dog": 0.0, "animal": 0.0, "is-a": 0.0, "fears": 1.0},
            {"cat": 1.0, "dog": 1.0, "animal": 0.0, "is-a": 0.0, "fears": 1.0},
        ),
        (
            # "fears" is active but "cat" is inactive, so "dog" receives no activation
            {"cat": 0.0, "dog": 0.0, "animal": 0.0, "is-a": 0.0, "fears": 1.0},
            {"cat": 0.0, "dog": 0.0, "animal": 0.0, "is-a": 0.0, "fears": 1.0},
        ),
        (
            # "cat" is active but "fears" is inactive, so "dog" receives no activation
            {"cat": 1.0, "dog": 0.0, "animal": 0.0, "is-a": 0.0, "fears": 0.0},
            {"cat": 1.0, "dog": 0.0, "animal": 0.0, "is-a": 0.0, "fears": 0.0},
        ),
        (
            # "cat" and "dog" spread activation along half-activated "is-a" to "animal"
            {"cat": 1.0, "dog": 1.0, "animal": 0.0, "is-a": 0.5, "fears": 0.0},
            {"cat": 1.0, "dog": 1.0, "animal": 1.0, "is-a": 0.5, "fears": 0.0},
        ),
        (
            # "cat" and "dog" spread activation along 1/4-activated "is-a" to half-activate "animal"
            {"cat": 1.0, "dog": 1.0, "animal": 0.0, "is-a": 0.25, "fears": 0.0},
            {"cat": 1.0, "dog": 1.0, "animal": 0.5, "is-a": 0.25, "fears": 0.0},
        ),
    ],
)
def test_update_activations(start_state, expected_end_state):
    cat_node = SimpleNamespace(name="cat")
    dog_node = SimpleNamespace(name="dog")
    animal_node = SimpleNamespace(name="animal")
    is_a_node = SimpleNamespace(name="is-a")
    fears_node = SimpleNamespace(name="fears")

    cat_is_a_animal = SimpleNamespace(
        from_node=cat_node, to_node=animal_node, type_node=is_a_node
    )
    dog_is_a_animal = SimpleNamespace(
        from_node=dog_node, to_node=animal_node, type_node=is_a_node
    )
    cat_fears_dog = SimpleNamespace(
        from_node=cat_node, to_node=dog_node, type_node=fears_node
    )

    nodes = [cat_node, dog_node, animal_node, is_a_node, fears_node]
    links = [cat_is_a_animal, dog_is_a_animal, cat_fears_dog]

    slipnet = Slipnet.create(nodes, links)

    slipnet.node_activations[slipnet.node_index_lookup["cat"]] = start_state["cat"]
    slipnet.node_activations[slipnet.node_index_lookup["dog"]] = start_state["dog"]
    slipnet.node_activations[slipnet.node_index_lookup["animal"]] = start_state[
        "animal"
    ]
    slipnet.node_activations[slipnet.node_index_lookup["is-a"]] = start_state["is-a"]
    slipnet.node_activations[slipnet.node_index_lookup["fears"]] = start_state["fears"]

    slipnet.update_activations()

    assert slipnet.get_node_activation("cat") == expected_end_state["cat"]
    assert slipnet.get_node_activation("dog") == expected_end_state["dog"]
    assert slipnet.get_node_activation("animal") == expected_end_state["animal"]
    assert slipnet.get_node_activation("is-a") == expected_end_state["is-a"]
    assert slipnet.get_node_activation("fears") == expected_end_state["fears"]
