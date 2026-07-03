"""Strategy interface and the shared machinery for the scoring strategies."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections import Counter
from functools import lru_cache
from importlib import resources
from typing import ClassVar

from ..feedback import feedback
from ..game import GameState
from ..words import load_curated_answers, load_valid_words

GuessPool = str  # "answers" | "all"
VALID_POOLS = ("answers", "all")


def validate_pool(guess_pool: GuessPool) -> GuessPool:
    if guess_pool not in VALID_POOLS:
        raise ValueError(f"guess_pool must be one of {VALID_POOLS}: {guess_pool!r}")
    return guess_pool


# Openings only depend on the candidate set, so cache them. The full-pool
# opening is the most expensive thing we compute, so this matters.
_OPENING_CACHE: dict[tuple[str, str, int], str] = {}


@lru_cache(maxsize=1)
def _shipped_openings() -> dict[str, str]:
    """Precomputed openings keyed by "<strategy>|<pool>" (empty if the file is missing)."""
    try:
        text = resources.files("wordlesmith.data").joinpath("openings.json").read_text("utf-8")
    except (FileNotFoundError, ModuleNotFoundError):
        return {}
    return dict(json.loads(text))


@lru_cache(maxsize=1)
def _default_pools() -> dict[str, tuple[str, ...]]:
    # Named default candidate sets, so a shipped opening can be matched to
    # whichever pool the game started from.
    return {"valid": load_valid_words(), "curated": load_curated_answers()}


class Strategy(ABC):
    name: ClassVar[str]

    @abstractmethod
    def choose(self, state: GameState) -> str:
        """Return the next guess (lowercase, length 5)."""


def _pool(state: GameState, guess_pool: GuessPool) -> list[str] | tuple[str, ...]:
    if guess_pool == "answers":
        return state.candidates
    if guess_pool == "all":
        return state.allowed_guesses
    raise ValueError(f"guess_pool must be one of {VALID_POOLS}: {guess_pool!r}")


def pattern_counts(guess: str, candidates: list[str]) -> Counter[int]:
    """Group candidates by the feedback pattern guess would produce."""
    counts: Counter[int] = Counter()
    for target in candidates:
        counts[feedback(guess, target)] += 1
    return counts


class ScoringStrategy(Strategy):
    """Score every candidate guess and pick the best; subclasses supply score()."""

    maximize: ClassVar[bool]

    def __init__(self, guess_pool: GuessPool = "answers") -> None:
        self.guess_pool = validate_pool(guess_pool)

    @abstractmethod
    def score(self, counts: Counter[int]) -> float: ...

    def choose(self, state: GameState) -> str:
        candidates = state.candidates
        if len(candidates) <= 2:
            return candidates[0]

        if not state.history:
            cand = tuple(candidates)
            openings = _shipped_openings()
            for pool_name, words in _default_pools().items():
                if cand == words:
                    shipped = openings.get(f"{self.name}|{self.guess_pool}|{pool_name}")
                    if shipped is not None:
                        return shipped
                    break
            key = (self.name, self.guess_pool, hash(cand))
            if key not in _OPENING_CACHE:
                _OPENING_CACHE[key] = self._best_guess(state)
            return _OPENING_CACHE[key]

        return self._best_guess(state)

    def _best_guess(self, state: GameState) -> str:
        candidates = state.candidates
        candidate_set = set(candidates)
        best_guess: str | None = None
        best_score = float("-inf") if self.maximize else float("inf")
        best_is_answer = False

        # The pool is sorted, so keeping the first winner on ties gives us
        # alphabetical order; we only override a tie to prefer an answer word.
        for guess in _pool(state, self.guess_pool):
            score = self.score(pattern_counts(guess, candidates))
            if best_guess is None:
                better = True
            elif score == best_score:
                better = (guess in candidate_set) and not best_is_answer
            else:
                better = score > best_score if self.maximize else score < best_score

            if better:
                best_guess = guess
                best_score = score
                best_is_answer = guess in candidate_set

        assert best_guess is not None
        return best_guess
