from types import SimpleNamespace

import pytest

from copycat import CoderackBin


def test_add_remove_population_and_total_urgency():
    codelet_1 = SimpleNamespace(urgency=0.1)
    codelet_2 = SimpleNamespace(urgency=0.2)

    coderack_bin = CoderackBin(7)
    assert 0 == len(coderack_bin)
    assert 0 == pytest.approx(coderack_bin.total_urgency)

    coderack_bin.add(codelet_1)
    assert 1 == len(coderack_bin)
    assert 7 == pytest.approx(coderack_bin.total_urgency)

    coderack_bin.add(codelet_2)
    assert 2 == len(coderack_bin)
    assert 14 == pytest.approx(coderack_bin.total_urgency)

    coderack_bin.remove(codelet_1)
    assert 1 == len(coderack_bin)
    assert 7 == pytest.approx(coderack_bin.total_urgency)

    coderack_bin.remove(codelet_2)
    assert 0 == len(coderack_bin)
    assert 0 == pytest.approx(coderack_bin.total_urgency)


def test_choose():
    codelets = [SimpleNamespace() for _ in range(10)]
    coderack_bin = CoderackBin(1)
    for codelet in codelets:
        coderack_bin.add(codelet)
    for codelet in codelets:
        codelet = coderack_bin.choose()
        assert codelet in codelets
    with pytest.raises(IndexError):
        coderack_bin.choose()
