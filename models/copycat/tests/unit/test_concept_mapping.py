import pytest
from types import SimpleNamespace


from copycat.concept_mapping import ConceptMapping


@pytest.mark.parametrize(
    "descriptor_1_name, descriptor_2_name, degree_of_association, expected",
    [
        ("same_descriptor", "same_descriptor", None, 1.0),
        ("descriptor_1", "descriptor_2", 0.5, 0.5),
        ("descriptor_1", "descriptor_2", 0.0, 0.0),
    ],
)
def test_degree_of_association(
    descriptor_1_name, descriptor_2_name, degree_of_association, expected
):
    slipnodes = {
        name: SimpleNamespace(name=name)
        for name in [descriptor_1_name, descriptor_2_name]
    }
    slipnodes[descriptor_1_name].lateral_sliplinks = [
        SimpleNamespace(
            target=slipnodes[descriptor_2_name],
            degree_of_association=degree_of_association,
        )
    ]
    concept_mapping = ConceptMapping(
        description_type_1=None,
        description_type_2=None,
        descriptor_1=slipnodes[descriptor_1_name],
        descriptor_2=slipnodes[descriptor_2_name],
        label=None,
        object_1=None,
        object_2=None,
    )
    assert expected == concept_mapping.degree_of_assocation


@pytest.mark.parametrize(
    "descriptor_1_depth, descriptor_2_depth, expected",
    [
        (1.0, 1.0, 1.0),
        (1.0, 0.0, 0.5),
        (0.0, 1.0, 0.5),
        (0.0, 0.0, 0.0),
    ],
)
def test_conceptual_depth(descriptor_1_depth, descriptor_2_depth, expected):
    descriptor_1 = SimpleNamespace(conceptual_depth=descriptor_1_depth)
    descriptor_2 = SimpleNamespace(conceptual_depth=descriptor_2_depth)
    concept_mapping = ConceptMapping(
        description_type_1=None,
        description_type_2=None,
        descriptor_1=descriptor_1,
        descriptor_2=descriptor_2,
        label=None,
        object_1=None,
        object_2=None,
    )
    assert expected == concept_mapping.conceptual_depth


@pytest.mark.parametrize(
    "descriptor_1_name, descriptor_2_name, "
    "descriptor_1_depth, descriptor_2_depth, "
    "degree_of_association, expected",
    [
        ("same_descriptor", "same_descriptor", 1.0, 1.0, None, 1.0),
        ("descriptor_1", "descriptor_2", 1.0, 1.0, 1.0, 1.0),
        ("descriptor_1", "descriptor_2", 1.0, 1.0, 0.5, 1.0),
        ("descriptor_1", "descriptor_2", 1.0, 1.0, 0.0, 0.0),
        ("descriptor_1", "descriptor_2", 1.0, 0.0, 0.5, 0.625),
        ("descriptor_1", "descriptor_2", 0.0, 1.0, 0.5, 0.625),
        ("descriptor_1", "descriptor_2", 0.0, 0.0, 0.5, 0.5),
    ],
)
def test_strength(
    descriptor_1_name,
    descriptor_2_name,
    descriptor_1_depth,
    descriptor_2_depth,
    degree_of_association,
    expected,
):
    slipnodes = {
        name: SimpleNamespace(name=name, conceptual_depth=depth)
        for name, depth in [
            (descriptor_1_name, descriptor_1_depth),
            (descriptor_2_name, descriptor_2_depth),
        ]
    }
    slipnodes[descriptor_1_name].lateral_sliplinks = [
        SimpleNamespace(
            target=slipnodes[descriptor_2_name],
            degree_of_association=degree_of_association,
        )
    ]
    concept_mapping = ConceptMapping(
        description_type_1=None,
        description_type_2=None,
        descriptor_1=slipnodes[descriptor_1_name],
        descriptor_2=slipnodes[descriptor_2_name],
        label=None,
        object_1=None,
        object_2=None,
    )
    assert expected == concept_mapping.strength


@pytest.mark.parametrize(
    "description_type_1_activated, description_type_2_activated, expected",
    [
        (True, True, True),
        (True, False, False),
        (False, True, False),
        (False, False, False),
    ],
)
def test_is_relevant(
    description_type_1_activated, description_type_2_activated, expected
):
    description_type_1 = SimpleNamespace()
    description_type_1.is_active = lambda: description_type_1_activated
    description_type_2 = SimpleNamespace()
    description_type_2.is_active = lambda: description_type_2_activated
    concept_mapping = ConceptMapping(
        description_type_1=description_type_1,
        description_type_2=description_type_2,
        descriptor_1=None,
        descriptor_2=None,
        label=None,
        object_1=None,
        object_2=None,
    )
    assert expected == concept_mapping.is_relevant()


