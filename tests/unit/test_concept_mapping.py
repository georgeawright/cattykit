import pytest
from types import SimpleNamespace


from copycat.concept_mapping import ConceptMapping


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
