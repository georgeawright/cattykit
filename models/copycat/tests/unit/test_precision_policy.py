import pytest
from cattykit.precision_policies import DecimalPlaces, FullPrecision
from copycat.cattykit_plugin import create_model
from copycat.copycat import Copycat
from copycat.tools import temperature_adjust_probability


def test_default_and_full_precision_are_per_model():
    rounded = create_model()
    full = create_model(precision_policy=FullPrecision())
    assert rounded.precision_policy == DecimalPlaces(2)
    assert full.slipnet.precision_policy == FullPrecision()
    assert rounded.workspace.initial_string.precision_policy == DecimalPlaces(2)
    policy = rounded.precision_policy
    assert rounded.slipnet.precision_policy is policy
    assert rounded.workspace.precision_policy is policy
    for string in (
        rounded.workspace.initial_string,
        rounded.workspace.modified_string,
        rounded.workspace.target_string,
        rounded.workspace.answer_string,
    ):
        assert string.precision_policy is policy
    rounded.workspace.initial_string.empty()
    assert rounded.workspace.initial_string.precision_policy is policy


def test_direct_constructor_requires_shared_policy():
    model = create_model()
    args = (
        model.slipnet,
        model.coderack,
        model.workspace,
        model.time_step_length,
        model.initially_clamped_nodes,
        model.initial_slipnode_clamp_time,
        model.logger,
    )
    constructed = Copycat(*args, precision_policy=model.precision_policy)
    assert constructed.precision_policy is model.precision_policy
    with pytest.raises(ValueError, match="same precision policy"):
        Copycat(*args, precision_policy=FullPrecision())
    model.workspace.answer_string.precision_policy = FullPrecision()
    with pytest.raises(ValueError, match="same precision policy"):
        Copycat(*args, precision_policy=model.precision_policy)


def test_activation_rounds_contributions_individually():
    model = create_model()
    net = model.slipnet
    net.node_activations[:] = 0
    net.node_activations[:2] = 1
    net.adjacency_table[:] = 0
    net.adjacency_table[0, 2] = 0.014
    net.adjacency_table[1, 2] = 0.014
    assert net._spread_activations()[2] == pytest.approx(0.02)
    net.precision_policy = FullPrecision()
    assert net._spread_activations()[2] == pytest.approx(0.028)


def test_probabilities_are_not_quantized():
    assert temperature_adjust_probability(0.004, 0) == pytest.approx(0.004)
    assert temperature_adjust_probability(0.004, 0) > 0


def test_structures_inherit_policy_from_their_workspace_or_string():
    from types import SimpleNamespace

    from copycat.workspace_objects_and_structures import (
        Bond,
        Correspondence,
        Description,
        Group,
    )

    policy = DecimalPlaces(1)
    string = SimpleNamespace(precision_policy=policy)
    source = SimpleNamespace(string=string, left_position=0)
    target = SimpleNamespace(string=string, left_position=1)
    workspace = SimpleNamespace(precision_policy=policy)
    structures = [
        Bond(source, target, None, None, None, None, None),
        Description(source, None, None),
        Group(string, 0, 1, [], [], None, None, None),
        Correspondence(workspace, source, target, []),
    ]
    assert all(structure.precision_policy is policy for structure in structures)


def test_structure_rejects_a_source_without_a_string():
    from types import SimpleNamespace

    from copycat.workspace_objects_and_structures import Description

    with pytest.raises(AttributeError):
        Description(SimpleNamespace(), None, None)
