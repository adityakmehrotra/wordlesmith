"""Word-list loading tests."""

from __future__ import annotations

import pytest

from wordlesmith.words import load_curated_answers, load_valid_words, load_words


def test_valid_word_list_shape() -> None:
    valid = load_valid_words()
    assert len(valid) == 14855
    assert all(len(w) == 5 and w.isalpha() and w.islower() for w in valid)
    assert len(set(valid)) == len(valid)
    assert list(valid) == sorted(valid)


def test_curated_list_shape() -> None:
    curated = load_curated_answers()
    assert len(curated) == 2315
    assert all(len(w) == 5 and w.isalpha() and w.islower() for w in curated)


def test_curated_is_subset_of_valid() -> None:
    assert set(load_curated_answers()) <= set(load_valid_words())


def test_todays_answer_is_solvable() -> None:
    # Regression: MAVEN (a real NYT answer) is missing from the curated set but
    # present in the valid-word list, so the default solver can reach it.
    assert "maven" in set(load_valid_words())
    assert "maven" not in set(load_curated_answers())


def test_load_custom_words(tmp_path) -> None:
    p = tmp_path / "mine.txt"
    p.write_text("# a comment\nCRANE\nslate\nslate\n")
    assert load_words(p) == ("crane", "slate")


def test_load_words_rejects_bad_length(tmp_path) -> None:
    p = tmp_path / "bad.txt"
    p.write_text("crane\ntoolong\n")
    with pytest.raises(ValueError):
        load_words(p)
