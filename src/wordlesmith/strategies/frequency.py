"""Frequency strategy: the project's original positional-letter-count baseline."""

from __future__ import annotations

from collections import Counter

from ..game import GameState
from .base import GuessPool, Strategy, _pool, validate_pool


class FrequencyStrategy(Strategy):
    name = "frequency"

    def __init__(self, guess_pool: GuessPool = "answers") -> None:
        self.guess_pool = validate_pool(guess_pool)

    def choose(self, state: GameState) -> str:
        candidates = state.candidates
        if len(candidates) <= 2:
            return candidates[0]

        position_counts = [Counter(word[i] for word in candidates) for i in range(5)]
        candidate_set = set(candidates)

        best_guess: str | None = None
        best_score = -1
        best_is_answer = False
        for guess in _pool(state, self.guess_pool):
            score = sum(position_counts[i][guess[i]] for i in range(5))
            if best_guess is None or score > best_score:
                better = True
            elif score == best_score:
                better = (guess in candidate_set) and not best_is_answer
            else:
                better = False
            if better:
                best_guess = guess
                best_score = score
                best_is_answer = guess in candidate_set

        assert best_guess is not None
        return best_guess
