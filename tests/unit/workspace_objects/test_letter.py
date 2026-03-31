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
