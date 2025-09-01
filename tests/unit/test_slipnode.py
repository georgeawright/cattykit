import pytest

from copycat import Slipnode


@pytest.mark.parametrize(
    ["activation", "is_active"],
    [
        (1.1, True),
        (1.0, True),
        (0.9999, False),
        (0.9, False),
        (0.5, False),
        (0.0, False),
    ],
)
def test_is_active(activation, is_active):
    slipnode = Slipnode("name", 1, 1, 1, lambda x: None)
    slipnode.activation = activation
    assert is_active == slipnode.is_active()
