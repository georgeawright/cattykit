from types import SimpleNamespace

import pytest

from copycat.workspace_objects import Letter


@pytest.mark.parametrize(
    "descriptor, other_descriptors, expected",
    [
        ("letter", ["anything"], False),
        ("group", ["anything"], False),
        ("1", ["anything"], False),
        ("descriptor", ["anything"], True),
        ("descriptor", ["descriptor"], False),
    ],
)
def test_is_distinguished_by(descriptor, other_descriptors, expected):
    string = SimpleNamespace()

    slipnodes = {
        d: SimpleNamespace(name=d) for d in set([descriptor] + other_descriptors)
    }

    letter = Letter(string, None, 0)
    letter.descriptions.append(SimpleNamespace(descriptor=slipnodes[descriptor]))
    other_letter = Letter(string, None, 1)
    for d in other_descriptors:
        other_letter.descriptions.append(SimpleNamespace(descriptor=slipnodes[d]))

    string.letters = [letter, other_letter]

    assert expected == letter.is_distinguished_by(slipnodes[descriptor])


def test_intra_string_happiness_and_unhappiness():
    string = SimpleNamespace()
    letter_1 = Letter(string, None, 0)
    string.letters = [letter_1]

    # lone letters span whole string so are maximally happy and not unhappy
    assert letter_1.calculate_intra_string_happiness() == 1
    assert letter_1.calculate_intra_string_unhappiness() == 0

    letter_2 = Letter(string, None, 1)
    letter_3 = Letter(string, None, 2)
    string.letters += [letter_2, letter_3]

    # letters have no bonds or group membership, so are maximally unhappy and not happy
    assert letter_1.calculate_intra_string_happiness() == 0
    assert letter_1.calculate_intra_string_unhappiness() == 1
    assert letter_2.calculate_intra_string_happiness() == 0
    assert letter_2.calculate_intra_string_unhappiness() == 1
    assert letter_3.calculate_intra_string_happiness() == 0
    assert letter_3.calculate_intra_string_unhappiness() == 1

    # leftmost letter has 1 bond
    letter_1_bond = SimpleNamespace(total_strength=1.0)
    letter_1.outgoing_bonds.append(letter_1_bond)
    assert letter_1.calculate_intra_string_happiness() == pytest.approx(1 / 3)
    assert letter_1.calculate_intra_string_unhappiness() == pytest.approx(2 / 3)

    # middle letter has 1 bond, more unhappy than left letter
    letter_2_bond_1 = SimpleNamespace(total_strength=1.0)
    letter_2.incoming_bonds.append(letter_2_bond_1)
    assert letter_2.calculate_intra_string_happiness() == pytest.approx(1 / 6)
    assert letter_2.calculate_intra_string_unhappiness() == pytest.approx(5 / 6)

    # middle letter has group so is happier than with just a bond
    letter_2.group = SimpleNamespace(total_strength=1.0)
    assert letter_2.calculate_intra_string_happiness() == 1
    assert letter_2.calculate_intra_string_unhappiness() == 0
