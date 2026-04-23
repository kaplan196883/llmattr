from src.core.observables import ROLLING_SEP, build_all_for_run


def _steps(texts):
    return [
        {"output_text": t, "context_after": "".join(texts[: i + 1])}
        for i, t in enumerate(texts)
    ]


def test_rolling_k5_parsed_from_name():
    s = _steps(["a", "b", "c", "d", "e", "f"])
    built = build_all_for_run(s, ["rolling_k5"], k=3, tail_chars=100)
    # at t=5, rolling_k5 should include steps 1..5
    assert built["rolling_k5"][5] == ROLLING_SEP.join(["b", "c", "d", "e", "f"])


def test_rolling_defaults_to_config_k_when_name_unsuffixed():
    s = _steps(["a", "b", "c", "d"])
    built = build_all_for_run(s, ["rolling"], k=2, tail_chars=100)
    assert built["rolling"][3] == ROLLING_SEP.join(["c", "d"])


def test_rolling_unknown_observable_still_raises():
    s = _steps(["a", "b"])
    try:
        build_all_for_run(s, ["banana"], k=3, tail_chars=100)
    except ValueError:
        return
    raise AssertionError("expected ValueError")
