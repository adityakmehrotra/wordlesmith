"""Assemble the primary committed benchmark: every strategy over the full
valid-word list (answers pool), which is wordlesmith's default.

Each result is checkpointed under benchmarks/results/official/raw/ (see
bench_one.py) and combined here into the primary tables, per-word CSV, and plot.
The curated 2,315-answer results are produced separately and kept as the
labeled secondary. Resumable: re-running skips finished results.

    python scripts/run_official_benchmark.py
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path

from wordlesmith import __version__
from wordlesmith.benchmark import (
    BenchmarkResult,
    format_markdown,
    format_table,
    plot_distributions,
    run_benchmark,
    to_csv,
    to_json,
)
from wordlesmith.words import load_valid_words

JOBS = 9
OUT = Path(__file__).resolve().parent.parent / "benchmarks" / "results" / "official"
RAW = OUT / "raw"
ORDER = ["random", "frequency", "expected-size", "minimax", "entropy"]


def _load(path: Path) -> BenchmarkResult:
    d = json.loads(path.read_text(encoding="utf-8"))
    d["distribution"] = {int(k): v for k, v in d["distribution"].items()}
    d["per_word"] = [tuple(x) for x in d["per_word"]]
    return BenchmarkResult(**d)


def _get(strategy: str) -> BenchmarkResult:
    path = RAW / f"{strategy}_answers.json"
    if path.exists():
        return _load(path)
    result = run_benchmark(strategy, guess_pool="answers", jobs=JOBS, per_word=True)
    RAW.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(result), indent=2), encoding="utf-8")
    return result


def _write_per_word(results: list[BenchmarkResult], path: Path) -> None:
    words = [w for w, _ in results[0].per_word]
    turns = {r.strategy: dict(r.per_word) for r in results}
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["word", *turns])
        for w in words:
            writer.writerow([w, *(turns[s][w] for s in turns)])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    results = [_get(s) for s in ORDER]

    to_csv(results, str(OUT / "primary_valid.csv"))
    to_json(results, str(OUT / "primary_valid.json"))
    (OUT / "primary_valid.md").write_text(format_markdown(results) + "\n", encoding="utf-8")
    _write_per_word(results, OUT / "per_word_valid.csv")
    plot_distributions(results, str(OUT / "distribution_valid.png"))
    (OUT / "meta.txt").write_text(
        f"package_version={__version__}\njobs={JOBS}\n"
        f"valid_words={len(load_valid_words())}\ncurated_words=2315\n",
        encoding="utf-8",
    )

    print("=== PRIMARY: full valid list, answers pool ===")
    print(format_table(results))
    print(f"\nwrote artifacts to {OUT}")


if __name__ == "__main__":
    main()
