"""Loading the packaged word lists (and custom ones).

By default wordlesmith treats every valid Wordle guess as a possible answer, so
it can solve any real puzzle regardless of the curated solution set. The
original 2,315-word answer list is kept as ``curated_answers`` for the secondary
benchmark and the ``--curated`` mode.
"""

from __future__ import annotations

from functools import cache
from importlib import resources
from pathlib import Path

from .feedback import WORD_LEN

_DATA_PACKAGE = "wordlesmith.data"


def _parse(text: str) -> list[str]:
    words = []
    for raw in text.splitlines():
        line = raw.strip().lower()
        if not line or line.startswith("#"):
            continue
        if len(line) != WORD_LEN or not line.isalpha():
            raise ValueError(f"invalid word in list: {raw!r}")
        words.append(line)
    return sorted(set(words))


def _load_packaged(filename: str) -> tuple[str, ...]:
    text = resources.files(_DATA_PACKAGE).joinpath(filename).read_text(encoding="utf-8")
    return tuple(_parse(text))


@cache
def load_valid_words() -> tuple[str, ...]:
    """Every valid Wordle word, used as both the answer and guess pool by default."""
    return _load_packaged("valid_words.txt")


@cache
def load_curated_answers() -> tuple[str, ...]:
    """The original 2,315-word Wordle solution set (a subset of the valid words)."""
    return _load_packaged("curated_answers.txt")


def load_words(path: str | Path) -> tuple[str, ...]:
    """Load a custom word list, one word per line."""
    return tuple(_parse(Path(path).read_text(encoding="utf-8")))
