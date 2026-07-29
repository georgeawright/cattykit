from unittest.mock import MagicMock, Mock

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


def test_sets_initial_letter_to_changed_if_different():
    slipnet = MagicMock()
    slipnet.__getitem__ = Mock()

    letter_a = Mock()
    letter_b = Mock()

    initial_letter = Mock()
    initial_letter.get_descriptor.return_value = letter_a
    initial_letter.left_position = 0
    initial_letter.replacement = None
    initial_letter.is_changed_letter = False

    modified_letter = Mock()
    modified_letter.get_descriptor.return_value = letter_b

    workspace = Mock()
    workspace.initial_string.letters = [initial_letter]
    workspace.modified_string.letters = [modified_letter]

    replacement_finder = ReplacementFinder(0, Mock(), workspace, slipnet)
    result = replacement_finder.run(temperature=0.0)

    assert result == Finish()
    assert initial_letter.is_changed_letter is True
    assert initial_letter.replacement is not None
