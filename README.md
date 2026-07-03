<a id="readme-top"></a>

<div align="center">

[![CI][ci-shield]][ci-url]
[![Python 3.10+][python-shield]][python-url]
[![MIT License][license-shield]][license-url]

# wordlesmith

A Wordle solver with pluggable strategies and a benchmark suite for comparing them.

Considers every valid word a possible answer, so it never dead-ends on a real puzzle (entropy
averages 4.52 guesses over all 14,855 valid words, and 3.60 on the classic 2,315-answer set). The
core is pure standard library.

<img src="https://raw.githubusercontent.com/adityakmehrotra/wordlesmith/main/docs/demo.gif" alt="wordlesmith playing along with a Wordle" width="760">

</div>

---

## Contents

- [What it does](#what-it-does)
- [Install](#install)
- [Quickstart](#quickstart)
- [Benchmark](#benchmark)
- [How it works](#how-it-works)
- [Strategies](#strategies) ([in-depth](docs/strategies.md))
- [Development](#development)
- [License &amp; contact](#license--contact)

## What it does

`wordlesmith` is a command-line and library Wordle solver. It ships:

- A Wordle scoring engine that handles duplicate letters correctly, which is where most
  solvers have subtle bugs.
- Five strategies behind one interface: positional frequency, entropy, expected remaining
  size, minimax, and a random control.
- A benchmark framework that plays every valid word and reports the full guess distribution.
- The full 14,855-word valid-guess list (the default answer pool, so it never dead-ends on a
  real puzzle) and the original 2,315-word answer set, packaged with a precomputed
  opening-guess table so the first move is instant.

The core has no third-party dependencies. Plotting is the only extra.

## Install

```bash
# From GitHub
pip install "git+https://github.com/adityakmehrotra/wordlesmith"

# For development (tests, lint, plots)
git clone https://github.com/adityakmehrotra/wordlesmith
cd wordlesmith
pip install -e ".[dev,bench]"
```

Requires Python 3.10+.

## Quickstart

### Command line

Auto-solve a known word:

<img src="https://raw.githubusercontent.com/adityakmehrotra/wordlesmith/main/docs/solve.gif" alt="wordlesmith solve maven, then solve crane --curated" width="720">

(`maven` is a real NYT answer that isn't in the original 2,315-word list, so a solver built only
on that list would never find it. The default pool is every valid word, so this just works.)

Play along with a real puzzle: it suggests a guess, you type the colors back
(`g`=green, `y`=yellow, `x`=gray):

```console
$ wordlesmith play --strategy entropy
Turn 1 suggestion: TARES   (14855 candidates)
Enter feedback: xgxgx
Turn 2 suggestion: LADEN   (150 candidates)
Enter feedback: ...
```

Benchmark one strategy, or compare several:

```console
$ wordlesmith benchmark --strategy entropy --sample 300
$ wordlesmith compare --strategies frequency,entropy,minimax --markdown
$ wordlesmith compare --curated --markdown          # the classic 2,315-answer set
```

Run `wordlesmith --help` (or `wordlesmith <command> --help`) for all options,
including `--curated`, `--guess-pool all`, `--jobs` for parallel benchmarks, and
`--answers`/`--allowed` for custom word lists.

### Python API

```python
from wordlesmith import get_strategy, simulate, feedback, pattern_to_string

# Score a guess against a target (base-3 pattern; g/y/x string for humans)
print(pattern_to_string(feedback("speed", "abide")))  # -> xxyxy

# Auto-play a word
result = simulate("maven", get_strategy("entropy"))
print(result.turns, result.guesses)  # -> 3 ['tares', 'laden', 'maven']
```

## Benchmark

Lower average is better; `max` is the worst game; `fail%` is games not solved within six
guesses.

### Primary: every valid word (the default)

Each strategy plays all 14,855 valid words, guessing from the words still consistent with the
feedback. This is how the solver actually runs, so it never dead-ends on a real puzzle:

| strategy | pool | avg | max | fail% |
| --- | --- | --- | --- | --- |
| random | answers | 5.061 | >6 | 16.68 |
| frequency | answers | 4.922 | >6 | 14.57 |
| minimax | answers | 4.658 | >6 | 11.29 |
| expected-size | answers | 4.585 | >6 | 10.57 |
| entropy | answers | 4.523 | >6 | 9.47 |

The averages are higher and the failure rate is non-trivial (about 9% even for entropy) because the
full valid list is packed with near-identical clusters (`match`/`batch`/`catch`/`hatch`/..., the
`-ound` and `-ight` families, plus many obscure words) that simply cannot be separated in six
guesses. Those hard words are almost never real NYT answers, so for actual daily play the curated
number below is the realistic one; this table is the pessimistic "solve literally any valid word"
figure.

![Guess distribution by strategy](https://raw.githubusercontent.com/adityakmehrotra/wordlesmith/main/benchmarks/results/official/distribution_valid.png)

### Secondary: the classic 2,315-answer set (`--curated`)

Restricted to the original Wordle solution set, the problem is easier and the numbers are
comparable to published solvers. The `all` pool (guessing any word for information) gets close
to the known optimum of about 3.421:

| strategy | pool | avg | max | fail% |
| --- | --- | --- | --- | --- |
| random | answers | 4.039 | >6 | 0.82 |
| frequency | answers | 3.640 | >6 | 0.60 |
| expected-size | answers | 3.623 | >6 | 0.60 |
| minimax | answers | 3.677 | >6 | 0.65 |
| entropy | answers | 3.598 | >6 | 0.48 |
| entropy | all | 3.465 | 6 | 0.00 |
| expected-size | all | 3.481 | 5 | 0.00 |
| minimax | all | 3.573 | 6 | 0.00 |

A concrete example of what the smart strategies buy you: solving `mound` on the curated set, the
frequency baseline burns turns cycling through lookalikes (`slate`, `crony`, `bound`, `found`,
`hound`, `mound`) while entropy picks a splitting guess and finishes in three (`raise`, `mulch`,
`mound`).

<sub>Methodology: a game is a failure if unsolved in 6 guesses (counted as 7 in the mean).
Deterministic strategies are reproducible; `random` uses a fixed seed. Full results and per-word
data are in [`benchmarks/results/official/`](https://raw.githubusercontent.com/adityakmehrotra/wordlesmith/main/benchmarks/results/official); regenerate the primary
with `python scripts/run_official_benchmark.py`. The primary `answers`-pool run takes about 10
minutes per strategy on 9 cores; the curated `all`-pool run scores every valid word each turn and
takes far longer, which is why it stays on the smaller curated set. Use `--sample N` for a quick
estimate.</sub>

## How it works

Scoring: Wordle feedback is computed in two passes. Greens are assigned first and each
consumes its letter in the target; yellows are then assigned left to right, each consuming
a remaining occurrence. A guess letter with no occurrence left is gray. This is why the
second `E` in `SPEED` is gray against `ABIDE`, which has only one `E`.

Filtering: after each guess the solver keeps a word `w` only if `feedback(guess, w)`
equals the pattern actually observed. This single rule handles every duplicate-letter case
correctly, so there is no separate (and bug-prone) tracking of which letters are "in" or
"out".

Word lists: by default every valid Wordle word is treated as a possible answer. The original
Wordle solution set was only 2,315 words, but the NYT has revised it over time, so a solver
built on that list can dead-end on a legitimate answer it never considered (`maven`, for
instance). Using the full valid list avoids that, at the cost of a somewhat higher average
since there are more words to tell apart. Pass `--curated` to fall back to the original
2,315-answer set (faster, and the numbers become comparable to published solvers).

## Strategies

| name | idea | good for |
| --- | --- | --- |
| `frequency` | Sum of per-position letter frequencies among candidates (the original baseline). | A strong, cheap heuristic. |
| `entropy` | Maximize expected information (Shannon entropy of the feedback-bucket distribution). | Best average guess count. |
| `expected-size` | Minimize the expected number of remaining candidates. | Simple, nearly as strong as entropy. |
| `minimax` | Minimize the largest feedback bucket (worst case). | Smallest worst case. |
| `random` | Guess a random consistent word. | A control / lower bound. |

The entropy, expected-size, and minimax strategies accept a `--guess-pool` of `answers`
(guess from remaining candidates) or `all` (guess from the full allowed list).

See [`docs/strategies.md`](docs/strategies.md) for an in-depth explanation of each strategy:
the scoring formulas, the bucket-splitting idea the information-theoretic strategies share
(with a worked example), the guess-pool trade-off, and how to add your own strategy.

## Limitations

- **Pure Python is slow for the `all` guess pool.** Scoring every valid word each turn takes
  minutes per benchmark, which is why the committed `all`-pool numbers stay on the curated set.
  For a single interactive `solve`/`play` it's fine (the opening is precomputed).
- **The word list is a snapshot.** `valid_words.txt` is the NYT valid-guess list as of mid-2025.
  If the NYT adds words later, refresh it and regenerate the opening table.
- **Six-guess failures are expected.** Over the full valid list even entropy fails about 9% of
  games, because clusters like `match`/`batch`/`catch`/`hatch` or the `-ound`/`-ight` families
  can't be separated in six turns. Those words are rarely real answers, so `--curated` is the
  realistic daily-play figure.
- **The strategies are greedy.** They optimize the current guess, not the whole game tree, so
  even the best is a step behind the known optimal decision tree (about 3.421 on the curated set).
- **English five-letter Wordle only.** No hard mode and no other word lengths (the engine assumes
  five letters), though `--answers`/`--allowed` accept custom five-letter word lists.

## Development

```bash
pip install -e ".[dev,bench]"
pytest --cov=wordlesmith      # tests + coverage
ruff check . && ruff format --check .
mypy src/
python -m build && twine check dist/*
```

Contributions welcome. A natural extension is adding a new strategy: implement `Strategy`,
register it, and it shows up in `compare` automatically. Please open an
[issue](https://github.com/adityakmehrotra/wordlesmith/issues) or PR.

## License &amp; contact

Distributed under the MIT License. See [`LICENSE.txt`](LICENSE.txt).

Aditya Mehrotra. Reach me at `adi1.mehrotra@gmail.com` or on
[LinkedIn](https://www.linkedin.com/in/aditya-mehrotra-).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

[ci-shield]: https://github.com/adityakmehrotra/wordlesmith/actions/workflows/ci.yml/badge.svg
[ci-url]: https://github.com/adityakmehrotra/wordlesmith/actions/workflows/ci.yml
[python-shield]: https://img.shields.io/badge/python-3.10%2B-blue
[python-url]: https://www.python.org/downloads/
[license-shield]: https://img.shields.io/badge/license-MIT-green
[license-url]: https://github.com/adityakmehrotra/wordlesmith/blob/main/LICENSE.txt
