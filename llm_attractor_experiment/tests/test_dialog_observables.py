import pytest

from src.experiments.dialog.observables import (
    build_dialog_observables,
    observable_last_agent_turn,
    observable_last_role_turn,
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


# --- D2-style configurable role names ---

def _drilldown_steps(seed="SEED: q"):
    # 6-step drill-down: explorer asks, expert answers, alternating, explorer first.
    return [
        {"role": "explorer", "output_text": "EX0", "step": 0},
        {"role": "expert",   "output_text": "EP1", "step": 1},
        {"role": "explorer", "output_text": "EX2", "step": 2},
        {"role": "expert",   "output_text": "EP3", "step": 3},
        {"role": "explorer", "output_text": "EX4", "step": 4},
        {"role": "expert",   "output_text": "EP5", "step": 5},
    ]


def test_observable_last_role_turn_picks_named_role():
    steps = _drilldown_steps()
    assert observable_last_role_turn(steps, 0, "explorer") == "EX0"
    assert observable_last_role_turn(steps, 1, "explorer") == "EX0"  # repeats while expert speaks
    assert observable_last_role_turn(steps, 2, "explorer") == "EX2"
    assert observable_last_role_turn(steps, 3, "expert") == "EP3"
    assert observable_last_role_turn(steps, 0, "expert", fallback="SEED") == "SEED"


def test_build_dialog_observables_accepts_explorer_expert_role_names():
    steps = _drilldown_steps()
    out = build_dialog_observables(
        steps,
        [
            "output",
            "last_explorer_turn",
            "last_expert_turn",
            "rolling_explorer_k3",
            "rolling_expert_k2",
            "turn_pair",
        ],
        role_a_name="explorer",
        role_b_name="expert",
        k=3,
        tail_chars=100,
        full_chars=200,
        seed_utterance="SEED: q",
    )
    assert len(out["output"]) == 6
    # Step 0 is explorer's first turn, expert hasn't spoken yet.
    assert out["last_explorer_turn"][0] == "EX0"
    assert out["last_expert_turn"][0] == "SEED: q"
    # rolling_explorer_k3 at step 5 should contain all three explorer turns.
    rolling_ex_5 = out["rolling_explorer_k3"][5]
    assert "EX0" in rolling_ex_5 and "EX2" in rolling_ex_5 and "EX4" in rolling_ex_5
    # Rolling-explorer must NOT contain expert turns.
    assert "EP1" not in rolling_ex_5
    assert "EP3" not in rolling_ex_5
    assert "EP5" not in rolling_ex_5
    # turn_pair uses the configured role names in the labels.
    pair_5 = out["turn_pair"][5]
    assert "[Explorer]: EX4" in pair_5
    assert "[Expert]: EP5" in pair_5


def test_build_dialog_observables_legacy_role_name_falls_back_with_warning(caplog):
    steps = _drilldown_steps()
    # `last_user_turn` doesn't match the configured explorer/expert roles.
    # Historical D1-era configs that were copy-pasted into D2-style
    # explorer/expert experiments referenced the old D1 role names. The
    # cross-model regeneration of those configs in 2026-04 surfaced
    # this; rather than crash the embed phase mid-sweep we emit a
    # one-line WARNING and fill the column with the seed utterance,
    # leaving a constant-fill column the downstream pipeline can
    # simply ignore. (Was: ValueError; superseded once we needed
    # backward compat across many existing configs.)
    import logging
    with caplog.at_level(logging.WARNING):
        out = build_dialog_observables(
            steps,
            ["last_user_turn"],
            role_a_name="explorer",
            role_b_name="expert",
            k=3,
            tail_chars=100,
            full_chars=200,
            seed_utterance="SEED: q",
        )
    assert "last_user_turn" in out
    assert all(s == "SEED: q" for s in out["last_user_turn"])
    assert any(
        "doesn't match configured role_a" in rec.message
        for rec in caplog.records
    ), "legacy-role fallback should emit a WARNING for visibility"
