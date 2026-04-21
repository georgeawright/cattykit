import pytest

from copycat.tools import *


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
        temperature_adjust(value, temperature) for value in values
    ]
    assert expected_values == pytest.approx(
        temperature_adjusted_values,
        abs=0.01,
        rel=0.01,
    )
    assert expected_values == pytest.approx(
        temperature_adjust_list(values, temperature),
        abs=0.01,
        rel=0.01,
    )


@pytest.mark.parametrize(
    [
        "structure_1_strength",
        "weight_1",
        "structure_2_strength",
        "weight_2",
        "temperature",
        "expected_win_proportion",
    ],
    [
        # zero temperature => near deterministic
        (1.0, 1.0, 0.0, 1.0, 0.0, 1.0),
        (0.8, 1.0, 0.2, 1.0, 0.0, 1.0),
        (0.7, 1.0, 0.3, 1.0, 0.0, 0.9),
        (0.5, 1.0, 0.5, 1.0, 0.0, 0.5),
        (0.3, 1.0, 0.7, 1.0, 0.0, 0.1),
        # high temperature => closer to random
        (1.0, 1.0, 0.0, 1.0, 1.0, 1.0),
        (0.8, 1.0, 0.2, 1.0, 1.0, 0.5),
        (0.7, 1.0, 0.3, 1.0, 1.0, 0.5),
        (0.5, 1.0, 0.5, 1.0, 1.0, 0.5),
        (0.3, 1.0, 0.7, 1.0, 1.0, 0.5),
        # mid temperature => in between
        (1.0, 1.0, 0.0, 1.0, 0.5, 1.0),
        (0.8, 1.0, 0.2, 1.0, 0.5, 0.9),
        (0.7, 1.0, 0.3, 1.0, 0.5, 0.8),
        (0.5, 1.0, 0.5, 1.0, 0.5, 0.5),
        (0.3, 1.0, 0.7, 1.0, 0.5, 0.2),
    ],
)
def test_structure_1_beats_structure_2(
    structure_1_strength,
    weight_1,
    structure_2_strength,
    weight_2,
    temperature,
    expected_win_proportion,
):
    class MockStructure:
        def __init__(self, total_strength):
            self.total_strength = total_strength

        def update_strength_values(self):
            pass

    structure_1 = MockStructure(total_strength=structure_1_strength)
    structure_2 = MockStructure(total_strength=structure_2_strength)

    win_count = 0
    for i in range(100):
        result = structure_1_beats_structure_2(
            structure_1, weight_1, structure_2, weight_2, temperature=temperature
        )
        if result:
            win_count += 1

    assert win_count / 100 == pytest.approx(expected_win_proportion, abs=0.1, rel=0.1)
