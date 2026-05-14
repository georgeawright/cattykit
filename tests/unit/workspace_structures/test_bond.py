from types import SimpleNamespace

import pytest

from copycat.workspace_structures import Bond


class MockLetter:
    def __init__(self, id, left_position, string):
        self.id = id
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
    object_0 = MockLetter(id="o0", left_position=0, string=string)
    object_1 = MockLetter(id="o1", left_position=1, string=string)
    object_2 = MockLetter(id="o2", left_position=2, string=string)

    bond_0_1 = Bond(object_0, object_1, None, None, None, None, None)
    bond_1_2 = Bond(object_1, object_2, None, None, None, None, None)

    bond_0_1.salience = 1.0
    bond_1_2.salience = 1.0

    object_0.left_neighbours = []
    object_0.right_neighbours = [object_1]
    object_1.left_neighbours = [object_0]
    object_1.right_neighbours = [object_2]
    object_2.left_neighbours = [object_1]
    object_2.right_neighbours = []

    string.bonds_by_position = {
        "o0": {"o0": None, "o1": bond_0_1, "o2": None},
        "o1": {"o0": bond_0_1, "o1": None, "o2": bond_1_2},
        "o2": {"o0": None, "o1": bond_1_2, "o2": None},
    }

    assert bond_0_1.choose_neighbour(direction=SimpleNamespace(name="left")) is None
    assert (
        bond_0_1.choose_neighbour(direction=SimpleNamespace(name="right")) == bond_1_2
    )
    assert bond_1_2.choose_neighbour(direction=SimpleNamespace(name="left")) == bond_0_1
    assert bond_1_2.choose_neighbour(direction=SimpleNamespace(name="right")) is None


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
    from_object = MockLetter(None, 1, None) if from_type == "letter" else MockGroup(1)
    to_object = MockLetter(None, 2, None) if to_type == "letter" else MockGroup(2)
    bond_category = SimpleNamespace(
        bond_degree_of_association=bond_degree_of_association
    )
    bond_facet = SimpleNamespace(name=bond_facet_name)
    bond = Bond(from_object, to_object, bond_category, None, bond_facet, None, None)

    actual = bond.calculate_internal_strength()
    assert expected == pytest.approx(actual)


def test_calculate_external_strength():
    predecessor_category = SimpleNamespace(name="predecessor_category")
    successor_category = SimpleNamespace(name="successor_category")
    letter_category = SimpleNamespace(name="letter_category")

    string = SimpleNamespace()

    object_0 = MockLetter(id="o0", left_position=0, string=string)
    object_1 = MockLetter(id="o1", left_position=1, string=string)
    object_2 = MockLetter(id="o2", left_position=2, string=string)
    object_3 = MockLetter(id="o3", left_position=3, string=string)

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
        "o0": {"o0": None, "o1": bond_0_1, "o2": None, "o3": None},
        "o1": {"o0": None, "o1": None, "o2": bond_1_2, "o3": None},
        "o2": {"o0": None, "o1": None, "o2": None, "o3": bond_2_3},
        "o3": {"o0": None, "o1": None, "o2": None, "o3": None},
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
