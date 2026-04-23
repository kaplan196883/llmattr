from src.core.observables import build_all_for_run, observable_context_full


def test_context_full_short_context_returned_whole():
    step = {"context_after": "abcdefg", "output_text": "g"}
    assert observable_context_full(step, max_chars=100) == "abcdefg"


def test_context_full_tails_to_fixed_size():
    big = "".join(chr(ord("a") + (i % 26)) for i in range(50_000))
    step = {"context_after": big, "output_text": "X"}
    result = observable_context_full(step, max_chars=8000)
    assert len(result) == 8000
    assert result == big[-8000:]


def test_context_full_always_tail_slices():
    # Even when context is exactly at the limit, slice is deterministic.
    s = "A" * 8000
    step = {"context_after": s}
    assert observable_context_full(step, max_chars=8000) == s


def test_build_all_for_run_passes_full_chars():
    steps = [
        {"output_text": "a", "context_after": "X_0 a"},
        {"output_text": "b", "context_after": "X_0 a b"},
    ]
    built = build_all_for_run(steps, ["context_full"], k=3, tail_chars=100, full_chars=5)
    # max_chars=5 → tail-slice to last 5 chars each step
    assert built["context_full"] == ["X_0 a", "0 a b"]
