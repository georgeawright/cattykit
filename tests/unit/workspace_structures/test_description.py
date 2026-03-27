from types import SimpleNamespace
import pytest


from copycat.workspace_structures import Description


@pytest.mark.parametrize(
    "descriptor_depth, expected",
    [
        (0.0, 0.0),
        (0.5, 0.5),
        (1.0, 1.0),
    ],
)
def test_calculate_internal_strength(descriptor_depth, expected):
    descriptor = SimpleNamespace(conceptual_depth=descriptor_depth)
    description = Description(argument_object=None, facet=None, descriptor=descriptor)

    assert expected == description.calculate_internal_strength()


def test_calculate_external_strength():
    string = SimpleNamespace(objects=[])
    argument = SimpleNamespace(string=string)
    string.objects.append(argument)
    facet = SimpleNamespace(activation=0.5)
    supporting_objects = [
        SimpleNamespace(descriptions=[SimpleNamespace(facet=facet)]),
        SimpleNamespace(descriptions=[SimpleNamespace(facet=facet)]),
        SimpleNamespace(descriptions=[SimpleNamespace(facet=facet)]),
        SimpleNamespace(descriptions=[SimpleNamespace(facet=facet)]),
    ]
    argument.has_recursive_group_member = lambda o: False
    for o in supporting_objects:
        o.has_recursive_group_member = lambda other: False
    description = Description(argument_object=argument, facet=facet, descriptor=None)

    # No supporting objects
    assert 0.25 == description.calculate_external_strength()

    # One supporting object
    string.objects.append(supporting_objects[0])
    assert 0.35 == description.calculate_external_strength()

    # Two supporting objects
    string.objects.append(supporting_objects[1])
    assert 0.55 == description.calculate_external_strength()

    # Three supporting objects
    string.objects.append(supporting_objects[2])
    assert 0.7 == description.calculate_external_strength()

    # More than three supporting objects
    string.objects.append(supporting_objects[3])
    assert 0.75 == description.calculate_external_strength()