@pytest.mark.parametrize(
    "descriptor_1_name, descriptor_2_name, "
    "object_1_distinguished_by_descriptor, object_2_distinguished_by_descriptor, "
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
    descriptor_1_name,
    descriptor_2_name,
    object_1_distinguished_by_descriptor,
    object_2_distinguished_by_descriptor,
    expected,
):
    descriptor_1 = SimpleNamespace(name=descriptor_1_name)
    descriptor_2 = SimpleNamespace(name=descriptor_2_name)
    object_1 = SimpleNamespace()
    object_1.is_distinguished_by = lambda d: (
        object_1_distinguished_by_descriptor if d == descriptor_1 else False
    )
    object_2 = SimpleNamespace()
    object_2.is_distinguished_by = lambda d: (
        object_2_distinguished_by_descriptor if d == descriptor_2 else False
    )
    concept_mapping = ConceptMapping(
        description_type_1=None,
        description_type_2=None,
        descriptor_1=descriptor_1,
        descriptor_2=descriptor_2,
        label=None,
        object_1=object_1,
        object_2=object_2,
    )
    assert expected == concept_mapping.is_distinguishing()


@pytest.mark.parametrize(
    "self_descriptor_1, self_descriptor_2, "
    "other_descriptor_1, other_descriptor_2, "
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
    self_descriptor_1,
    self_descriptor_2,
    other_descriptor_1,
    other_descriptor_2,
    related_1,
    related_2,
    self_label,
    other_label,
    expected,
):
    slipnodes = {
        name: SimpleNamespace(name=name)
        for name in [
            self_descriptor_1,
            self_descriptor_2,
            other_descriptor_1,
            other_descriptor_2,
            self_label,
            other_label,
        ]
    }
    slipnodes[self_descriptor_1].is_related_to = (
        lambda other: related_1 if other.name == other_descriptor_1 else False
    )
    slipnodes[self_descriptor_2].is_related_to = (
        lambda other: related_2 if other.name == other_descriptor_2 else False
    )
    self_concept_mapping = ConceptMapping(
        description_type_1=None,
        description_type_2=None,
        descriptor_1=slipnodes[self_descriptor_1],
        descriptor_2=slipnodes[self_descriptor_2],
        label=slipnodes[self_label] if self_label is not None else None,
        object_1=None,
        object_2=None,
    )
    other_concept_mapping = ConceptMapping(
        description_type_1=None,
        description_type_2=None,
        descriptor_1=slipnodes[other_descriptor_1],
        descriptor_2=slipnodes[other_descriptor_2],
        label=slipnodes[other_label] if other_label is not None else None,
        object_1=None,
        object_2=None,
    )

    assert expected == self_concept_mapping.supports(other_concept_mapping)


@pytest.mark.parametrize(
    "self_descriptor_1, self_descriptor_2, "
    "other_descriptor_1, other_descriptor_2, "
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
    self_descriptor_1,
    self_descriptor_2,
    other_descriptor_1,
    other_descriptor_2,
    related_1,
    related_2,
    self_label,
    other_label,
    expected,
):
    slipnodes = {
        name: SimpleNamespace(name=name)
        for name in [
            self_descriptor_1,
            self_descriptor_2,
            other_descriptor_1,
            other_descriptor_2,
            self_label,
            other_label,
        ]
    }
    slipnodes[self_descriptor_1].is_related_to = (
        lambda other: related_1 if other.name == other_descriptor_1 else False
    )
    slipnodes[self_descriptor_2].is_related_to = (
        lambda other: related_2 if other.name == other_descriptor_2 else False
    )
    self_concept_mapping = ConceptMapping(
        description_type_1=None,
        description_type_2=None,
        descriptor_1=slipnodes[self_descriptor_1],
        descriptor_2=slipnodes[self_descriptor_2],
        label=slipnodes[self_label] if self_label is not None else None,
        object_1=None,
        object_2=None,
    )
    other_concept_mapping = ConceptMapping(
        description_type_1=None,
        description_type_2=None,
        descriptor_1=slipnodes[other_descriptor_1],
        descriptor_2=slipnodes[other_descriptor_2],
        label=slipnodes[other_label] if other_label is not None else None,
        object_1=None,
        object_2=None,
    )

    assert expected == self_concept_mapping.is_incompatible_with(other_concept_mapping)
