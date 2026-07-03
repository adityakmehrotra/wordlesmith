"""Random strategy: a consistent-guess control to benchmark against."""

from __future__ import annotations

import random

from ..game import GameState
from .base import Strategy


class RandomStrategy(Strategy):
    """Guess a random word from the remaining candidates; seeded for reproducibility."""

    name = "random"

    def __init__(self, seed: int | None = 0) -> None:
        self._rng = random.Random(seed)

    def choose(self, state: GameState) -> str:
        return self._rng.choice(state.candidates)
