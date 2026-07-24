from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from copycat.codelets.scouts.correspondence_scouts import (
    ImportantObjectCorrespondenceScout,
)
from copycat.codelet_result import Finish, Fizzle, FizzleReason
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
            self.proposed_correspondences = 0
            self.slippages = []
            self.object = None

        def choose_object(self, temperature, salience_function):
            return self.object

        def add_proposed_correspondence(self, proposed_correspondence):
            self.proposed_correspondences += 1

    class MockWorkspaceString:
        def __init__(self, objects):
            self.objects = objects

        def choose_object(self, selection_method):
            return self.objects[0] if self.objects else None

    coderack = MockCoderack()
    slipnet = MockSlipnet()
    workspace = MockWorkspace(MockWorkspaceString([]), MockWorkspaceString([]))

    scout = ImportantObjectCorrespondenceScout(
        urgency_bin=0, coderack=coderack, slipnet=slipnet, workspace=workspace
    )

    from_object = SimpleNamespace(spans_whole_string=lambda: True)
    to_object = SimpleNamespace(spans_whole_string=lambda: True)
    workspace.target_string.objects = [to_object]

    # initial string has no objects
    workspace.initial_string.objects = []
    result = scout.run(temperature=0.0)
    assert isinstance(result, Fizzle)
    assert result.reason == FizzleReason.NO_OBJECTS

    # initial string has object but object has no relevant descriptions
    workspace.initial_string.objects = [from_object]
    from_object.choose_relevant_description_by_conceptual_depth = lambda: None
    result = scout.run(temperature=0.0)
    assert isinstance(result, Fizzle)
    assert result.reason == FizzleReason.NO_RELEVANT_DESCRIPTIONS

    # object 1 has relevant description but no objects in target string have that descriptor
    description = SimpleNamespace(descriptor="descriptor")
    from_object.choose_relevant_description_by_conceptual_depth = lambda: description
    to_object.relevant_descriptions = []
    result = scout.run(temperature=0.0)
    assert isinstance(result, Fizzle)
    assert result.reason == FizzleReason.NO_OBJECTS_WITH_DESCRIPTOR

    # object 1 spans string but object 2 does not
    to_object.relevant_descriptions = [description]
    to_object.spans_whole_string = lambda: False
    to_object.inter_string_salience = 0.5
    result = scout.run(temperature=0.0)
    assert coderack.post_called == 0
    assert slipnet.activate_called == 0

    # object 2 spans string but object 1 does not
    from_object.spans_whole_string = lambda: True
    to_object.spans_whole_string = lambda: False
    result = scout.run(temperature=0.0)
    assert coderack.post_called == 0
    assert slipnet.activate_called == 0

    # both objects span whole string but concept mappings not possible
    to_object.spans_whole_string = lambda: True
    description_1 = SimpleNamespace(facet=SimpleNamespace(name="bond"))
    description_2 = SimpleNamespace(facet=SimpleNamespace(name="group"))
    from_object.descriptions = [description_1]
    to_object.descriptions = [description_2]
    result = scout.run(temperature=0.0)
    assert coderack.post_called == 0
    assert slipnet.activate_called == 0

    # concept mappings possible but not distinguishing
    description_1 = SimpleNamespace(
        facet=SimpleNamespace(name="group"), descriptor=SimpleNamespace(name="whole")
    )
    description_2 = SimpleNamespace(
        facet=SimpleNamespace(name="group"), descriptor=SimpleNamespace(name="whole")
    )
    from_object.descriptions = [description_1]
    to_object.descriptions = [description_2]
    result = scout.run(temperature=0.0)
    assert coderack.post_called == 0
    assert slipnet.activate_called == 0

    # distinguishing concept mappings
    successor_node = SimpleNamespace(name="successor", conceptual_depth=0.5)
    predecessor_node = SimpleNamespace(name="predecessor", conceptual_depth=0.5)
    successor_node.is_linked_to = lambda other: other == predecessor_node
    predecessor_node.is_linked_to = lambda other: other == successor_node
    succesor_to_predecessor_link = SimpleNamespace(
        from_node=successor_node, to_node=predecessor_node, degree_of_association=1.0
    )
    predecessor_to_successor_link = SimpleNamespace(
        from_node=predecessor_node, to_node=successor_node, degree_of_association=1.0
    )
    successor_node.lateral_sliplinks = [succesor_to_predecessor_link]
    predecessor_node.lateral_sliplinks = [predecessor_to_successor_link]
    description_1 = SimpleNamespace(
        facet=SimpleNamespace(name="group"), descriptor=successor_node
    )
    description_2 = SimpleNamespace(
        facet=SimpleNamespace(name="group"), descriptor=predecessor_node
    )
    from_object.descriptions = [description_1]
    to_object.descriptions = [description_2]
    from_object.is_distinguished_by = lambda descriptor: True
    to_object.is_distinguished_by = lambda descriptor: True
    result = scout.run(temperature=0.0)
    assert coderack.post_called == 1
    assert result == Finish()
    assert slipnet.activate_called == 4
    assert workspace.proposed_correspondences == 1
