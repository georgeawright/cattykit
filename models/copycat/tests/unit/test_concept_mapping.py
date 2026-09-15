import pytest
from types import SimpleNamespace


from copycat.concept_mapping import ConceptMapping


@pytest.mark.parametrize(
    "source_descriptor_name, target_descriptor_name, degree_of_association, expected",
    [
        ("same_descriptor", "same_descriptor", None, 1.0),
        ("source_descriptor", "target_descriptor", 0.5, 0.5),
        ("source_descriptor", "target_descriptor", 0.0, 0.0),
    ],
)
def test_degree_of_association(
    source_descriptor_name, target_descriptor_name, degree_of_association, expected
):
    slipnodes = {
        name: SimpleNamespace(name=name)
        for name in [source_descriptor_name, target_descriptor_name]
    }
    slipnodes[source_descriptor_name].lateral_sliplinks = [
        SimpleNamespace(
            target=slipnodes[target_descriptor_name],
            degree_of_association=degree_of_association,
        )
    ]
    concept_mapping = ConceptMapping(
        source_facet=None,
        target_facet=None,
        source_descriptor=slipnodes[source_descriptor_name],
        target_descriptor=slipnodes[target_descriptor_name],
        label=None,
        source=None,
        target=None,
    )
    assert expected == concept_mapping.degree_of_assocation


@pytest.mark.parametrize(
    "source_descriptor_depth, target_descriptor_depth, expected",
    [
        (1.0, 1.0, 1.0),
        (1.0, 0.0, 0.5),
        (0.0, 1.0, 0.5),
        (0.0, 0.0, 0.0),
    ],
)
def test_conceptual_depth(source_descriptor_depth, target_descriptor_depth, expected):
    source_descriptor = SimpleNamespace(conceptual_depth=source_descriptor_depth)
    target_descriptor = SimpleNamespace(conceptual_depth=target_descriptor_depth)
    concept_mapping = ConceptMapping(
        source_facet=None,
        target_facet=None,
        source_descriptor=source_descriptor,
        target_descriptor=target_descriptor,
        label=None,
        source=None,
        target=None,
    )
    assert expected == concept_mapping.conceptual_depth


@pytest.mark.parametrize(
    "source_descriptor_name, target_descriptor_name, "
    "source_descriptor_depth, target_descriptor_depth, "
    "degree_of_association, expected",
    [
        ("same_descriptor", "same_descriptor", 1.0, 1.0, None, 1.0),
        ("source_descriptor", "target_descriptor", 1.0, 1.0, 1.0, 1.0),
        ("source_descriptor", "target_descriptor", 1.0, 1.0, 0.5, 1.0),
        ("source_descriptor", "target_descriptor", 1.0, 1.0, 0.0, 0.0),
        ("source_descriptor", "target_descriptor", 1.0, 0.0, 0.5, 0.625),
        ("source_descriptor", "target_descriptor", 0.0, 1.0, 0.5, 0.625),
        ("source_descriptor", "target_descriptor", 0.0, 0.0, 0.5, 0.5),
    ],
)
def test_strength(
    source_descriptor_name,
    target_descriptor_name,
    source_descriptor_depth,
    target_descriptor_depth,
    degree_of_association,
    expected,
):
    slipnodes = {
        name: SimpleNamespace(name=name, conceptual_depth=depth)
        for name, depth in [
            (source_descriptor_name, source_descriptor_depth),
            (target_descriptor_name, target_descriptor_depth),
        ]
    }
    slipnodes[source_descriptor_name].lateral_sliplinks = [
        SimpleNamespace(
            target=slipnodes[target_descriptor_name],
            degree_of_association=degree_of_association,
        )
    ]
    concept_mapping = ConceptMapping(
        source_facet=None,
        target_facet=None,
        source_descriptor=slipnodes[source_descriptor_name],
        target_descriptor=slipnodes[target_descriptor_name],
        label=None,
        source=None,
        target=None,
    )
    assert expected == concept_mapping.strength


@pytest.mark.parametrize(
    "source_facet_activated, target_facet_activated, expected",
    [
        (True, True, True),
        (True, False, False),
        (False, True, False),
        (False, False, False),
    ],
)
def test_is_relevant(source_facet_activated, target_facet_activated, expected):
    source_facet = SimpleNamespace()
    source_facet.is_active = source_facet_activated
    target_facet = SimpleNamespace()
    target_facet.is_active = target_facet_activated
    concept_mapping = ConceptMapping(
        source_facet=source_facet,
        target_facet=target_facet,
        source_descriptor=None,
        target_descriptor=None,
        label=None,
        source=None,
        target=None,
    )
    assert expected == concept_mapping.is_relevant


