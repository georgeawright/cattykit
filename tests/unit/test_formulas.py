import pytest

from copycat.formulas import *


@pytest.mark.parametrize(
    ["values", "temperature", "expected_values"],
    [
        # low temperatures exaggerate differences
        ([0, 0.2, 0.4, 0.6, 0.8, 1], 0.0, [0.00, 0.00, 0.05, 0.18, 0.47, 1.00]),
        ([0, 0.2, 0.4, 0.6, 0.8, 1], 0.2, [0.00, 0.01, 0.09, 0.26, 0.55, 1.00]),
        # mid temperatures make smaller adjustments
        ([0, 0.2, 0.4, 0.6, 0.8, 1], 0.4, [0.00, 0.04, 0.16, 0.36, 0.64, 1.00]),
        ([0, 0.2, 0.4, 0.6, 0.8, 1], 0.6, [0.00, 0.12, 0.29, 0.50, 0.74, 1.00]),
        # high temperatures flatten differences
        ([0, 0.2, 0.4, 0.6, 0.8, 1], 0.8, [0.00, 0.34, 0.54, 0.71, 0.86, 1.00]),
        ([0, 0.2, 0.4, 0.6, 0.8, 1], 1.0, [0.00, 0.99, 1.00, 1.00, 1.00, 1.00]),
    ],
)
def test_temperature_adjust(values, temperature, expected_values):
    temperature_adjusted_values = [
        round(temperature_adjust(value, temperature), 2) for value in values
    ]
    assert expected_values == pytest.approx(temperature_adjusted_values)
