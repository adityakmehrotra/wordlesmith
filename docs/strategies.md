# Strategies

wordlesmith ships five strategies. They all plug into the same engine, so they
share one setup and differ only in how they pick the next guess. This document
explains the shared machinery first, then each strategy, then the options that
apply on top of them.

Each strategy below lists two averages: over all 14,855 valid words (the default
pool) and over the original 2,315-answer curated set (`--curated`). Both come
from [`../benchmarks/results/official/`](../benchmarks/results/official);
regenerate the primary with `python scripts/run_official_benchmark.py`.

## The candidate set

Wordle feedback colors each letter of a guess green (right letter, right spot),
yellow (in the word, wrong spot), or gray (not available). wordlesmith computes
this in two passes so duplicate letters are handled correctly: greens are
assigned first and consume their letter in the target, then yellows are assigned
left to right and consume remaining occurrences. Anything with no occurrence
left is gray. (This is why the second `E` in `SPEED` is gray against `ABIDE`,
which has only one `E`.)

After each guess, the solver keeps only the words still consistent with every
color seen so far. Concretely, it keeps a word `w` only if
`feedback(guess, w)` equals the pattern that was actually observed. The words
that survive are the **candidate set**: the words that could still be the
answer. Every strategy's only job is to look at the current candidate set and
choose the next word to guess.

## Splitting candidates into buckets

Three of the five strategies (entropy, expected-size, minimax) share one idea.

Before committing to a guess, imagine playing it against every remaining
candidate. Each candidate would return some color pattern. Group the candidates
by the pattern they would produce. Those groups are "buckets." Whichever bucket
the real answer falls into is exactly the candidate set you would be left with
next turn, so a guess that breaks the candidates into many small buckets is
informative, and a guess that dumps most of them into one big bucket barely
helps.

A worked example. Suppose the candidate set is the `-OUND` family, a classic
place a weak solver gets stuck:

```
bound  found  hound  mound  pound  round  sound  wound   (8 words)
```

Guessing one of the candidates only tests its own first letter, so it barely
splits the set. Guessing `MOUND` produces just two buckets:

```
ggggg -> mound
xgggg -> bound, found, hound, pound, round, sound, wound
```

If the answer is not `MOUND`, seven words are still tied and you have learned
almost nothing. A guess drawn from the full dictionary can test several of the
distinguishing first letters at once. The highest-information guess here is
`BARFS`, which splits the same eight words into five buckets (about 2.0 bits of
information):

```
xxxxx -> hound, mound, pound, wound
gxxxx -> bound
xxxyx -> found
xxyxx -> round
xxxxy -> sound
```

That is the intuition the scoring strategies formalize, each in a slightly
different way.

## The five strategies

### frequency (the original baseline)

Opening guess: `sanes` (valid pool) or `slate` (curated). Average: 4.922 over all
valid words, 3.640 on the curated set.

No bucketing. For each of the five positions, it counts how often each letter
appears in that position across the remaining candidates. A word's score is the
sum of its five per-position counts, and it guesses the highest-scoring word.

The intuition is "play the word built from the most common letters in the most
common positions." It is cheap and surprisingly effective, and it is the
heuristic the project started with. Its weakness is that it chases common
letters even when they no longer distinguish the remaining words, so it gets
stuck cycling through near-identical candidates. Solving `mound` on the curated
set, it plays
`slate`, `crony`, `bound`, `found`, `hound`, `mound`: six guesses spent walking
the `-OUND` family one first-letter at a time.

### entropy (maximum information gain)

Opening guess: `tares` (valid pool) or `raise` (curated). Average: 4.523 over all
valid words, 3.598 on the curated set (3.465 with the curated `all` pool). Best
average of the five.

Buckets the candidates by feedback pattern, then scores a guess by the Shannon
entropy of the bucket-size distribution:

```
score = -sum over buckets of  p * log2(p)      where p = bucket_size / total
```

Entropy is the expected number of bits of information the guess reveals. It is
maximized when the buckets are many and evenly sized, which is exactly the
"split them up" goal. The strategy guesses the word with the highest entropy.
This is the information-theoretic approach popularized by 3Blue1Brown, and it is
the strongest average performer here.

