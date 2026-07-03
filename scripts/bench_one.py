"""Compute one (strategy, pool) benchmark result and checkpoint it to disk.

Usage: python scripts/bench_one.py <strategy> <answers|all>

Saves benchmarks/results/official/raw/<strategy>_<pool>.json immediately, so a
long comparison can be built up incrementally and resumed if interrupted.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

from wordlesmith.benchmark import run_benchmark

JOBS = 10
RAW = Path(__file__).resolve().parent.parent / "benchmarks" / "results" / "official" / "raw"


def main() -> None:
    strategy, pool = sys.argv[1], sys.argv[2]
    RAW.mkdir(parents=True, exist_ok=True)
    out = RAW / f"{strategy}_{pool}.json"
    if out.exists():
        print(f"skip {strategy}|{pool} (already done)", flush=True)
        return
    result = run_benchmark(strategy, guess_pool=pool, jobs=JOBS, per_word=True)
    out.write_text(json.dumps(asdict(result), indent=2), encoding="utf-8")
    print(
        f"{strategy}|{pool}: avg={result.average:.4f} max={result.maximum} "
        f"fail={result.fail_pct:.2f}% ({result.wall_seconds:.0f}s) -> {out.name}",
        flush=True,
    )


if __name__ == "__main__":
    main()
