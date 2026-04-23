import pytest

from src.experiments.dialog.observables import (
    build_dialog_observables,
    observable_last_agent_turn,
    observable_last_user_turn,
    observable_rolling_role,
    observable_turn_pair,
)


def _dialog_steps(seed="SEED: hello"):
    # 6-step dialog alternating agent/user starting with agent.
    # Transcript is (seed at t=-1 as role_a's opener, then agent, user, agent, ...).
    return [
        {"role": "agent", "output_text": "A0", "step": 0, "context_after": seed + " A0"},
        {"role": "user",  "output_text": "U1", "step": 1, "context_after": seed + " A0 U1"},
        {"role": "agent", "output_text": "A2", "step": 2, "context_after": seed + " A0 U1 A2"},
        {"role": "user",  "output_text": "U3", "step": 3, "context_after": seed + " A0 U1 A2 U3"},
        {"role": "agent", "output_text": "A4", "step": 4, "context_after": seed + " A0 U1 A2 U3 A4"},
        {"role": "user",  "output_text": "U5", "step": 5, "context_after": seed + " A0 U1 A2 U3 A4 U5"},
    ]


def test_last_user_turn_uses_fallback_before_any_user():
    steps = _dialog_steps()
    assert observable_last_user_turn(steps, 0, fallback="SEED") == "SEED"


def test_last_user_turn_repeats_when_not_matching_role():
    steps = _dialog_steps()
    # Step 1 is user → U1; step 2 is agent, so last-user = U1
    assert observable_last_user_turn(steps, 1) == "U1"
    assert observable_last_user_turn(steps, 2) == "U1"
    assert observable_last_user_turn(steps, 3) == "U3"


def test_last_agent_turn_tracks_most_recent_agent():
    steps = _dialog_steps()
    assert observable_last_agent_turn(steps, 0) == "A0"
    assert observable_last_agent_turn(steps, 1) == "A0"
    assert observable_last_agent_turn(steps, 2) == "A2"
    assert observable_last_agent_turn(steps, 4) == "A4"


def test_rolling_role_user_k3_down_to_user_turns_only():
    steps = _dialog_steps()
    # At step 5 (user), last 3 user turns = [U1, U3, U5]
    out = observable_rolling_role(steps, 5, "user", k=3)
    assert "U1" in out and "U3" in out and "U5" in out
    assert "A0" not in out and "A2" not in out


def test_rolling_role_agent_k2():
    steps = _dialog_steps()
    # At step 4 (agent), last 2 agent turns = [A2, A4]
    out = observable_rolling_role(steps, 4, "agent", k=2)
    assert "A2" in out and "A4" in out
    assert "A0" not in out
    assert "U1" not in out and "U3" not in out


def test_turn_pair_formats_as_labeled_exchange():
    steps = _dialog_steps()
    pair = observable_turn_pair(steps, 2)
    assert "[User]: U1" in pair
    assert "[Agent]: A2" in pair


def test_build_dialog_observables_delegates_for_generic_and_handles_role_ones():
    steps = _dialog_steps()
    out = build_dialog_observables(
        steps,
        ["output", "last_user_turn", "last_agent_turn", "rolling_user_k3", "rolling_agent_k3", "turn_pair"],
        k=3,
        tail_chars=100,
        full_chars=200,
        seed_utterance="SEED: hello",
    )
    assert len(out["output"]) == 6
    assert out["last_user_turn"][0] == "SEED: hello"  # fallback at step 0
    assert out["last_user_turn"][1] == "U1"
    assert out["last_agent_turn"][0] == "A0"
    assert out["turn_pair"][5].startswith("[User]: U5")


def test_build_dialog_rejects_unknown_observable():
    steps = _dialog_steps()
    with pytest.raises(ValueError):
        build_dialog_observables(steps, ["banana"], k=3, tail_chars=100, full_chars=200)
