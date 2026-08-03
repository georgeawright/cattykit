from unittest.mock import Mock

import pytest

from copycat.codelet_result import Finish, Fizzle, FizzleReason
from copycat.codelets.scouts.description_scouts import TopDownDescriptionScout
from copycat.codelets.strength_testers import DescriptionStrengthTester


def test_run():
    class MockCoderack:
        def __init__(self):
            self.posted_codelets = []
            self.post_called = 0

        def post(self, codelet, temperature):
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
        object = None

        def choose_object(self, temperature, salience_function):
            return self.object

    coderack = MockCoderack()
    slipnet = MockSlipnet()
    workspace = MockWorkspace()

    description_type = Mock()
    scout = TopDownDescriptionScout(
        urgency_bin=0,
        coderack=coderack,
        slipnet=slipnet,
        workspace=workspace,
        description_type=description_type,
    )

    # No object to choose
    result = scout.run(temperature=0.0)
    assert isinstance(result, Fizzle)
    assert result.reason == FizzleReason.NO_OBJECTS
    assert coderack.post_called == 0
    assert slipnet.activate_called == 0

    # Description type has no possible descriptors for the object
    workspace.object = Mock()
    description_type.get_possible_descriptors.return_value = []
    result = scout.run(temperature=0.0)
    assert isinstance(result, Fizzle)
    assert result.reason == FizzleReason.NO_POSSIBLE_DESCRIPTORS
    assert coderack.post_called == 0
    assert slipnet.activate_called == 0

    # Description type has possible descriptors
    descriptor = Mock()
    description_type.get_possible_descriptors.return_value = [descriptor]
    result = scout.run(temperature=0.0)
    assert isinstance(result, Finish)
    assert coderack.post_called == 1
    assert slipnet.activate_called == 1
    assert isinstance(coderack.posted_codelets[0], DescriptionStrengthTester)
