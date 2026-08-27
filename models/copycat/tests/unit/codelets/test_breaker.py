import random
from unittest.mock import Mock

import pytest

from copycat.codelet_result import Finish, Fizzle, FizzleReason
from copycat.codelets import Breaker


def test_fizzles_if_temperature_is_too_low():
    breaker = Breaker(Mock(), Mock(), Mock(), Mock())
    result = breaker.run(temperature=0.0)

    assert result == Fizzle(FizzleReason.TEMPERATURE_TOO_LOW)


def test_fizzles_if_there_are_no_structures():
    workspace = Mock()
    workspace.structures = []

    breaker = Breaker(Mock(), Mock(), workspace, Mock())
    result = breaker.run(temperature=1.0)

    assert result == Fizzle(FizzleReason.NO_STRUCTURES)


def test_fizzles_if_structure_too_strong():
    structure = Mock()
    structure.total_weakness = 0.0
    workspace = Mock()
    workspace.structures = [structure]

    breaker = Breaker(Mock(), Mock(), workspace, Mock())
    result = breaker.run(temperature=1.0)

    assert result == Fizzle(FizzleReason.STRUCTURE_TOO_STRONG)


def test_succeeds_if_structure_weak():
    random.seed(1)
    structure = Mock()
    structure.total_weakness = 1.0
    workspace = Mock()
    workspace.structures = [structure]

    breaker = Breaker(Mock(), Mock(), workspace, Mock())
    result = breaker.run(temperature=1.0)

    assert result == Finish()
