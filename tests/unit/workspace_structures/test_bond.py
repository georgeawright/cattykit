from types import SimpleNamespace

import pytest

from copycat.workspace_structures import Bond


class MockLetter:
    pass


class MockGroup:
    pass


@pytest.mark.parametrize(
    "from_type, to_type, bond_degree_of_association, bond_facet_name, expected",
    [
        ("letter", "letter", 1.0, "letter_category", 1.0),
        ("group", "group", 1.0, "letter_category", 1.0),
        ("letter", "letter", 0.5, "letter_category", 0.5),
        ("letter", "letter", 1.0, "something_else", 0.7),
        ("letter", "group", 1.0, "letter_category", 0.7),
        ("letter", "group", 1.0, "something_else", 0.49),
        ("letter", "group", 0.5, "something_else", 0.245),
    ],
)
def test_calculate_internal_strength(
    from_type, to_type, bond_degree_of_association, bond_facet_name, expected
):
    from_object = MockLetter() if from_type == "letter" else MockGroup()
    to_object = MockLetter() if to_type == "letter" else MockGroup()
    bond_category = SimpleNamespace(
        bond_degree_of_association=bond_degree_of_association
    )
    bond_facet = SimpleNamespace(name=bond_facet_name)
    bond = Bond(from_object, to_object, bond_category, bond_facet, None, None)

    actual = bond.calculate_internal_strength()
    assert expected == pytest.approx(actual)
