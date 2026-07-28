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
        None,
        from_object="A",
        to_object="B",
        concept_mappings=[mapping_1],
    )
    correspondence_2 = Correspondence(
        None,
        from_object="C",
        to_object="D",
        concept_mappings=[mapping_2],
    )
    correspondence_3 = Correspondence(
        None,
        from_object="C",
        to_object="D",
        concept_mappings=[mapping_3],
    )
    correspondence_4 = Correspondence(
        None,
        from_object="A",
        to_object="B",
        concept_mappings=[],
    )
    correspondence_5 = Correspondence(
        None,
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
        None,
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
        None,
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
        None,
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


def test_calculate_external_strength():
    workspace = SimpleNamespace(correspondences=[])

    mapping_1 = SimpleNamespace()
    mapping_1.is_distinguishing = lambda: True

    mapping_2 = SimpleNamespace()
    mapping_2.is_distinguishing = lambda: True
    mapping_1.supports = lambda other: other == mapping_2
    mapping_1.is_incompatible_with = lambda other: other != mapping_2

    mapping_3 = SimpleNamespace()
    mapping_3.is_distinguishing = lambda: True

    correspondence_1 = Correspondence(
        workspace,
        from_object="A",
        to_object="B",
        concept_mappings=[mapping_1],
    )
    workspace.correspondences.append(correspondence_1)
    assert correspondence_1.calculate_external_strength() == 0.0

    supporting_correspondence = Correspondence(
        workspace,
        from_object="C",
        to_object="D",
        concept_mappings=[mapping_2],
    )
    supporting_correspondence.total_strength = 0.1
    workspace.correspondences.append(supporting_correspondence)
    assert correspondence_1.calculate_external_strength() == 0.1

    unsupporting_correspondence = Correspondence(
        workspace,
        from_object="C",
        to_object="D",
        concept_mappings=[mapping_3],
    )
    unsupporting_correspondence.total_strength = 0.9
    workspace.correspondences.append(unsupporting_correspondence)
    assert correspondence_1.calculate_external_strength() == 0.1

    supporting_correspondence_2 = Correspondence(
        workspace,
        from_object="E",
        to_object="F",
        concept_mappings=[mapping_2],
    )
    supporting_correspondence_2.total_strength = 0.5
    workspace.correspondences.append(supporting_correspondence_2)
    assert correspondence_1.calculate_external_strength() == 0.6
