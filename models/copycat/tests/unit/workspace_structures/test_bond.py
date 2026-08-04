from types import SimpleNamespace

import pytest

from copycat.workspace_structures import Bond


class MockLetter:
    def __init__(self, left_position, string):
        self.left_position = left_position
        self.right_position = left_position
        self.string = string

    def distance_from(self, other):
        return abs(self.left_position - other.left_position)


class MockGroup:
    def __init__(self, left_position):
        self.left_position = left_position
        self.string = SimpleNamespace()


def test_choose_neighbour():
    class MockString(SimpleNamespace):
        def __len__(self):
            return 3

    string = MockString()
    object_0 = MockLetter(left_position=0, string=string)
    object_1 = MockLetter(left_position=1, string=string)
    object_2 = MockLetter(left_position=2, string=string)

    bond_0_1 = Bond(
        object_0, object_1, SimpleNamespace(name="sameness"), None, None, None, None
    )
    bond_1_2 = Bond(
        object_1, object_2, SimpleNamespace(name="sameness"), None, None, None, None
    )

    object_0.left_neighbours = []
    object_0.right_neighbours = [object_1]
    object_1.left_neighbours = [object_0]
    object_1.right_neighbours = [object_2]
    object_2.left_neighbours = [object_1]
    object_2.right_neighbours = []

    string.bonds_by_position = {
        object_0: {object_0: None, object_1: bond_0_1, object_2: None},
        object_1: {object_0: bond_0_1, object_1: None, object_2: bond_1_2},
        object_2: {object_0: None, object_1: bond_1_2, object_2: None},
    }

    assert bond_0_1.choose_neighbour(direction=SimpleNamespace(name="left")) is None
    assert (
        bond_0_1.choose_neighbour(direction=SimpleNamespace(name="right")) == bond_1_2
    )
    assert bond_1_2.choose_neighbour(direction=SimpleNamespace(name="left")) == bond_0_1
    assert bond_1_2.choose_neighbour(direction=SimpleNamespace(name="right")) is None


def test_get_flipped_version():
    object_0 = MockLetter(left_position=0, string=None)
    object_1 = MockLetter(left_position=1, string=None)

    bond_category = SimpleNamespace(name="bond_category")
    opposite_bond_category = SimpleNamespace(name="opposite_bond_category")
    bond_category.get_related_node = lambda relation: (
        opposite_bond_category if relation == "opposite" else None
    )

    direction_category = SimpleNamespace(name="direction_category")
    opposite_direction_category = SimpleNamespace(name="opposite_direction_category")
    direction_category.get_related_node = lambda relation: (
        opposite_direction_category if relation == "opposite" else None
    )

    bond_facet = SimpleNamespace(name="bond_facet")
    source_descriptor = SimpleNamespace(name="source_descriptor")
    target_descriptor = SimpleNamespace(name="target_descriptor")

    bond = Bond(
        object_0,
        object_1,
        bond_category,
        direction_category,
        bond_facet,
        source_descriptor,
        target_descriptor,
    )

    flipped_bond = bond.get_flipped_version()

    assert flipped_bond.source == bond.target
    assert flipped_bond.target == bond.source
    assert flipped_bond.bond_category == opposite_bond_category
    assert flipped_bond.direction_category == opposite_direction_category
    assert flipped_bond.bond_facet == bond.bond_facet
    assert flipped_bond.source_descriptor == bond.target_descriptor
    assert flipped_bond.target_descriptor == bond.source_descriptor


@pytest.mark.parametrize(
    "source_type, target_type, bond_degree_of_association, bond_facet_name, expected",
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
    source_type, target_type, bond_degree_of_association, bond_facet_name, expected
):
    source = MockLetter(1, None) if source_type == "letter" else MockGroup(1)
    target = MockLetter(2, None) if target_type == "letter" else MockGroup(2)
    bond_category = SimpleNamespace(
        bond_degree_of_association=bond_degree_of_association
    )
    bond_facet = SimpleNamespace(name=bond_facet_name)
    bond = Bond(source, target, bond_category, None, bond_facet, None, None)

    actual = bond.calculate_internal_strength()
    assert expected == pytest.approx(actual)


def test_calculate_external_strength():
    predecessor_category = SimpleNamespace(name="predecessor_category")
    successor_category = SimpleNamespace(name="successor_category")
    letter_category = SimpleNamespace(name="letter_category")

    string = SimpleNamespace()

    object_0 = MockLetter(left_position=0, string=string)
    object_1 = MockLetter(left_position=1, string=string)
    object_2 = MockLetter(left_position=2, string=string)
    object_3 = MockLetter(left_position=3, string=string)

    object_0.choose_left_neighbor = lambda: None
    object_1.choose_left_neighbor = lambda: object_0
    object_2.choose_left_neighbor = lambda: object_1
    object_3.choose_left_neighbor = lambda: object_2

    object_0.choose_right_neighbor = lambda: object_1
    object_1.choose_right_neighbor = lambda: object_2
    object_2.choose_right_neighbor = lambda: object_3
    object_3.choose_right_neighbor = lambda: None

    bond_0_1 = Bond(
        object_0, object_1, successor_category, None, letter_category, None, None
    )
    bond_1_2 = Bond(
        object_1, object_2, successor_category, None, letter_category, None, None
    )
    bond_2_3 = Bond(
        object_3, object_2, predecessor_category, None, letter_category, None, None
    )

    string.bonds = [bond_0_1, bond_1_2, bond_2_3]
    string.bonds_by_position = {
        object_0: {object_0: None, object_1: bond_0_1, object_2: None, object_3: None},
        object_1: {object_0: None, object_1: None, object_2: bond_1_2, object_3: None},
        object_2: {object_0: None, object_1: None, object_2: None, object_3: bond_2_3},
        object_3: {object_0: None, object_1: None, object_2: None, object_3: None},
    }

    assert bond_0_1._number_of_local_supporting_bonds() == 1
    assert bond_1_2._number_of_local_supporting_bonds() == 1
    assert bond_2_3._number_of_local_supporting_bonds() == 0

    assert bond_0_1._local_density() == pytest.approx(0.5)
    assert bond_1_2._local_density() == pytest.approx(0.5)
    assert bond_2_3._local_density() == pytest.approx(0)

    assert bond_0_1.calculate_external_strength() == pytest.approx(0.4242641)
    assert bond_1_2.calculate_external_strength() == pytest.approx(0.4242641)
    assert bond_2_3._local_support() == pytest.approx(0.0)
