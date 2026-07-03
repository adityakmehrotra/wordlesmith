"""Strategy tests: legality, determinism, tie-breaking, and hand-checked picks."""

from __future__ import annotations

from collections import Counter
from math import log2

import pytest

from wordlesmith import available_strategies, get_strategy, simulate
from wordlesmith.feedback import feedback
from wordlesmith.game import GameState
from wordlesmith.strategies import Strategy

ALL = available_strategies()


def _entropy(guess: str, candidates: list[str]) -> float:
    counts = Counter(feedback(guess, t) for t in candidates)
    total = sum(counts.values())
    return -sum((n / total) * log2(n / total) for n in counts.values())


@pytest.mark.parametrize("name", ALL)
def test_returns_legal_guess(name: str) -> None:
    state = GameState.new()
    guess = get_strategy(name).choose(state)
    assert len(guess) == 5
    assert guess in set(state.allowed_guesses)


@pytest.mark.parametrize("name", ALL)
def test_solves_a_game(name: str) -> None:
    result = simulate("vivid", get_strategy(name, seed=1))
    if result.solved:
        assert result.guesses[-1] == "vivid"
    else:
        assert result.turns == 7


@pytest.mark.parametrize("name", [n for n in ALL if n != "random"])
def test_deterministic(name: str) -> None:
    s1, s2 = get_strategy(name), get_strategy(name)
    st1, st2 = GameState.new(), GameState.new()
    assert s1.choose(st1) == s2.choose(st2)


def test_random_reproducible_with_seed() -> None:
    a = simulate("crane", get_strategy("random", seed=42))
    b = simulate("crane", get_strategy("random", seed=42))
    assert a.guesses == b.guesses


def test_two_candidate_shortcut() -> None:
    pool = ("abide", "abode")
    for name in ALL:
        state = GameState(candidates=["abide", "abode"], allowed_guesses=pool)
        # With two candidates all strategies guess a candidate directly.
        assert get_strategy(name).choose(state) in {"abide", "abode"}


def test_entropy_matches_bruteforce_on_small_set() -> None:
    # Sorted, matching the real invariant (candidate lists are always sorted),
    # so the alphabetical tie-break is well defined.
    candidates = sorted(["crane", "slate", "trace", "grace", "brace", "place", "peace"])
    state = GameState(candidates=list(candidates), allowed_guesses=tuple(candidates))
    got = get_strategy("entropy", guess_pool="answers").choose(state)
    # Reference: highest entropy, ties broken alphabetically (all pool words are
    # answers here, so the answer-word tie-break is a no-op).
    top = max(_entropy(g, candidates) for g in candidates)
    tied = sorted(g for g in candidates if _entropy(g, candidates) == top)
    assert got == tied[0]
    assert _entropy(got, candidates) == top


def test_minimax_minimizes_worst_bucket() -> None:
    candidates = sorted(["crane", "slate", "trace", "grace", "brace", "place", "peace"])
    state = GameState(candidates=list(candidates), allowed_guesses=tuple(candidates))
    got = get_strategy("minimax", guess_pool="answers").choose(state)

    def worst(g: str) -> int:
        return max(Counter(feedback(g, t) for t in candidates).values())

    assert worst(got) == min(worst(g) for g in candidates)


def test_tie_break_prefers_answer_word() -> None:
    # Four candidates (so we skip the <=2 shortcut). "zzzzz" partitions them
    # identically to any candidate guess, so the answer-word must win the tie.
    candidates = ["aaabb", "aaacc", "aaadd", "aaaee"]
    allowed = (*candidates, "zzzzz")
    state = GameState(candidates=list(candidates), allowed_guesses=allowed)
    guess = get_strategy("entropy", guess_pool="all").choose(state)
    assert guess in set(candidates)


@pytest.mark.parametrize("name", ["frequency", "entropy", "expected-size", "minimax"])
def test_invalid_guess_pool_rejected(name: str) -> None:
    # Every pool-taking strategy must validate in __init__, not lazily in choose().
    with pytest.raises(ValueError):
        get_strategy(name, guess_pool="nonsense")


def test_unknown_strategy_rejected() -> None:
    with pytest.raises(ValueError):
        get_strategy("bogus")


def test_strategy_is_abstract() -> None:
    with pytest.raises(TypeError):
        Strategy()  # type: ignore[abstract]
