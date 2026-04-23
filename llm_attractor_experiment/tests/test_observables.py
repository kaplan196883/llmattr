from src.core.observables import (
    ROLLING_SEP,
    build_all_for_run,
    observable_context_tail,
    observable_output,
    observable_rolling,
)


def _steps(texts):
    return [
        {
            "output_text": t,
            "context_after": "".join(texts[: i + 1]),
        }
        for i, t in enumerate(texts)
    ]


def test_output_observable():
    s = _steps(["a", "b", "c"])
    assert observable_output(s[1]) == "b"


def test_rolling_early_steps_are_shorter():
    s = _steps(["A", "B", "C", "D"])
    assert observable_rolling(s, 0, k=3) == "A"
    assert observable_rolling(s, 1, k=3) == f"A{ROLLING_SEP}B"
    assert observable_rolling(s, 2, k=3) == f"A{ROLLING_SEP}B{ROLLING_SEP}C"
    assert observable_rolling(s, 3, k=3) == f"B{ROLLING_SEP}C{ROLLING_SEP}D"


def test_context_tail_limits_length():
    step = {"context_after": "0123456789"}
    assert observable_context_tail(step, max_chars=4) == "6789"


def test_build_all_for_run_lengths_match():
    s = _steps(["one", "two", "three", "four"])
    built = build_all_for_run(s, ["output", "rolling_k3", "context_tail"], k=3, tail_chars=4)
    assert len(built["output"]) == 4
    assert len(built["rolling_k3"]) == 4
    assert len(built["context_tail"]) == 4
    assert built["output"] == ["one", "two", "three", "four"]


def test_rolling_is_deterministic():
    s = _steps(["alpha", "beta", "gamma"])
    a = observable_rolling(s, 2, k=3)
    b = observable_rolling(s, 2, k=3)
    assert a == b