@pytest.mark.parametrize(
    "source_descriptor_name, target_descriptor_name, "
    "source_distinguished_by_descriptor, target_distinguished_by_descriptor, "
    "expected",
    [
        ("whole", "whole", True, True, False),
        ("whole", "whole", True, False, False),
        ("whole", "whole", False, True, False),
        ("whole", "whole", False, False, False),
        ("descriptor", "whole", True, True, True),
        ("descriptor", "whole", True, False, False),
        ("descriptor", "whole", False, True, False),
        ("descriptor", "whole", False, False, False),
        ("whole", "descriptor", True, True, True),
        ("whole", "descriptor", True, False, False),
        ("whole", "descriptor", False, True, False),
        ("whole", "descriptor", False, False, False),
        ("descriptor1", "descriptor2", True, True, True),
        ("descriptor1", "descriptor2", True, False, False),
        ("descriptor1", "descriptor2", False, True, False),
        ("descriptor1", "descriptor2", False, False, False),
    ],
)
def test_is_distinguishing(
    source_descriptor_name,
    target_descriptor_name,
    source_distinguished_by_descriptor,
    target_distinguished_by_descriptor,
    expected,
):
    source_descriptor = SimpleNamespace(name=source_descriptor_name)
    target_descriptor = SimpleNamespace(name=target_descriptor_name)
    source = SimpleNamespace()
    source.is_distinguished_by = lambda d: (
        source_distinguished_by_descriptor if d == source_descriptor else False
    )
    target = SimpleNamespace()
    target.is_distinguished_by = lambda d: (
        target_distinguished_by_descriptor if d == target_descriptor else False
    )
    concept_mapping = ConceptMapping(
        source_facet=None,
        target_facet=None,
        source_descriptor=source_descriptor,
        target_descriptor=target_descriptor,
        label=None,
        source=source,
        target=target,
    )
    assert expected == concept_mapping.is_distinguishing


@pytest.mark.parametrize(
    "self_source_descriptor, self_target_descriptor, "
    "other_source_descriptor, other_target_descriptor, "
    "related_1, related_2, "
    "self_label, other_label, "
    "expected",
    [
        ("a", "b", "c", "d", True, False, "e", "e", True),
        ("a", "b", "c", "d", False, True, "e", "e", True),
        ("a", "b", "c", "d", False, True, "e", "f", False),
    ],
)
def test_supports(
    self_source_descriptor,
    self_target_descriptor,
    other_source_descriptor,
    other_target_descriptor,
    related_1,
    related_2,
    self_label,
    other_label,
    expected,
):
    slipnodes = {
        name: SimpleNamespace(name=name)
        for name in [
            self_source_descriptor,
            self_target_descriptor,
            other_source_descriptor,
            other_target_descriptor,
            self_label,
            other_label,
        ]
    }
    slipnodes[self_source_descriptor].is_related_to = (
        lambda other: related_1 if other.name == other_source_descriptor else False
    )
    slipnodes[self_target_descriptor].is_related_to = (
        lambda other: related_2 if other.name == other_target_descriptor else False
    )
    self_concept_mapping = ConceptMapping(
        source_facet=None,
        target_facet=None,
        source_descriptor=slipnodes[self_source_descriptor],
        target_descriptor=slipnodes[self_target_descriptor],
        label=slipnodes[self_label] if self_label is not None else None,
        source=None,
        target=None,
    )
    other_concept_mapping = ConceptMapping(
        source_facet=None,
        target_facet=None,
        source_descriptor=slipnodes[other_source_descriptor],
        target_descriptor=slipnodes[other_target_descriptor],
        label=slipnodes[other_label] if other_label is not None else None,
        source=None,
        target=None,
    )

    assert expected == self_concept_mapping.supports(other_concept_mapping)


@pytest.mark.parametrize(
    "self_source_descriptor, self_target_descriptor, "
    "other_source_descriptor, other_target_descriptor, "
    "related_1, related_2, "
    "self_label, other_label, "
    "expected",
    [
        ("a", "b", "a", "b", None, None, None, None, False),
        ("a", "b", "c", "d", True, False, "e", "f", True),
        ("a", "b", "c", "d", False, True, "e", "f", True),
        ("a", "b", "c", "d", False, False, None, None, False),
        ("a", "b", "c", "d", False, True, "e", "e", False),
        ("a", "b", "c", "d", False, True, None, None, False),
    ],
)
def test_is_incompatible_with(
    self_source_descriptor,
    self_target_descriptor,
    other_source_descriptor,
    other_target_descriptor,
    related_1,
    related_2,
    self_label,
    other_label,
    expected,
):
    slipnodes = {
        name: SimpleNamespace(name=name)
        for name in [
            self_source_descriptor,
            self_target_descriptor,
            other_source_descriptor,
            other_target_descriptor,
            self_label,
            other_label,
        ]
    }
    slipnodes[self_source_descriptor].is_related_to = (
        lambda other: related_1 if other.name == other_source_descriptor else False
    )
    slipnodes[self_target_descriptor].is_related_to = (
        lambda other: related_2 if other.name == other_target_descriptor else False
    )
    self_concept_mapping = ConceptMapping(
        source_facet=None,
        target_facet=None,
        source_descriptor=slipnodes[self_source_descriptor],
        target_descriptor=slipnodes[self_target_descriptor],
        label=slipnodes[self_label] if self_label is not None else None,
        source=None,
        target=None,
    )
    other_concept_mapping = ConceptMapping(
        source_facet=None,
        target_facet=None,
        source_descriptor=slipnodes[other_source_descriptor],
        target_descriptor=slipnodes[other_target_descriptor],
        label=slipnodes[other_label] if other_label is not None else None,
        source=None,
        target=None,
    )

    assert expected == self_concept_mapping.is_incompatible_with(other_concept_mapping)
