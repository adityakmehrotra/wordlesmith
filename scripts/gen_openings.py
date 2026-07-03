"""Regenerate src/wordlesmith/data/openings.json.

Computes the answers-pool opening for each scoring strategy over both default
pools (valid words and curated answers) and ships them, so interactive solves
and benchmark workers skip the expensive first guess. Keys are
"<strategy>|answers|<poolset>". Parallel and resumable: re-running fills in only
the missing keys.
"""

from __future__ import annotations

import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from wordlesmith.game import GameState
from wordlesmith.strategies import get_strategy
from wordlesmith.strategies.base import pattern_counts
from wordlesmith.words import load_curated_answers, load_valid_words

OUT = Path(__file__).resolve().parent.parent / "src" / "wordlesmith" / "data" / "openings.json"
POOLS = {"valid": load_valid_words, "curated": load_curated_answers}
SCORING = ["entropy", "expected-size", "minimax"]
JOBS = 9


def _chunk_best(args: tuple[int, int, str, str]) -> tuple[float, str]:
    lo, hi, name, poolset = args
    cands = list(POOLS[poolset]())
    strat = get_strategy(name)
    maximize = strat.maximize  # type: ignore[attr-defined]
    best: tuple[float, str] | None = None
    for g in cands[lo:hi]:
        s = strat.score(pattern_counts(g, cands))  # type: ignore[attr-defined]
        if (
            best is None
            or (s > best[0] if maximize else s < best[0])
            or (s == best[0] and g < best[1])
        ):
            best = (s, g)
    assert best is not None
    return best


def _opening_scored(name: str, poolset: str) -> str:
    cands = list(POOLS[poolset]())
    n = len(cands)
    step = (n + JOBS - 1) // JOBS
    chunks = [(i, min(i + step, n), name, poolset) for i in range(0, n, step)]
    with ProcessPoolExecutor(max_workers=JOBS) as ex:
        results = list(ex.map(_chunk_best, chunks))
    maximize = get_strategy(name).maximize  # type: ignore[attr-defined]
    best: tuple[float, str] | None = None
    for s, g in results:
        if (
            best is None
            or (s > best[0] if maximize else s < best[0])
            or (s == best[0] and g < best[1])
        ):
            best = (s, g)
    assert best is not None
    return best[1]


def _opening_frequency(poolset: str) -> str:
    cands = list(POOLS[poolset]())
    state = GameState(candidates=cands, allowed_guesses=tuple(cands))
    return get_strategy("frequency").choose(state)


def main() -> None:
    openings: dict[str, str] = json.loads(OUT.read_text()) if OUT.exists() else {}

    def save() -> None:
        OUT.write_text(json.dumps(openings, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    for poolset in POOLS:
        for name in ["frequency", *SCORING]:
            key = f"{name}|answers|{poolset}"
            if key in openings:
                print(f"skip {key} ({openings[key]})", flush=True)
                continue
            word = (
                _opening_frequency(poolset)
                if name == "frequency"
                else _opening_scored(name, poolset)
            )
            openings[key] = word
            save()
            print(f"{key}: {word}", flush=True)
    print(f"wrote {OUT} ({len(openings)} openings)", flush=True)


if __name__ == "__main__":
    main()
