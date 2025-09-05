from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from copycat import Coderack


@pytest.mark.parametrize(
    ["bin_populations", "total_population"],
    [
        ([1], 1),
        ([1, 2, 3], 6),
        ([1, 1, 1, 1, 1, 1], 6),
        ([10, 10, 10, 10, 10, 10], 60),
    ],
)
def test_codelets(bin_populations, total_population):
    urgency_bins = [
        SimpleNamespace(codelets=[SimpleNamespace() for _ in range(bin_population)])
        for bin_population in bin_populations
    ]
    coderack = Coderack(urgency_bins, None)
    assert total_population == len(coderack.codelets)


@pytest.mark.parametrize(
    ["bin_populations", "total_population"],
    [
        ([1], 1),
        ([1, 2, 3], 6),
        ([1, 1, 1, 1, 1, 1], 6),
        ([10, 10, 10, 10, 10, 10], 60),
    ],
)
def test_population(bin_populations, total_population):
    urgency_bins = []
    for n in bin_populations:
        urgency_bin = MagicMock()
        urgency_bin.__len__.return_value = n
        urgency_bins.append(urgency_bin)
    coderack = Coderack(urgency_bins, None)
    assert total_population == coderack.population
