"""Benchmark runner and formatter tests (small samples only, never full runs)."""

from __future__ import annotations

import json

import pytest

from wordlesmith.benchmark import (
    compare,
    format_distribution,
    format_markdown,
    format_table,
    run_benchmark,
    to_csv,
    to_json,
)
from wordlesmith.game import FAILED, MAX_TURNS


def test_benchmark_sample_stats_are_coherent() -> None:
    result = run_benchmark("frequency", sample=25, seed=1)
    assert result.num_words == 25
    # Distribution covers every outcome bucket and sums to the sample size.
    assert set(result.distribution) == set(range(1, MAX_TURNS + 1)) | {FAILED}
    assert sum(result.distribution.values()) == 25
    # Reported average matches the distribution mean.
    total = sum(turns * n for turns, n in result.distribution.items())
    assert abs(result.average - total / 25) < 1e-9
    assert result.fails == result.distribution[FAILED]


def test_benchmark_is_reproducible() -> None:
    a = run_benchmark("entropy", sample=15, seed=7)
    b = run_benchmark("entropy", sample=15, seed=7)
    assert a.average == b.average
    assert a.distribution == b.distribution


def test_custom_answer_list() -> None:
    words = ("crane", "slate", "trace", "grace", "brace", "place")
    result = run_benchmark("frequency", answers=words, allowed_guesses=words)
    assert result.num_words == len(words)


def test_curated_benchmark_uses_curated_pool() -> None:
    result = run_benchmark("frequency", curated=True, sample=10, seed=1)
    assert result.num_words == 10


def test_curated_parallel_matches_serial() -> None:
    # curated must parallelize (it's a packaged list), unlike custom --answers.
    serial = run_benchmark("frequency", curated=True, sample=30, seed=3, jobs=1)
    parallel = run_benchmark("frequency", curated=True, sample=30, seed=3, jobs=2)
    assert serial.average == parallel.average
    assert serial.distribution == parallel.distribution


def test_compare_returns_one_result_per_strategy() -> None:
    results = compare(["frequency", "random"], sample=10, seed=2)
    assert [r.strategy for r in results] == ["frequency", "random"]


def test_markdown_table_shape() -> None:
    results = compare(["frequency", "random"], sample=10, seed=2)
    md = format_markdown(results)
    lines = md.splitlines()
    assert lines[0].startswith("| strategy |")
    assert set(lines[1].replace(" ", "")) <= {"|", "-"}
    assert len(lines) == 2 + len(results)


def test_ascii_table_and_histogram_render() -> None:
    result = run_benchmark("frequency", sample=10, seed=2)
    table = format_table([result])
    assert "strategy" in table and "frequency" in table
    hist = format_distribution(result)
    assert hist.splitlines()[0].startswith("1:")
    assert "unsolved" in hist


def test_parallel_matches_serial() -> None:
    serial = run_benchmark("frequency", sample=40, seed=3, jobs=1)
    parallel = run_benchmark("frequency", sample=40, seed=3, jobs=2)
    assert serial.average == parallel.average
    assert serial.distribution == parallel.distribution


def test_plot_distributions(tmp_path) -> None:
    pytest.importorskip("matplotlib")  # plotting is behind the optional 'bench' extra
    results = compare(["frequency", "random"], sample=10, seed=2)
    from wordlesmith.benchmark import plot_distributions

    out = tmp_path / "dist.png"
    plot_distributions(results, str(out))
    assert out.exists() and out.stat().st_size > 0


def test_csv_and_json_output(tmp_path) -> None:
    results = compare(["frequency", "random"], sample=10, seed=2)
    csv_path = tmp_path / "out.csv"
    json_path = tmp_path / "out.json"
    to_csv(results, str(csv_path))
    to_json(results, str(json_path))

    csv_lines = csv_path.read_text().splitlines()
    assert csv_lines[0].startswith("strategy,guess_pool,num_words")
    assert len(csv_lines) == 1 + len(results)

    data = json.loads(json_path.read_text())
    assert len(data) == 2
    assert {d["strategy"] for d in data} == {"frequency", "random"}
