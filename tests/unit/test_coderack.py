import random
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from copycat import Coderack

random.seed(1)


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
    coderack = Coderack(urgency_bins, None, 100)
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
    coderack = Coderack(urgency_bins, None, 100)
    assert total_population == coderack.population


@pytest.mark.parametrize(
    ["temperature", "list_index"],
    [
        (0.0, 0),
        (0.001, 0),
        (0.01, 1),
        (0.012, 1),
        (0.015, 2),
        (0.49, 49),
        (0.499, 50),
        (1.0, 100),
    ],
)
def test_get_urgency_bin_weights(temperature, list_index):
    coderack = Coderack.create(7, 100)
    bin_weights = coderack.get_urgency_bin_weights(temperature)
    assert coderack.urgency_lookup_table[list_index] == bin_weights


@pytest.mark.parametrize(
    ["number_of_bins", "activation", "expected"],
    [
        (7, 0.00, 0),
        (7, 0.01, 0),
        (7, 0.14, 0),
        (7, 0.15, 1),
        (7, 0.28, 1),
        (7, 0.29, 2),
        (7, 0.42, 2),
        (7, 0.43, 3),
        (7, 0.57, 3),
        (7, 0.58, 4),
        (7, 0.71, 4),
        (7, 0.72, 5),
        (7, 0.85, 5),
        (7, 0.86, 6),
        (7, 1.00, 6),
    ],
)
def test_get_urgency_level_from_activation(number_of_bins, activation, expected):
    coderack = Coderack.create(number_of_bins, 100)
    urgency_level = coderack.get_urgency_level_from_activation(activation)
    assert expected == urgency_level


def test_post_to_empty_coderack():
    coderack = Coderack.create(7, 100)
    for urgency_bin in range(1, 8):
        codelet = SimpleNamespace(urgency_bin=urgency_bin)
        temperature = 0.0
        assert 0 == len(coderack.get_urgency_bin(urgency_bin))
        coderack.post(codelet, temperature)
        assert 1 == len(coderack.get_urgency_bin(urgency_bin))


def test_post_removes_excess_codelets():
    coderack = Coderack.create(7, 2)
    temperature = 0.0

    codelet_1 = SimpleNamespace(urgency=0.5, urgency_bin=3, birth_time=1)
    codelet_2 = SimpleNamespace(urgency=1.0, urgency_bin=6, birth_time=1)
    assert 0 == coderack.population
    coderack.post(codelet_1, temperature)
    coderack.post(codelet_2, temperature)
    coderack.number_of_codelets_run = 10
    assert 2 == coderack.population
    assert 0.5 == coderack.codelets[0].urgency

    codelet_3 = SimpleNamespace(urgency=0.4, urgency_bin=2)
    coderack.post(codelet_3, temperature)
    assert 2 == coderack.population
    assert 0.4 == coderack.codelets[0].urgency


def test_post_many():
    codelets = [SimpleNamespace(urgency_bin=i % 7) for i in range(11)]
    coderack = Coderack.create(7, 100)
    temperature = 0.0
    assert 0 == coderack.population
    coderack.post_many(codelets, temperature)
    assert 11 == coderack.population


def test_choose():
    codelets = [SimpleNamespace(urgency_bin=i % 7) for i in range(7)]
    coderack = Coderack.create(7, 100)
    temperature = 0.0
    assert 0 == coderack.population
    coderack.post_many(codelets, temperature)
    codelet = coderack.choose(temperature)
    assert codelet.urgency_bin == 6
