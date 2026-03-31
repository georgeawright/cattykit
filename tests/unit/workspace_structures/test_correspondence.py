from types import SimpleNamespace

import pytest

from copycat.workspace_structures import Correspondence


def test_supports_and_is_incompatible_with():
    mapping_1 = SimpleNamespace()
    mapping_1.is_distinguishing = lambda: True

    mapping_2 = SimpleNamespace()
    mapping_2.is_distinguishing = lambda: True
    mapping_1.supports = lambda other: other == mapping_2
    mapping_1.is_incompatible_with = lambda other: other != mapping_2

    mapping_3 = SimpleNamespace()
    mapping_3.is_distinguishing = lambda: True

    correspondence_1 = Correspondence(
        from_object="A",
        to_object="B",
        concept_mappings=[mapping_1],
    )
    correspondence_2 = Correspondence(
        from_object="C",
        to_object="D",
        concept_mappings=[mapping_2],
    )
    correspondence_3 = Correspondence(
        from_object="C",
        to_object="D",
        concept_mappings=[mapping_3],
    )
    correspondence_4 = Correspondence(
        from_object="A",
        to_object="B",
        concept_mappings=[],
    )
    correspondence_5 = Correspondence(
        from_object="A",
        to_object="D",
        concept_mappings=[],
    )

    assert correspondence_1.supports(correspondence_2) is True
    assert correspondence_1.is_incompatible_with(correspondence_2) is False
    assert correspondence_1.supports(correspondence_3) is False
    assert correspondence_1.is_incompatible_with(correspondence_3) is True
    assert correspondence_1.supports(correspondence_4) is False
    assert correspondence_1.is_incompatible_with(correspondence_4) is True
    assert correspondence_1.supports(correspondence_5) is False
    assert correspondence_1.is_incompatible_with(correspondence_5) is True


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

    assert correspondence.get_relevant_mappings() == [
        relevant_not_distinguishing,
        relevant_distinguishing,
    ]
    assert correspondence.get_distinguishing_mappings() == [
        distinguishing_not_relevant,
        relevant_distinguishing,
    ]
    assert correspondence.get_relevant_distinguishing_mappings() == [
        relevant_distinguishing
    ]


def test_is_internally_coherent():
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


def test_calculate_internal_strength():
    relevant_distinguishing = SimpleNamespace()
    relevant_distinguishing.is_distinguishing = lambda: True
    relevant_distinguishing.is_relevant = lambda: True
    relevant_distinguishing.strength = 0.5

    correspondence = Correspondence(
        from_object=None,
        to_object=None,
        concept_mappings=[relevant_distinguishing],
    )

    assert correspondence.calculate_internal_strength() == 0.4

    second_relevant_distinguishing = SimpleNamespace()
    second_relevant_distinguishing.is_distinguishing = lambda: True
    second_relevant_distinguishing.is_relevant = lambda: True
    second_relevant_distinguishing.strength = 0.8
    relevant_distinguishing.supports = (
        lambda other: other == second_relevant_distinguishing
    )
    correspondence.concept_mappings.append(second_relevant_distinguishing)

    assert correspondence.calculate_internal_strength() == 1.0
