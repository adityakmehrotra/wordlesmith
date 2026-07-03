"""Entropy strategy: maximize expected information."""

from __future__ import annotations

from collections import Counter
from math import log2
from typing import ClassVar

from .base import ScoringStrategy


class EntropyStrategy(ScoringStrategy):
    """Pick the guess whose feedback buckets have the highest Shannon entropy."""

    name = "entropy"
    maximize: ClassVar[bool] = True

    def score(self, counts: Counter[int]) -> float:
        total = sum(counts.values())
        entropy = 0.0
        for bucket in counts.values():
            p = bucket / total
            entropy -= p * log2(p)
        return entropy
