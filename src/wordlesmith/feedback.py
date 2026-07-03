"""Wordle feedback scoring.

Patterns are encoded as a base-3 int in [0, 242]: one trit per position
(0=gray, 1=yellow, 2=green), position 0 is the least significant.
"""

from __future__ import annotations

from collections import Counter

WORD_LEN = 5
GRAY = 0
YELLOW = 1
GREEN = 2
NUM_PATTERNS = 3**WORD_LEN

_CHAR_TO_TRIT = {"x": GRAY, "y": YELLOW, "g": GREEN}
_TRIT_TO_CHAR = {GRAY: "x", YELLOW: "y", GREEN: "g"}


def feedback(guess: str, target: str) -> int:
    """Score guess against target, returning the encoded pattern."""
    guess = guess.lower()
    target = target.lower()
    if len(guess) != WORD_LEN or len(target) != WORD_LEN:
        raise ValueError(f"words must be {WORD_LEN} letters: {guess!r}, {target!r}")

    trits = [GRAY] * WORD_LEN
    remaining = Counter(target)

    # Greens claim their letter first, so a doubled guess letter only goes
    # yellow if the target still has one to spare (e.g. SPEED vs ABIDE).
    for i in range(WORD_LEN):
        if guess[i] == target[i]:
            trits[i] = GREEN
            remaining[guess[i]] -= 1

    for i in range(WORD_LEN):
        if trits[i] != GREEN and remaining[guess[i]] > 0:
            trits[i] = YELLOW
            remaining[guess[i]] -= 1

    code = 0
    for i in range(WORD_LEN - 1, -1, -1):
        code = code * 3 + trits[i]
    return code


def pattern_to_string(code: int) -> str:
    """Render an encoded pattern as a g/y/x string (position 0 first)."""
    if not 0 <= code < NUM_PATTERNS:
        raise ValueError(f"pattern out of range [0, {NUM_PATTERNS}): {code}")
    chars = []
    for _ in range(WORD_LEN):
        chars.append(_TRIT_TO_CHAR[code % 3])
        code //= 3
    return "".join(chars)


def pattern_from_string(text: str) -> int:
    """Parse a feedback string into an encoded pattern.

    Accepts g/y/x or the legacy 2/1/0 form, comma- or space-separated
    (e.g. "gyxxg" or "2,1,0,0,2").
    """
    text = text.strip().lower()
    if any(sep in text for sep in (",", " ")):
        parts = [p for p in text.replace(",", " ").split() if p]
        trit_seq = [int(p) for p in parts]
    else:
        try:
            trit_seq = [_CHAR_TO_TRIT[c] for c in text]
        except KeyError as exc:
            raise ValueError(f"invalid feedback character in {text!r}") from exc

    if len(trit_seq) != WORD_LEN:
        raise ValueError(f"feedback must have {WORD_LEN} entries: {text!r}")
    if any(t not in (GRAY, YELLOW, GREEN) for t in trit_seq):
        raise ValueError(f"feedback entries must be 0/1/2 (x/y/g): {text!r}")

    code = 0
    for t in reversed(trit_seq):
        code = code * 3 + t
    return code


ALL_GREEN = pattern_from_string("ggggg")
