"""Running strategies over the answer list and reporting the results."""

from __future__ import annotations

import csv
import json
import random
import statistics
import time
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass, field

from . import __version__
from .game import FAILED, MAX_TURNS
from .game import simulate as _simulate
from .strategies import get_strategy
from .words import load_curated_answers, load_valid_words


@dataclass
class BenchmarkResult:
    strategy: str
    guess_pool: str
    num_words: int
    average: float
    median: float
    maximum: int
    fails: int
    distribution: dict[int, int]  # turns (1..6, 7 == fail) -> count
    wall_seconds: float
    seed: int
    package_version: str = __version__
    per_word: list[tuple[str, int]] = field(default_factory=list)

    @property
    def fail_pct(self) -> float:
        return 100.0 * self.fails / self.num_words if self.num_words else 0.0


def _play_one(args: tuple[str, str, str, int, bool]) -> int:
    target, strategy_name, guess_pool, seed, curated = args
    strategy = get_strategy(strategy_name, guess_pool=guess_pool, seed=seed)
    answers = load_curated_answers() if curated else None
    return _simulate(target, strategy, answers=answers).turns


def run_benchmark(
    strategy: str,
    guess_pool: str = "answers",
    sample: int | None = None,
    seed: int = 0,
    jobs: int = 1,
    per_word: bool = False,
    curated: bool = False,
    answers: Sequence[str] | None = None,
    allowed_guesses: Sequence[str] | None = None,
) -> BenchmarkResult:
    """Benchmark a strategy over the valid-word list, or a random sample of it.

    ``curated=True`` restricts the answer pool to the original 2,315 solutions.
    The default and curated pools both parallelize with ``jobs``; only custom
    ``answers`` / ``allowed_guesses`` force single-process, since the parallel
    workers reload a packaged list rather than receiving these.
    """
    custom_lists = answers is not None or allowed_guesses is not None
    pool_words = answers if answers is not None else (load_curated_answers() if curated else None)
    answer_list = list(pool_words) if pool_words is not None else list(load_valid_words())
    targets = random.Random(seed).sample(answer_list, sample) if sample else answer_list

    t0 = time.perf_counter()
    # random must stay single-process to keep its seeded sequence reproducible.
    if strategy == "random" or jobs <= 1 or custom_lists:
        strat = get_strategy(strategy, guess_pool=guess_pool, seed=seed)
        turns = [
            _simulate(t, strat, answers=pool_words, allowed_guesses=allowed_guesses).turns
            for t in targets
        ]
    else:
        payload = [(t, strategy, guess_pool, seed, curated) for t in targets]
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            turns = list(pool.map(_play_one, payload, chunksize=32))
    wall = time.perf_counter() - t0

    distribution = dict.fromkeys(range(1, MAX_TURNS + 1), 0)
    distribution[FAILED] = 0
    for t in turns:
        distribution[t] += 1

    return BenchmarkResult(
        strategy=strategy,
        guess_pool=guess_pool,
        num_words=len(targets),
        average=statistics.fmean(turns),
        median=statistics.median(turns),
        maximum=max(turns),
        fails=distribution[FAILED],
        distribution=distribution,
        wall_seconds=wall,
        seed=seed,
        per_word=list(zip(targets, turns, strict=True)) if per_word else [],
    )


def compare(
    strategies: list[str],
    guess_pool: str = "answers",
    sample: int | None = None,
    seed: int = 0,
    jobs: int = 1,
    curated: bool = False,
    answers: Sequence[str] | None = None,
    allowed_guesses: Sequence[str] | None = None,
) -> list[BenchmarkResult]:
    """Benchmark several strategies under identical settings."""
    return [
        run_benchmark(
            s,
            guess_pool=guess_pool,
            sample=sample,
            seed=seed,
            jobs=jobs,
            curated=curated,
            answers=answers,
            allowed_guesses=allowed_guesses,
        )
        for s in strategies
    ]


_HEADERS = ("strategy", "pool", "avg", "median", "max", "fail%", "time(s)")


def _rows(results: list[BenchmarkResult]) -> list[tuple[str, ...]]:
    return [
        (
            r.strategy,
            r.guess_pool,
            f"{r.average:.3f}",
            f"{r.median:.1f}",
            str(r.maximum) if r.maximum <= MAX_TURNS else f">{MAX_TURNS}",
            f"{r.fail_pct:.2f}",
            f"{r.wall_seconds:.1f}",
        )
        for r in results
    ]


def format_table(results: list[BenchmarkResult]) -> str:
    """Aligned plain-text table."""
    rows = [_HEADERS, *_rows(results)]
    widths = [max(len(row[i]) for row in rows) for i in range(len(_HEADERS))]
    lines = ["  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)) for row in rows]
    return "\n".join(lines)


def format_markdown(results: list[BenchmarkResult]) -> str:
    """Markdown table, ready to paste into a README."""
    rows = _rows(results)
    head = "| " + " | ".join(_HEADERS) + " |"
    sep = "| " + " | ".join("---" for _ in _HEADERS) + " |"
    body = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([head, sep, *body])


def format_distribution(result: BenchmarkResult, width: int = 40) -> str:
    """ASCII histogram of the guess distribution for a single result."""
    dist = result.distribution
    peak = max(dist.values()) or 1
    lines = []
    for turns in range(1, MAX_TURNS + 1):
        n = dist[turns]
        bar = "#" * round(width * n / peak)
        lines.append(f"{turns}: {bar} {n}")
    fail = dist[FAILED]
    lines.append(f"X: {'#' * round(width * fail / peak)} {fail}  (unsolved)")
    return "\n".join(lines)


def to_csv(results: list[BenchmarkResult], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["strategy", "guess_pool", "num_words", "average", "median", "max", "fails", "fail_pct"]
            + [f"turns_{n}" for n in range(1, MAX_TURNS + 1)]
            + ["turns_fail", "wall_seconds", "seed", "package_version"]
        )
        for r in results:
            writer.writerow(
                [
                    r.strategy,
                    r.guess_pool,
                    r.num_words,
                    f"{r.average:.4f}",
                    r.median,
                    r.maximum,
                    r.fails,
                    f"{r.fail_pct:.4f}",
                ]
                + [r.distribution[n] for n in range(1, MAX_TURNS + 1)]
                + [r.distribution[FAILED], f"{r.wall_seconds:.2f}", r.seed, r.package_version]
            )


def to_json(results: list[BenchmarkResult], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in results], f, indent=2)


def plot_distributions(results: list[BenchmarkResult], path: str) -> None:
    """Save a grouped bar chart of guess distributions (requires the ``bench`` extra)."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - exercised only without matplotlib
        raise RuntimeError(
            "plotting requires the 'bench' extra: pip install wordlesmith[bench]"
        ) from exc

    turns = list(range(1, MAX_TURNS + 1)) + [FAILED]
    labels = [str(t) for t in range(1, MAX_TURNS + 1)] + ["X"]
    n = len(results)
    bar_w = 0.8 / n
    fig, ax = plt.subplots(figsize=(9, 5))
    for i, r in enumerate(results):
        offsets = [x + i * bar_w for x in range(len(turns))]
        ax.bar(
            offsets,
            [r.distribution[t] for t in turns],
            width=bar_w,
            label=f"{r.strategy} ({r.average:.2f})",
        )
    ax.set_xticks([x + bar_w * (n - 1) / 2 for x in range(len(turns))])
    ax.set_xticklabels(labels)
    ax.set_xlabel("guesses to solve (X = unsolved)")
    ax.set_ylabel("number of answers")
    ax.set_title("Wordle guess distribution by strategy")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
