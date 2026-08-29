from unittest.mock import Mock

import pytest

from copycat.codelets.strength_testers import CorrespondenceStrengthTester
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
        def __init__(self):
            self.objects = []
            self.target_string = Mock()
            self.target_string.get_group_if_present.return_value = False
            self.delete_proposed_correspondence_called = 0

        def delete_proposed_correspondence(self, proposed_correspondence):
            self.delete_proposed_correspondence_called += 1

    coderack = MockCoderack()
    slipnet = MockSlipnet()
    workspace = MockWorkspace()

    proposed_correspondence = Mock()
    source = Mock()
    target = Mock()
    target_flipped = Mock()
    proposed_correspondence.source = source
    proposed_correspondence.target = target
    proposed_correspondence.target.get_flipped_version.return_value = target_flipped
    proposed_correspondence.concept_mappings = [Mock()]

    strength_tester = CorrespondenceStrengthTester(
        urgency_bin=0,
        coderack=coderack,
        slipnet=slipnet,
        workspace=workspace,
        proposed_correspondence=proposed_correspondence,
        target_flipped=False,
    )

    # if object 1 no longer exists, should fizzle
    workspace.contains_object = Mock(return_value=True)
    result = strength_tester.run(temperature=0.0)
    assert result == Fizzle(FizzleReason.OBJECTS_NO_LONGER_EXIST)
    workspace.contains_object.assert_not_called()
    assert slipnet.activate_called == 0
    assert coderack.post_called == 0

    # if object 2 no longer exists (and is not flipped), should fizzle
    workspace.objects.append(proposed_correspondence.source)
    result = strength_tester.run(temperature=0.0)
    assert result == Fizzle(FizzleReason.OBJECTS_NO_LONGER_EXIST)
    assert slipnet.activate_called == 0
    assert coderack.post_called == 0

    # if object 2 and flipped object 2 no longer exists, should fizzle
    strength_tester.target_flipped = True
    result = strength_tester.run(temperature=0.0)
    assert result == Fizzle(FizzleReason.OBJECTS_NO_LONGER_EXIST)
    assert slipnet.activate_called == 0
    assert coderack.post_called == 0

    # weak correspondence should not post a builder
    workspace.objects.append(proposed_correspondence.target)
    proposed_correspondence.total_strength = 0.0
    strength_tester.target_flipped = False
    result = strength_tester.run(temperature=0.0)
    assert result == Fizzle(FizzleReason.PROPOSED_STRUCTURE_TOO_WEAK)
    assert slipnet.activate_called == 0
    assert coderack.post_called == 0
    assert workspace.delete_proposed_correspondence_called == 1

    # strong correspondence should post a builder
    slipnet.activate_called = 0
    coderack.post_called = 0
    proposed_correspondence.total_strength = 1.0
    result = strength_tester.run(temperature=0.0)
    assert result == Finish()
    assert slipnet.activate_called == 4
    assert coderack.post_called == 1

    # works when object 2 is flipped
    slipnet.activate_called = 0
    coderack.post_called = 0
    workspace.objects = [proposed_correspondence.source, target_flipped]
    workspace.target_string.get_group_if_present.return_value = target_flipped
    strength_tester.target_flipped = True
    result = strength_tester.run(temperature=0.0)
    assert result == Finish()
    assert slipnet.activate_called == 4
    assert coderack.post_called == 1
