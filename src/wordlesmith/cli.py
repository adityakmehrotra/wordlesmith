"""Command-line interface (argparse, standard library only).

wordlesmith play        Interactive assistant: suggests guesses, you enter feedback
wordlesmith solve WORD   Auto-play a known target word
wordlesmith benchmark    Run a strategy over all answers, report stats
wordlesmith compare      Benchmark multiple strategies side by side
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from . import __version__
from .benchmark import (
    compare,
    format_distribution,
    format_markdown,
    format_table,
    run_benchmark,
    to_csv,
    to_json,
)
from .feedback import ALL_GREEN, WORD_LEN, feedback, pattern_from_string, pattern_to_string
from .game import MAX_TURNS, GameState
from .strategies import available_strategies, get_strategy
from .words import load_curated_answers, load_valid_words, load_words


def _load_lists(args: argparse.Namespace) -> tuple[tuple[str, ...] | None, tuple[str, ...] | None]:
    answers = load_words(args.answers) if getattr(args, "answers", None) else None
    allowed = load_words(args.allowed) if getattr(args, "allowed", None) else None
    return answers, allowed


def _warn_custom_jobs(args: argparse.Namespace) -> None:
    if getattr(args, "jobs", 1) > 1 and (args.answers or args.allowed):
        print(
            "note: custom --answers/--allowed lists run single-process; --jobs is ignored.",
            file=sys.stderr,
        )


def _parse_play_input(line: str, suggestion: str) -> tuple[str, int]:
    """Parse a play line: either "<feedback>" or "<word> <feedback>"."""
    tokens = line.split()
    if not tokens:
        raise ValueError("empty input")
    if len(tokens) == 1:
        return suggestion, pattern_from_string(tokens[0])
    word = tokens[0].lower()
    if len(word) != WORD_LEN or not word.isalpha():
        raise ValueError(f"expected a {WORD_LEN}-letter word, got {tokens[0]!r}")
    return word, pattern_from_string(" ".join(tokens[1:]))


def cmd_play(args: argparse.Namespace) -> int:
    answers, allowed = _load_lists(args)
    if answers is None and args.curated:
        answers = load_curated_answers()
    state = GameState.new(answers=answers, allowed_guesses=allowed)
    strategy = get_strategy(args.strategy, guess_pool=args.guess_pool)
    print(f"Playing with strategy '{args.strategy}' (guess pool: {args.guess_pool}).")
    print(
        "Enter feedback as g/y/x (e.g. xgyxx) or 0,1,0,0,2. "
        "Prefix with the word you guessed to override the suggestion.\n"
    )

    turn = 1
    while turn <= MAX_TURNS:
        if not state.candidates:
            print("No candidate answers remain; check the feedback entered.")
            return 1
        suggestion = (
            args.first_guess if (turn == 1 and args.first_guess) else strategy.choose(state)
        )
        count = len(state.candidates)
        print(
            f"Turn {turn} suggestion: {suggestion.upper()}   "
            f"({count} candidate{'s' if count != 1 else ''})"
        )
        try:
            line = input("Enter feedback: ")
        except EOFError:
            print("\nInput closed; stopping.")
            return 1
        try:
            guess, pattern = _parse_play_input(line, suggestion)
        except ValueError as exc:
            print(f"  ! {exc}. Try again.\n")
            continue  # re-prompt the same turn without advancing
        if pattern == ALL_GREEN:
            print(
                f"Solved: the word is {guess.upper()} in {turn} guess{'es' if turn != 1 else ''}."
            )
            return 0
        state.record(guess, pattern)
        turn += 1

    print("Out of turns.")
    return 1


def cmd_solve(args: argparse.Namespace) -> int:
    target = args.word.lower()
    if len(target) != WORD_LEN or not target.isalpha():
        print(f"error: target must be {WORD_LEN} letters: {args.word!r}", file=sys.stderr)
        return 2

    answers, allowed = _load_lists(args)
    if answers is None and args.curated:
        answers = load_curated_answers()
    allowed_set = set(allowed) if allowed is not None else set(load_valid_words())
    if target not in allowed_set:
        if not args.force:
            print(
                f"error: {target!r} is not in the allowed-guess list; "
                "pass --force to solve it anyway.",
                file=sys.stderr,
            )
            return 2
        print(
            f"warning: {target!r} is not in the allowed-guess list; solving anyway.",
            file=sys.stderr,
        )

    state = GameState.new(answers=answers, allowed_guesses=allowed)
    strategy = get_strategy(args.strategy, guess_pool=args.guess_pool)
    for turn in range(1, MAX_TURNS + 1):
        guess = strategy.choose(state)
        pattern = feedback(guess, target)
        print(
            f"Turn {turn}: {guess.upper()}  [{pattern_to_string(pattern)}]  "
            f"({len(state.candidates)} candidates)"
        )
        if pattern == ALL_GREEN:
            print(f"Solved in {turn} guess{'es' if turn != 1 else ''}.")
            return 0
        state.record(guess, pattern)
    print("Not solved within 6 guesses.")
    return 1


def cmd_benchmark(args: argparse.Namespace) -> int:
    answers, allowed = _load_lists(args)
    _warn_custom_jobs(args)
    result = run_benchmark(
        args.strategy,
        guess_pool=args.guess_pool,
        sample=args.sample,
        seed=args.seed,
        jobs=args.jobs,
        curated=args.curated,
        answers=answers,
        allowed_guesses=allowed,
    )
    print(
        f"strategy={result.strategy}  pool={result.guess_pool}  words={result.num_words}  "
        f"seed={result.seed}"
    )
    print(
        f"average={result.average:.4f}  median={result.median}  max={result.maximum}  "
        f"fails={result.fails} ({result.fail_pct:.2f}%)  time={result.wall_seconds:.1f}s"
    )
    print()
    print(format_distribution(result))
    if args.output:
        to_csv([result], args.output)
        print(f"\nwrote CSV: {args.output}")
    if args.json:
        to_json([result], args.json)
        print(f"wrote JSON: {args.json}")
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    strategies = (
        [s.strip() for s in args.strategies.split(",")]
        if args.strategies
        else available_strategies()
    )
    unknown = [s for s in strategies if s not in available_strategies()]
    if unknown:
        print(
            f"error: unknown strategy(ies): {unknown}; choose from {available_strategies()}",
            file=sys.stderr,
        )
        return 2
    answers, allowed = _load_lists(args)
    _warn_custom_jobs(args)
    results = compare(
        strategies,
        guess_pool=args.guess_pool,
        sample=args.sample,
        seed=args.seed,
        jobs=args.jobs,
        curated=args.curated,
        answers=answers,
        allowed_guesses=allowed,
    )
    print(format_markdown(results) if args.markdown else format_table(results))
    if args.output:
        to_csv(results, args.output)
        print(f"\nwrote CSV: {args.output}")
    if args.json:
        to_json(results, args.json)
        print(f"wrote JSON: {args.json}")
    return 0


def _add_common_list_args(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--curated",
        action="store_true",
        help="use the original 2,315-word answer set instead of all valid words",
    )
    p.add_argument("--answers", metavar="PATH", help="custom answer list (one word per line)")
    p.add_argument("--allowed", metavar="PATH", help="custom allowed-guess list")


def build_parser() -> argparse.ArgumentParser:
    strategies = available_strategies()
    parser = argparse.ArgumentParser(
        prog="wordlesmith",
        description="A Wordle solver with pluggable strategies.",
    )
    parser.add_argument("--version", action="version", version=f"wordlesmith {__version__}")
    sub = parser.add_subparsers(
        dest="command", required=True, metavar="{play,solve,benchmark,compare}"
    )

    # play
    p_play = sub.add_parser(
        "play", help="interactive assistant: suggests guesses, you enter feedback"
    )
    p_play.add_argument("--strategy", choices=strategies, default="entropy")
    p_play.add_argument("--guess-pool", choices=["answers", "all"], default="answers")
    p_play.add_argument("--first-guess", metavar="WORD", help="override the first suggested guess")
    _add_common_list_args(p_play)
    p_play.set_defaults(func=cmd_play)

    # solve
    p_solve = sub.add_parser("solve", help="auto-play a known target word")
    p_solve.add_argument("word", help="the target word to solve")
    p_solve.add_argument("--strategy", choices=strategies, default="entropy")
    p_solve.add_argument("--guess-pool", choices=["answers", "all"], default="answers")
    p_solve.add_argument(
        "--force", action="store_true", help="solve even if the word is not in the allowed list"
    )
    _add_common_list_args(p_solve)
    p_solve.set_defaults(func=cmd_solve)

    # benchmark
    p_bench = sub.add_parser("benchmark", help="run a strategy over all answers, report stats")
    p_bench.add_argument("--strategy", choices=strategies, default="entropy")
    p_bench.add_argument("--guess-pool", choices=["answers", "all"], default="answers")
    p_bench.add_argument("--sample", type=int, metavar="N", help="benchmark a random N-word sample")
    p_bench.add_argument("--seed", type=int, default=0)
    p_bench.add_argument(
        "--jobs",
        type=int,
        default=1,
        help="parallel worker processes (ignored for random and custom lists)",
    )
    p_bench.add_argument("--output", metavar="PATH", help="write results as CSV")
    p_bench.add_argument("--json", metavar="PATH", help="write results as JSON")
    _add_common_list_args(p_bench)
    p_bench.set_defaults(func=cmd_benchmark)

    # compare
    p_cmp = sub.add_parser("compare", help="benchmark multiple strategies side by side")
    p_cmp.add_argument(
        "--strategies",
        metavar="A,B,C",
        help=f"comma-separated (default: all of {','.join(strategies)})",
    )
    p_cmp.add_argument("--guess-pool", choices=["answers", "all"], default="answers")
    p_cmp.add_argument("--sample", type=int, metavar="N", help="benchmark a random N-word sample")
    p_cmp.add_argument("--seed", type=int, default=0)
    p_cmp.add_argument(
        "--jobs",
        type=int,
        default=1,
        help="parallel worker processes (ignored for random and custom lists)",
    )
    p_cmp.add_argument("--markdown", action="store_true", help="emit a Markdown table")
    p_cmp.add_argument("--output", metavar="PATH", help="write results as CSV")
    p_cmp.add_argument("--json", metavar="PATH", help="write results as JSON")
    _add_common_list_args(p_cmp)
    p_cmp.set_defaults(func=cmd_compare)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
