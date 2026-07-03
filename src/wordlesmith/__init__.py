"""wordlesmith: a Wordle solver with pluggable strategies."""

from __future__ import annotations

from .feedback import (
    ALL_GREEN,
    GRAY,
    GREEN,
    NUM_PATTERNS,
    WORD_LEN,
    YELLOW,
    feedback,
    pattern_from_string,
    pattern_to_string,
)
from .game import GameResult, GameState, simulate
from .strategies import available_strategies, get_strategy
from .words import load_curated_answers, load_valid_words, load_words

__version__ = "0.1.0"

__all__ = [
    "ALL_GREEN",
    "GRAY",
    "GREEN",
    "NUM_PATTERNS",
    "WORD_LEN",
    "YELLOW",
    "GameResult",
    "GameState",
    "__version__",
    "available_strategies",
    "feedback",
    "get_strategy",
    "load_curated_answers",
    "load_valid_words",
    "load_words",
    "pattern_from_string",
    "pattern_to_string",
    "simulate",
]
