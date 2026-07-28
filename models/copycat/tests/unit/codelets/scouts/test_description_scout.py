from unittest.mock import Mock

import pytest

from copycat.codelets.scouts import DescriptionScout
from copycat.codelets.strength_testers import DescriptionStrengthTester


def test_propose_description():
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
            return 0

    coderack = MockCoderack()
    slipnet = MockSlipnet()
    workspace = Mock()

    scout = DescriptionScout(
        urgency_bin=0, coderack=coderack, slipnet=slipnet, workspace=workspace
    )
    scout.propose_description(
        chosen_object=Mock(), description_type=Mock(), descriptor=Mock()
    )

    assert coderack.post_called == 1
    assert slipnet.activate_called == 1
    assert isinstance(coderack.posted_codelets[0], DescriptionStrengthTester)
