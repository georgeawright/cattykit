from unittest.mock import Mock

import pytest

from copycat.codelets.builders import DescriptionBuilder
from copycat.codelet_result import Finish, Fizzle, FizzleReason


def test_run_fizzles_if_argument_object_no_longer_exists():
    class MockWorkspace:
        objects = []

    workspace = MockWorkspace()
    description = Mock()
    description.argument_object = Mock()
    description.argument_object.descriptions = []
    builder = DescriptionBuilder(
        urgency_bin=0,
        coderack=Mock(),
        slipnet=Mock(),
        workspace=workspace,
        proposed_description=description,
    )
    result = builder.run(temperature=0.0)
    assert result == Fizzle(FizzleReason.OBJECTS_NO_LONGER_EXIST)
    # If the argument object doesn't exist, the description shouldn't be added to it
    assert description not in description.argument_object.descriptions


def test_activates_slipnodes_if_description_exists():
    class MockCoderack:
        def __init__(self):
            self.posted_codelets = []
            self.post_called = 0

        def post(self, codelet):
            self.post_called += 1
            self.posted_codelets.append(codelet)

        def get_urgency_level_from_activation(self, activation):
            return 0

    class MockSlipnet:
        def __init__(self):
            self.activate_called = 0

        def activate_node_from_workspace(self, name):
            self.activate_called += 1

        def get_node_activation(self, name):
            return 0.5

    class MockWorkspace:
        objects = []

    coderack = MockCoderack()
    slipnet = MockSlipnet()
    workspace = MockWorkspace()

    proposed_description = Mock()
    argument_object = Mock()
    argument_object.descriptions = [proposed_description]
    proposed_description.argument_object = argument_object
    workspace.objects.append(argument_object)

    builder = DescriptionBuilder(
        urgency_bin=0,
        coderack=coderack,
        slipnet=slipnet,
        workspace=workspace,
        proposed_description=proposed_description,
    )

    result = builder.run(temperature=0.0)
    # If the description already exists, the slipnodes for the descriptor and facet should be activated
    assert slipnet.activate_called == 2


def test_adds_description_to_argument_object():
    class MockCoderack:
        def __init__(self):
            self.posted_codelets = []
            self.post_called = 0

        def post(self, codelet):
            self.post_called += 1
            self.posted_codelets.append(codelet)

        def get_urgency_level_from_activation(self, activation):
            return 0

    class MockSlipnet:
        def __init__(self):
            self.activate_called = 0

        def activate_node_from_workspace(self, name):
            self.activate_called += 1

        def get_node_activation(self, name):
            return 0.5

    class MockWorkspace:
        objects = []

    coderack = MockCoderack()
    slipnet = MockSlipnet()
    workspace = MockWorkspace()

    proposed_description = Mock()
    proposed_description.is_bond_description.return_value = False
    argument_object = Mock()
    argument_object.add_description_has_been_called = False
    argument_object.add_description = lambda description: setattr(
        argument_object, "add_description_has_been_called", True
    )
    argument_object.has_description.return_value = False
    proposed_description.argument_object = argument_object
    workspace.objects.append(argument_object)

    builder = DescriptionBuilder(
        urgency_bin=0,
        coderack=coderack,
        slipnet=slipnet,
        workspace=workspace,
        proposed_description=proposed_description,
    )

    result = builder.run(temperature=0.0)
    assert result == Finish()
    # If the description doesn't already exist, it should be added to the argument object
    assert argument_object.add_description_has_been_called
    assert slipnet.activate_called == 2

    proposed_bond_description = Mock()
    proposed_bond_description.is_bond_description.return_value = True
    argument_object = Mock()
    argument_object.add_description_has_been_called = False
    argument_object.add_description = lambda description: setattr(
        argument_object, "add_description_has_been_called", True
    )
    argument_object.has_description.return_value = False
    proposed_bond_description.argument_object = argument_object
    workspace.objects.append(argument_object)

    builder = DescriptionBuilder(
        urgency_bin=0,
        coderack=coderack,
        slipnet=slipnet,
        workspace=workspace,
        proposed_description=proposed_bond_description,
    )

    builder.run(temperature=0.0)
    # If the description doesn't already exist, it should be added to the argument object
    assert argument_object.add_description_has_been_called
    assert slipnet.activate_called == 4
