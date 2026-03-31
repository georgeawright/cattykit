from types import SimpleNamespace

import pytest

from copycat.workspace_structures import Correspondence


def test_get_relevant_distinguishing_mappings():
    distinguishing_not_relevant = SimpleNamespace()
    distinguishing_not_relevant.is_distinguishing = lambda: True
    distinguishing_not_relevant.is_relevant = lambda: False

    relevant_not_distinguishing = SimpleNamespace()
    relevant_not_distinguishing.is_distinguishing = lambda: False
    relevant_not_distinguishing.is_relevant = lambda: True

    relevant_distinguishing = SimpleNamespace()
    relevant_distinguishing.is_distinguishing = lambda: True
    relevant_distinguishing.is_relevant = lambda: True

    correspondence = Correspondence(
        from_object=None,
        to_object=None,
        concept_mappings=[
            distinguishing_not_relevant,
            relevant_not_distinguishing,
            relevant_distinguishing,
        ],
    )

    assert correspondence.get_relevant_distinguishing_mappings() == [
        relevant_distinguishing
    ]


def test_is_inherently_coherent():
    distinguishing_not_relevant = SimpleNamespace()
    distinguishing_not_relevant.is_distinguishing = lambda: True
    distinguishing_not_relevant.is_relevant = lambda: False

    relevant_not_distinguishing = SimpleNamespace()
    relevant_not_distinguishing.is_distinguishing = lambda: False
    relevant_not_distinguishing.is_relevant = lambda: True

    relevant_distinguishing = SimpleNamespace()
    relevant_distinguishing.is_distinguishing = lambda: True
    relevant_distinguishing.is_relevant = lambda: True

    correspondence = Correspondence(
        from_object=None,
        to_object=None,
        concept_mappings=[
            distinguishing_not_relevant,
            relevant_not_distinguishing,
            relevant_distinguishing,
        ],
    )

    assert correspondence.is_internally_coherent() is False

    second_relevant_distinguishing = SimpleNamespace()
    second_relevant_distinguishing.is_distinguishing = lambda: True
    second_relevant_distinguishing.is_relevant = lambda: True
    correspondence.concept_mappings.append(second_relevant_distinguishing)

    relevant_distinguishing.supports = (
        lambda other: other == second_relevant_distinguishing
    )

    assert correspondence.is_internally_coherent()
