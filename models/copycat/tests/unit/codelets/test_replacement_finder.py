from unittest.mock import Mock

import pytest

from copycat.codelet_result import Finish, Fizzle, FizzleReason
from copycat.codelets import ReplacementFinder


def test_fizzles_if_initial_letter_has_replacement():
    initial_letter = Mock()
    initial_letter.replacemet = Mock()

    workspace = Mock()
    workspace.initial_string.letters = [initial_letter]

    replacement_finder = ReplacementFinder(0, Mock(), workspace, Mock())
    result = replacement_finder.run(temperature=0.0)

    assert result == Fizzle(FizzleReason.LETTER_ALREADY_HAS_REPLACEMENT)
