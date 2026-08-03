from unittest.mock import Mock

import pytest

from copycat.codelets.strength_testers import BondStrengthTester
from copycat.codelet_result import Finish, Fizzle, FizzleReason


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

    class MockWorkspace:
        pass

    coderack = MockCoderack()
    slipnet = MockSlipnet()
    workspace = MockWorkspace()

    proposed_bond = Mock()
    strength_tester = BondStrengthTester(
        urgency_bin=0,
        coderack=coderack,
        slipnet=slipnet,
        workspace=workspace,
        proposed_bond=proposed_bond,
    )

    # weak bond should not post a builder
    proposed_bond.total_strength = 0.0
    result = strength_tester.run(temperature=0.0)
    assert result == Fizzle(FizzleReason.PROPOSED_STRUCTURE_TOO_WEAK)
    assert slipnet.activate_called == 0
    assert coderack.post_called == 0

    # strong bond should post a builder
    slipnet.activate_called = 0
    coderack.post_called = 0
    proposed_bond.total_strength = 1.0
    result = strength_tester.run(temperature=0.0)
    assert result == Finish()
    assert slipnet.activate_called == 3
    assert coderack.post_called == 1
