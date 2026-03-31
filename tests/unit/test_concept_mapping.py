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
