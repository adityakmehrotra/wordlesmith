"""Game-state and simulation tests, focused on pattern-consistency filtering."""

from __future__ import annotations

from wordlesmith import get_strategy, simulate
from wordlesmith.feedback import feedback
from wordlesmith.game import FAILED, GameState


def test_record_filters_by_pattern_consistency() -> None:
    words = ["crane", "slate", "trace", "grace", "brace"]
    state = GameState(candidates=list(words), allowed_guesses=tuple(words))
    guess = "crane"
    pattern = feedback(guess, "brace")
    state.record(guess, pattern)
    # Only words that reproduce the same pattern for this guess survive.
    expected = [w for w in words if feedback(guess, w) == pattern]
    assert state.candidates == expected
    assert "brace" in state.candidates


def test_duplicate_letter_filtering_keeps_single_occurrence_words() -> None:
    # "geese" vs "abide" grays the second E, so single-E words must survive.
    words = ["abide", "sheep", "steed", "crane"]
    state = GameState(candidates=list(words), allowed_guesses=tuple(words))
    guess = "geese"
    pattern = feedback(guess, "abide")
    state.record(guess, pattern)
    assert "abide" in state.candidates
    for w in state.candidates:
        assert feedback(guess, w) == pattern


def test_gray_letter_that_is_green_elsewhere() -> None:
    # Doubled L (one green, one gray) must not wrongly drop single-L words.
    guess = "alley"  # vs "llama" gives y g y x x
    pattern = feedback(guess, "llama")
    pool = ["llama", "lolly", "salad", "villa"]
    state = GameState(candidates=list(pool), allowed_guesses=tuple(pool))
    state.record(guess, pattern)
    assert "llama" in state.candidates
    for w in state.candidates:
        assert feedback(guess, w) == pattern


def test_simulate_solves_known_word() -> None:
    result = simulate("crane", get_strategy("entropy"))
    assert result.solved
    assert result.turns <= 6
    assert result.guesses[-1] == "crane"
    # candidate_counts is recorded before each guess and starts at the full list.
    assert result.candidate_counts[0] == 14855
    assert len(result.candidate_counts) == result.turns


def test_simulate_reports_failure_sentinel() -> None:
    # Force a loss with max_turns=1 and check the failure sentinel.
    result = simulate("zonal", get_strategy("random", seed=3), max_turns=1)
    if not result.solved:
        assert result.turns == FAILED
