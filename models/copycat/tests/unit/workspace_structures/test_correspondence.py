from types import SimpleNamespace

import pytest

from copycat.workspace_objects import Group, Letter
from copycat.workspace_structures import Correspondence


def test_is_incompatible_argumentwise_with():
    correspondence_1 = Correspondence(
        None,
        source="A",
        target="a",
        concept_mappings=[],
    )
    correspondence_2 = Correspondence(
        None,
        source="A",
        target="b",
        concept_mappings=[],
    )
    correspondence_3 = Correspondence(
        None,
        source="B",
        target="b",
        concept_mappings=[],
    )
    assert correspondence_1.is_incompatible_argumentwise_with(correspondence_2) is True
    assert correspondence_1.is_incompatible_argumentwise_with(correspondence_3) is False
    assert correspondence_2.is_incompatible_argumentwise_with(correspondence_3) is True


def test_is_incompatible_conceptually_with():
    mapping_1 = SimpleNamespace()
    mapping_1.is_distinguishing = lambda: True

    mapping_2 = SimpleNamespace()
    mapping_2.is_distinguishing = lambda: True
    mapping_1.is_incompatible_with = lambda other: other != mapping_2

    mapping_3 = SimpleNamespace()
    mapping_3.is_distinguishing = lambda: True

    correspondence_1 = Correspondence(
        None,
        source="A",
        target="B",
        concept_mappings=[mapping_1],
    )
    correspondence_2 = Correspondence(
        None,
        source="C",
        target="D",
        concept_mappings=[mapping_2],
    )
    correspondence_3 = Correspondence(
        None,
        source="C",
        target="D",
        concept_mappings=[mapping_3],
    )
    correspondence_4 = Correspondence(
        None,
        source="A",
        target="B",
        concept_mappings=[],
    )

    assert correspondence_1.is_incompatible_conceptually_with(correspondence_2) is False
    assert correspondence_1.is_incompatible_conceptually_with(correspondence_3) is True
    assert correspondence_1.is_incompatible_conceptually_with(correspondence_4) is False


def test_is_incompatible_structurally_with():
    letter_a_1 = Letter(None, None, 0)
    letter_a_2 = Letter(None, None, 1)
    letter_b = Letter(None, None, 2)
    group_a_a = Group(None, 0, 1, [letter_a_1, letter_a_2], [], None, None, None)
    group_a_b = Group(None, 0, 1, [letter_a_1, letter_b], [], None, None, None)
    letter_i_1 = Letter(None, None, 0)
    letter_i_2 = Letter(None, None, 1)
    letter_j = Letter(None, None, 2)
    group_i_i = Group(None, 0, 1, [letter_i_1, letter_i_2], [], None, None, None)
    group_i_j = Group(None, 0, 1, [letter_i_1, letter_j], [], None, None, None)

    correspondence_1 = Correspondence(
        None, source=letter_a_1, target=letter_i_1, concept_mappings=[]
    )

    assert correspondence_1.is_incompatible_structurally_with(correspondence_1) is False

    correspondence_2 = Correspondence(
        None, source=letter_a_2, target=letter_i_2, concept_mappings=[]
    )
    letter_a_1.group = group_a_a
    letter_a_2.group = group_a_a
    letter_i_1.group = group_i_i
    letter_i_2.group = group_i_i

    assert correspondence_1.is_incompatible_structurally_with(correspondence_2) is False

    correspondence_3 = Correspondence(
        None, source=group_a_a, target=group_i_j, concept_mappings=[]
    )

    assert correspondence_1.is_incompatible_structurally_with(correspondence_3) is False
    assert correspondence_3.is_incompatible_structurally_with(correspondence_1) is False

    correspondence_4 = Correspondence(
        None, source=group_a_b, target=group_i_i, concept_mappings=[]
    )
    letter_a_2.group = group_a_b
    letter_b.group = group_a_b
    letter_i_2.group = group_i_i
    letter_j.group = group_i_j
    correspondence_5 = Correspondence(
        None, source=letter_a_2, target=letter_i_1, concept_mappings=[]
    )

    assert correspondence_4.is_incompatible_structurally_with(correspondence_5) is True


