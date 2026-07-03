"""Game state and simulation.

Candidates are filtered by one rule: after seeing (guess, pattern), keep a word
w only if feedback(guess, w) == pattern. That handles duplicate letters for
free, so there's no separate green/yellow/gray bookkeeping.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .feedback import ALL_GREEN, feedback
from .words import load_valid_words

if TYPE_CHECKING:
    from .strategies.base import Strategy

MAX_TURNS = 6
FAILED = MAX_TURNS + 1  # "turns taken" for a game we didn't solve in six


@dataclass
class GameState:
    """A single game in progress: the words still possible and what's been guessed."""

    candidates: list[str]
    allowed_guesses: tuple[str, ...]
    history: list[tuple[str, int]] = field(default_factory=list)

    @classmethod
    def new(
        cls,
        answers: Sequence[str] | None = None,
        allowed_guesses: Sequence[str] | None = None,
    ) -> GameState:
        """Start a fresh game. Defaults both pools to the full valid-word list."""
        ans = list(answers) if answers is not None else list(load_valid_words())
        allowed = tuple(allowed_guesses) if allowed_guesses is not None else load_valid_words()
        return cls(candidates=ans, allowed_guesses=allowed)

    @property
    def turn(self) -> int:
        return len(self.history) + 1

    @property
    def solved(self) -> bool:
        return bool(self.history) and self.history[-1][1] == ALL_GREEN

    def record(self, guess: str, pattern: int) -> None:
        """Log a guess and its result, then drop candidates that don't match."""
        guess = guess.lower()
        self.history.append((guess, pattern))
        self.candidates = [w for w in self.candidates if feedback(guess, w) == pattern]


@dataclass
class GameResult:
    target: str
    turns: int  # 1..6 if solved, FAILED (7) otherwise
    guesses: list[str]
    candidate_counts: list[int]  # candidates left before each guess

    @property
    def solved(self) -> bool:
        return self.turns <= MAX_TURNS


def simulate(
    target: str,
    strategy: Strategy,
    answers: Sequence[str] | None = None,
    allowed_guesses: Sequence[str] | None = None,
    max_turns: int = MAX_TURNS,
) -> GameResult:
    """Auto-play a full game of target with the given strategy."""
    target = target.lower()
    state = GameState.new(answers=answers, allowed_guesses=allowed_guesses)
    guesses: list[str] = []
    counts: list[int] = []

    for turn in range(1, max_turns + 1):
        counts.append(len(state.candidates))
        guess = strategy.choose(state)
        guesses.append(guess)
        pattern = feedback(guess, target)
        state.record(guess, pattern)
        if pattern == ALL_GREEN:
            return GameResult(target, turn, guesses, counts)

    return GameResult(target, FAILED, guesses, counts)