### expected-size (fewest candidates remaining)

Opening guess: `lares` (valid pool) or `raise` (curated). Average: 4.585 over all
valid words, 3.623 on the curated set (3.481 with the curated `all` pool).

Same buckets, simpler arithmetic. It computes the expected number of candidates
left after the guess and picks the guess that minimizes it:

```
score = sum over buckets of  bucket_size^2  /  total       (lower is better)
```

Each bucket contributes its size weighted by the probability of landing in it
(`bucket_size / total`), which works out to `sum(bucket_size^2) / total`. The
intuition is "leave me with as few possibilities as possible on average." It is
almost as strong as entropy and easier to reason about; in practice the two
usually pick the same or very similar guesses.

### minimax (best worst case)

Opening guess: `seria` (valid pool) or `arise` (curated). Average: 4.658 over all
valid words, 3.677 on the curated set (3.573 with the curated `all` pool).

Same buckets, but it looks only at the single largest bucket and picks the guess
that makes that largest bucket as small as possible:

```
score = max bucket_size        (lower is better)
```

This is Knuth's Mastermind heuristic applied to Wordle. It optimizes the worst
case rather than the average, so its mean guess count is a little higher than
entropy's, but it keeps the tail short: it never leaves a huge group of
survivors on any single turn. It is the strategy to reach for when the goal is
"never get stuck," and in the full pool it solves every answer with no failures.

### random (the control)

No opening preference. Average: 5.061 over all valid words, 4.039 on the curated
set. The worst of the five.

Guesses a uniformly random word from the remaining candidates. It uses feedback
only to stay consistent, never to choose informatively. It exists as a floor: it
shows how much the scoring strategies actually buy you. If a real strategy were
not clearly beating random, that would be a sign something is wrong. It accepts
a seed so its runs are reproducible.

## Options that apply on top

### Answer pool: all valid words vs curated (`--curated`)

By default every valid Wordle word is a possible answer, so the solver never
dead-ends on a real puzzle. `--curated` restricts the pool to the original 2,315
solutions, which is an easier problem and gives numbers comparable to published
solvers:

| strategy | all valid words | curated (2,315) |
| --- | --- | --- |
| entropy | 4.523 | 3.598 |
| expected-size | 4.585 | 3.623 |
| minimax | 4.658 | 3.677 |

The full-valid averages are higher, and even entropy fails about 9% of games,
because the valid list contains many near-identical clusters (`match`/`batch`/
`catch`/..., the `-ound` and `-ight` families) that cannot be separated in six
guesses. Those words are almost never real NYT answers, so the curated column is
the realistic "daily play" figure.

### Guess pool: answers vs all

The scoring strategies also take a `--guess-pool`:

- `answers` (default): guess only from words that could still be the answer.
- `all`: guess from the full valid-word list, including words that cannot win but
  split the candidates better (like `BARFS` above), for extra information.

On the curated set the `all` pool is the single biggest lever: it drops entropy
from 3.598 to 3.465, close to the known optimum of about 3.421, and eliminates
failures. It is far slower to benchmark, though, because it scores roughly 15,000
guesses every turn in pure Python, so the committed `all`-pool numbers are on the
curated set only.

### Two-candidate shortcut

When only one or two candidates remain, every strategy guesses one of them
directly instead of scoring. With two candidates left, scoring cannot beat a
coin flip, and guessing a candidate gives a chance to win outright, so this is a
small average-guess win as well as a speedup.

### Deterministic tie-breaking

When two guesses score equally, the scoring strategies prefer a guess that is
itself a possible answer (a chance to win on the spot), and then fall back to
alphabetical order. This makes every non-random strategy fully deterministic:
the same candidate set always yields the same guess.

## Adding your own strategy

Because all five share one interface, a new strategy is a single method. Subclass
`Strategy` (or `ScoringStrategy` if it fits the bucket-scoring shape), implement
`choose` (or `score`), and register it in `strategies/__init__.py`. It then works
everywhere automatically, including `wordlesmith compare`.
