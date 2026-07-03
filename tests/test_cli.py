"""CLI tests: invoke main(argv) directly and capture output."""

from __future__ import annotations

import pytest

from wordlesmith.cli import _parse_play_input, main
from wordlesmith.feedback import ALL_GREEN, pattern_from_string


def test_solve_known_word(capsys) -> None:
    rc = main(["solve", "crane", "--strategy", "entropy"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Solved" in out
    assert "CRANE" in out


def test_solve_rejects_non_word(capsys) -> None:
    rc = main(["solve", "toolong"])
    assert rc == 2
    assert "5 letters" in capsys.readouterr().err


def test_solve_unknown_word_requires_force(capsys) -> None:
    # "zzzzz" is not in the allowed list.
    rc = main(["solve", "zzzzz"])
    assert rc == 2
    assert "--force" in capsys.readouterr().err


def test_benchmark_sample(capsys) -> None:
    rc = main(["benchmark", "--strategy", "frequency", "--sample", "10", "--seed", "1"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "average=" in out
    assert "unsolved" in out


def test_compare_markdown(capsys) -> None:
    rc = main(["compare", "--strategies", "frequency,random", "--sample", "10", "--markdown"])
    out = capsys.readouterr().out
    assert rc == 0
    assert out.strip().startswith("| strategy |")


def test_compare_unknown_strategy(capsys) -> None:
    rc = main(["compare", "--strategies", "frequency,bogus", "--sample", "5"])
    assert rc == 2
    assert "unknown strategy" in capsys.readouterr().err


def test_benchmark_writes_files(tmp_path, capsys) -> None:
    csv_path = tmp_path / "b.csv"
    rc = main(["benchmark", "--strategy", "frequency", "--sample", "8", "--output", str(csv_path)])
    assert rc == 0
    assert csv_path.exists()


def test_play_reads_scripted_session(monkeypatch, capsys) -> None:
    # Feed a word + feedback line that immediately solves.
    inputs = iter(["crane ggggg"])
    monkeypatch.setattr("builtins.input", lambda *_: next(inputs))
    rc = main(["play", "--strategy", "frequency"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Solved" in out


def test_play_reprompts_on_bad_input(monkeypatch, capsys) -> None:
    # First line is malformed, second solves; the turn must not be consumed.
    inputs = iter(["not-valid", "crane ggggg"])
    monkeypatch.setattr("builtins.input", lambda *_: next(inputs))
    rc = main(["play", "--strategy", "frequency"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Try again" in out
    assert "Solved" in out


def test_parse_play_input_forms() -> None:
    # Feedback only -> uses the suggestion.
    assert _parse_play_input("xgyxx", "slate") == ("slate", pattern_from_string("xgyxx"))
    # Word + feedback -> overrides the guess.
    assert _parse_play_input("crane ggggg", "slate") == ("crane", ALL_GREEN)
    # Legacy numeric feedback.
    assert _parse_play_input("crane 2,2,2,2,2", "slate") == ("crane", ALL_GREEN)


@pytest.mark.parametrize("bad", ["", "gg", "gyzxg", "toolong ggggg"])
def test_parse_play_input_rejects_bad(bad: str) -> None:
    with pytest.raises(ValueError):
        _parse_play_input(bad, "slate")
