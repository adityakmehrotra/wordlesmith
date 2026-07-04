# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-03

First packaged release. Rewrites the original exploratory notebook into an
installable, tested Python package with a CLI and a strategy-comparison
benchmark suite.

### Added
- `wordlesmith` package with a zero-dependency core (pure standard library).
- Exact Wordle feedback scoring with correct duplicate-letter handling, encoded
  as base-3 patterns (`feedback`, `pattern_to_string`, `pattern_from_string`).
- `GameState` / `simulate` engine that filters candidates purely by
  pattern-consistency.
- Five strategies behind a common interface: `frequency` (the original
  positional-frequency baseline), `entropy`, `expected-size`, `minimax`, and a
  `random` control. Scoring strategies support both `answers` and `all` guess
  pools.
- Packaged word lists: the full 14,855-word valid-guess list (the default
  answer and guess pool) and the original 2,315-word curated answer set, plus a
  precomputed opening-guess table for fast first moves.
- `--curated` flag (and `load_curated_answers`) to run against the original
  2,315-word solution set instead of the full valid list.
- `wordlesmith` CLI with `play`, `solve`, `benchmark`, and `compare`
  subcommands (argparse, standard library only).
- Benchmark runner with average/median/max/fail metrics, guess-distribution
  histograms, and CSV/JSON/Markdown output; optional plots via the `bench`
  extra.
- Test suite (pytest) covering duplicate-letter scoring edge cases,
  pattern-consistency filtering, strategy selection, and the CLI.
- GitHub Actions CI (lint, type-check, test matrix on Python 3.10-3.13, build)
  and a tag-triggered PyPI release workflow using trusted publishing.

### Changed
- The engine no longer tracks greens/yellows/grays with ad-hoc bookkeeping. The
  pattern-consistency filter fixes latent duplicate-letter bugs in the original
  notebook, which slightly improves the frequency baseline (about 3.64 vs the
  previously reported 3.67 average).
- The solver now considers every valid word a possible answer by default,
  instead of only the original 2,315 solutions. The NYT has revised the answer
  set over time (for example MAVEN, a real answer, is not in the original list),
  so the old default could dead-end on a legitimate puzzle. The full-valid pool
  never does, at the cost of a somewhat higher average; the classic numbers are
  still available with `--curated`.
