import pytest

from src.experiments.operators.context import update_context


def test_append_mode_default():
    assert update_context("abc", "def", max_chars=100) == "abcdef"


def test_replace_mode_discards_context():
    assert update_context("abc", "def", max_chars=100, loop_mode="replace") == "def"


def test_replace_mode_respects_clip():
    assert update_context("abcdef", "X" * 100, max_chars=5, loop_mode="replace") == "XXXXX"


def test_append_mode_respects_clip():
    assert update_context("abcdef", "X" * 100, max_chars=5, loop_mode="append") == "XXXXX"


def test_unknown_loop_mode_raises():
    with pytest.raises(ValueError):
        update_context("a", "b", max_chars=10, loop_mode="banana")
