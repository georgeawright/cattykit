import numpy as np
import pytest
from cattykit.precision_policies import DecimalPlaces, FullPrecision


def test_decimal_places_rounds_scalars_and_arrays_without_mutation():
    policy = DecimalPlaces(2)
    values = np.array([0.123, 0.456])
    assert policy.quantize(0.126) == 0.13
    np.testing.assert_allclose(policy.quantize(values), [0.12, 0.46])
    np.testing.assert_allclose(values, [0.123, 0.456])
    assert policy.quantize(0.125) == 0.12  # ties to even


@pytest.mark.parametrize("places", [-1, 1.5, True])
def test_invalid_decimal_places(places):
    with pytest.raises(ValueError):
        DecimalPlaces(places)


def test_full_precision_keeps_values():
    value = np.array([0.12345])
    assert FullPrecision().quantize(value) is value
    assert FullPrecision().quantize(0.12345) == 0.12345
