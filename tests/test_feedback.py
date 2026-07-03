"""Feedback scoring tests.

The duplicate-letter vectors below are hand-verified against official Wordle
rules (greens consume target letters first; yellows consume remaining
occurrences left-to-right).
"""

from __future__ import annotations

import pytest

from wordlesmith.feedback import (
    ALL_GREEN,
    NUM_PATTERNS,
    feedback,
    pattern_from_string,
    pattern_to_string,
)
from wordlesmith.words import load_valid_words

# (guess, target, expected pattern string, description)
DUPLICATE_LETTER_CASES = [
    ("speed", "abide", "xxyxy", "two E in guess, one in target: first E yellow, second gray"),
    ("speed", "erase", "yxyyx", "two E in guess, two in target: both yellow"),
    ("greet", "stage", "yxyxy", "first E yellow, second gray (notebook's own example)"),
    ("sassy", "class", "yyxgx", "green S consumes a target S before yellows"),
    ("alley", "llama", "ygyxx", "green + yellow of the same letter L in one guess"),
    ("geese", "eerie", "xgyxg", "triple letter in guess; greens consume before yellow"),
    ("crane", "crane", "ggggg", "exact match"),
    ("aaaaa", "crane", "xxgxx", "repeated guess letter, single target occurrence already green"),
]


@pytest.mark.parametrize(
    ("guess", "target", "expected"),
    [(g, t, e) for g, t, e, _ in DUPLICATE_LETTER_CASES],
    ids=[f"{g}-{t}" for g, t, _, _ in DUPLICATE_LETTER_CASES],
)
def test_duplicate_letter_vectors(guess: str, target: str, expected: str) -> None:
    assert pattern_to_string(feedback(guess, target)) == expected


def test_all_patterns_round_trip() -> None:
    for code in range(NUM_PATTERNS):
        assert pattern_from_string(pattern_to_string(code)) == code


def test_self_feedback_is_all_green() -> None:
    # A word scored against itself is all green, for every valid word.
    for word in load_valid_words():
        assert feedback(word, word) == ALL_GREEN


def test_feedback_is_case_insensitive() -> None:
    assert feedback("CRANE", "slate") == feedback("crane", "SLATE")


def test_legacy_numeric_feedback_parsing() -> None:
    assert pattern_from_string("2,1,0,0,2") == pattern_from_string("gyxxg")
    assert pattern_from_string("2 1 0 0 2") == pattern_from_string("gyxxg")


def test_all_green_constant() -> None:
    assert pattern_to_string(ALL_GREEN) == "ggggg"


@pytest.mark.parametrize("bad", ["toolong", "", "four"])
def test_feedback_rejects_wrong_length_word(bad: str) -> None:
    with pytest.raises(ValueError):
        feedback("crane", bad)
    with pytest.raises(ValueError):
        feedback(bad, "crane")


@pytest.mark.parametrize("bad", ["gg", "ggggggg", ""])
def test_feedback_string_wrong_length_rejected(bad: str) -> None:
    with pytest.raises(ValueError):
        pattern_from_string(bad)


def test_invalid_feedback_characters_rejected() -> None:
    with pytest.raises(ValueError):
        pattern_from_string("gyzxg")


def test_pattern_out_of_range_rejected() -> None:
    with pytest.raises(ValueError):
        pattern_to_string(NUM_PATTERNS)
    with pytest.raises(ValueError):
        pattern_to_string(-1)
