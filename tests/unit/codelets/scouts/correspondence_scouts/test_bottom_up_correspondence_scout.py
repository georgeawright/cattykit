from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from copycat.codelets.scouts.correspondence_scouts import BottomUpCorrespondenceScout
from copycat.codelets.strength_testers import CorrespondenceStrengthTester


def test_run():
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

        def __getitem__(self, name):
            return SimpleNamespace(name=name)

        def activate_node_from_workspace(self, name):
            self.activate_called += 1

        def get_node_activation(self, name):
            return 0.5

    class MockWorkspace:
        def __init__(self, initial_string, target_string):
            self.initial_string = initial_string
            self.target_string = target_string
            object = None

        def choose_object(self, temperature, salience_function):
            return self.object

    class MockWorkspaceString:
        def __init__(self, objects):
            self.objects = objects

        def choose_object(self, selection_method):
            return self.objects[0]

    coderack = MockCoderack()
    slipnet = MockSlipnet()
    workspace = MockWorkspace(MockWorkspaceString([]), MockWorkspaceString([]))

    scout = BottomUpCorrespondenceScout(
        urgency_bin=0, coderack=coderack, slipnet=slipnet, workspace=workspace
    )

    object_1 = SimpleNamespace(spans_whole_string=lambda: True)
    object_2 = SimpleNamespace(spans_whole_string=lambda: True)
    workspace.initial_string.objects = [object_1]
    workspace.target_string.objects = [object_2]

    # object 1 spans string but object 2 does not
    object_2.spans_whole_string = lambda: False
    scout.run(temperature=0.0)
    assert coderack.post_called == 0
    assert slipnet.activate_called == 0

    # object 2 spans string but object 1 does not
    object_1.spans_whole_string = lambda: True
    object_2.spans_whole_string = lambda: False
    scout.run(temperature=0.0)
    assert coderack.post_called == 0
    assert slipnet.activate_called == 0

    # both objects span whole string but concept mappings not possible
    object_2.spans_whole_string = lambda: True
    scout.run(temperature=0.0)
    assert coderack.post_called == 0
    assert slipnet.activate_called == 0
