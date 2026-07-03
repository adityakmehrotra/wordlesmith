"""Strategy registry: look strategies up by name."""

from __future__ import annotations

from .base import VALID_POOLS, GuessPool, ScoringStrategy, Strategy
from .entropy import EntropyStrategy
from .expected_size import ExpectedSizeStrategy
from .frequency import FrequencyStrategy
from .minimax import MinimaxStrategy
from .random_guess import RandomStrategy

_REGISTRY: dict[str, type[Strategy]] = {
    FrequencyStrategy.name: FrequencyStrategy,
    EntropyStrategy.name: EntropyStrategy,
    ExpectedSizeStrategy.name: ExpectedSizeStrategy,
    MinimaxStrategy.name: MinimaxStrategy,
    RandomStrategy.name: RandomStrategy,
}


def available_strategies() -> list[str]:
    """The registered strategy names."""
    return list(_REGISTRY)


def get_strategy(
    name: str,
    guess_pool: GuessPool = "answers",
    seed: int | None = 0,
) -> Strategy:
    """Build a strategy by name. guess_pool applies to all but random; seed only to random."""
    try:
        cls = _REGISTRY[name]
    except KeyError:
        raise ValueError(f"unknown strategy {name!r}; choose from {sorted(_REGISTRY)}") from None

    if cls is RandomStrategy:
        return RandomStrategy(seed=seed)
    return cls(guess_pool=guess_pool)  # type: ignore[call-arg]


__all__ = [
    "VALID_POOLS",
    "GuessPool",
    "ScoringStrategy",
    "Strategy",
    "available_strategies",
    "get_strategy",
]
