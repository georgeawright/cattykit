from unittest.mock import Mock

import pytest

from copycat.codelet_result import CodeletResult, Finish, Fizzle, FizzleReason
from copycat.codelets.scouts.description_scouts import BottomUpDescriptionScout
from copycat.codelets.strength_testers import DescriptionStrengthTester


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

    scout = BottomUpDescriptionScout(
        urgency_bin=0, coderack=coderack, slipnet=slipnet, workspace=workspace
    )

    # No object to choose
    result = scout.run(temperature=0.0)
    assert isinstance(result, Fizzle)
    assert result.reason == FizzleReason.NO_OBJECTS
    assert coderack.post_called == 0
    assert slipnet.activate_called == 0

    # Object with no relevant description
    workspace.object = Mock()
    workspace.object.choose_relevant_description_by_activation.return_value = None
    result = scout.run(temperature=0.0)
    assert isinstance(result, Fizzle)
    assert result.reason == FizzleReason.NO_RELEVANT_DESCRIPTIONS
    assert coderack.post_called == 0
    assert slipnet.activate_called == 0

    # Object with relevant description but no has property links
    descriptor = Mock()
    descriptor.get_similar_has_property_links.return_value = []
    workspace.object.choose_relevant_description_by_activation.return_value = Mock(
        descriptor=descriptor
    )
    result = scout.run(temperature=0.0)
    assert isinstance(result, Fizzle)
    assert result.reason == FizzleReason.NO_RELEVANT_HAS_PROPERTY_LINKS
    assert coderack.post_called == 0
    assert slipnet.activate_called == 0

    # Object with relevant description and has property links
    link = Mock()
    link.degree_of_association = 1
    link.target.name = "property"
    descriptor.get_similar_has_property_links.return_value = [link]
    result = scout.run(temperature=0.0)
    assert isinstance(result, Finish)
    assert coderack.post_called == 1
    assert slipnet.activate_called == 1
    assert isinstance(coderack.posted_codelets[0], DescriptionStrengthTester)
