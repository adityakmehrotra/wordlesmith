"""Expected-size strategy: minimize the candidates left after a guess."""

from __future__ import annotations

from collections import Counter
from typing import ClassVar

from .base import ScoringStrategy


class ExpectedSizeStrategy(ScoringStrategy):
    """Minimize the expected remaining candidate count, sum(bucket**2) / total."""

    name = "expected-size"
    maximize: ClassVar[bool] = False

    def score(self, counts: Counter[int]) -> float:
        total = sum(counts.values())
        return sum(bucket * bucket for bucket in counts.values()) / total
