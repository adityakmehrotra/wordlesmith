"""Minimax strategy: minimize the worst-case bucket (Knuth's Mastermind idea)."""

from __future__ import annotations

from collections import Counter
from typing import ClassVar

from .base import ScoringStrategy


class MinimaxStrategy(ScoringStrategy):
    """Minimize the largest feedback bucket, i.e. the worst-case survivors."""

    name = "minimax"
    maximize: ClassVar[bool] = False

    def score(self, counts: Counter[int]) -> float:
        return float(max(counts.values()))