def test_is_incompatible_boundarywise_with():
    identity_category = SimpleNamespace(name="identity")
    opposite_category = SimpleNamespace(name="opposite")
    identity_mapping = SimpleNamespace(
        label=identity_category,
        description_type_1=SimpleNamespace(name="direction-category"),
        description_type_2=SimpleNamespace(name="direction-category"),
    )
    opposite_mapping = SimpleNamespace(
        label=opposite_category,
        description_type_1=SimpleNamespace(name="direction-category"),
        description_type_2=SimpleNamespace(name="direction-category"),
    )

    source_left = SimpleNamespace()
    target_left = SimpleNamespace()
    source_right = SimpleNamespace()
    target_right = SimpleNamespace()

    source_group = SimpleNamespace(
        is_string_spanning_group=lambda: True,
        left_object=source_left,
        right_object=source_right,
    )
    target_group = SimpleNamespace(
        is_string_spanning_group=lambda: True,
        left_object=target_left,
        right_object=target_right,
    )

    group_correspondence_identity = Correspondence(
        None,
        source=source_group,
        target=target_group,
        concept_mappings=[identity_mapping],
    )

    left_correspondence_identity = Correspondence(
        None,
        source=source_left,
        target=target_left,
        concept_mappings=[identity_mapping],
    )
    right_correspondence_identity = Correspondence(
        None,
        source=source_right,
        target=target_right,
        concept_mappings=[identity_mapping],
    )
    source_left.correspondence = left_correspondence_identity
    source_right.correspondence = right_correspondence_identity

    assert (
        group_correspondence_identity.is_incompatible_boundarywise_with(
            left_correspondence_identity
        )
        is False
    )
    assert (
        group_correspondence_identity.is_incompatible_boundarywise_with(
            right_correspondence_identity
        )
        is False
    )

    left_correspondence_opposite = Correspondence(
        None,
        source=source_left,
        target=target_right,
        concept_mappings=[opposite_mapping],
    )
    right_correspondence_opposite = Correspondence(
        None,
        source=source_right,
        target=target_left,
        concept_mappings=[identity_mapping],
    )
    source_left.correspondence = left_correspondence_opposite
    source_right.correspondence = right_correspondence_opposite

    assert (
        group_correspondence_identity.is_incompatible_boundarywise_with(
            left_correspondence_opposite
        )
        is False
    )
    assert (
        group_correspondence_identity.is_incompatible_boundarywise_with(
            right_correspondence_opposite
        )
        is False
    )


def test_supports():
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
        source="A",
        target="B",
        concept_mappings=[mapping_1],
    )
    correspondence_2 = Correspondence(
        None,
        source="C",
        target="D",
        concept_mappings=[mapping_2],
    )
    correspondence_3 = Correspondence(
        None,
        source="C",
        target="D",
        concept_mappings=[mapping_3],
    )
    correspondence_4 = Correspondence(
        None,
        source="A",
        target="B",
        concept_mappings=[],
    )
    correspondence_5 = Correspondence(
        None,
        source="A",
        target="D",
        concept_mappings=[],
    )

    assert correspondence_1.supports(correspondence_2) is True
    assert correspondence_1.supports(correspondence_3) is False
    assert correspondence_1.supports(correspondence_4) is False
    assert correspondence_1.supports(correspondence_5) is False


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
        source=None,
        target=None,
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
        source=None,
        target=None,
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
        source=None,
        target=None,
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
        source="A",
        target="B",
        concept_mappings=[mapping_1],
    )
    workspace.correspondences.append(correspondence_1)
    assert correspondence_1.calculate_external_strength() == 0.0

    supporting_correspondence = Correspondence(
        workspace,
        source="C",
        target="D",
        concept_mappings=[mapping_2],
    )
    supporting_correspondence.total_strength = 0.1
    workspace.correspondences.append(supporting_correspondence)
    assert correspondence_1.calculate_external_strength() == 0.1

    unsupporting_correspondence = Correspondence(
        workspace,
        source="C",
        target="D",
        concept_mappings=[mapping_3],
    )
    unsupporting_correspondence.total_strength = 0.9
    workspace.correspondences.append(unsupporting_correspondence)
    assert correspondence_1.calculate_external_strength() == 0.1

    supporting_correspondence_2 = Correspondence(
        workspace,
        source="E",
        target="F",
        concept_mappings=[mapping_2],
    )
    supporting_correspondence_2.total_strength = 0.5
    workspace.correspondences.append(supporting_correspondence_2)
    assert correspondence_1.calculate_external_strength() == 0.6
