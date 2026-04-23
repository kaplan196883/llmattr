import pytest

from src.core.context import ContextOverflow, append_only_update, clip_context


def test_clip_tail_chars_shorter_than_limit():
    assert clip_context("hello", 100) == "hello"


def test_clip_tail_chars_truncates_head():
    assert clip_context("abcdefghij", 5) == "fghij"


def test_append_only_update_deterministic():
    ctx = "abcdef"
    out = "ghij"
    result = append_only_update(ctx, out, max_chars=8)
    assert result == "cdefghij"


def test_clip_strict_stop_raises():
    with pytest.raises(ContextOverflow):
        clip_context("abcdefgh", 4, rule="strict_stop")


def test_clip_unknown_rule():
    with pytest.raises(ValueError):
        clip_context("abcdefgh", 4, rule="does_not_exist")
