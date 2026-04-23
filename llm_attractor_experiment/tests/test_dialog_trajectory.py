import pytest

from src.experiments.dialog.trajectory import Role, _format_turn, _last_turn


def test_format_turn_produces_speaker_label():
    assert _format_turn("user", "hello") == "[User]: hello\n\n"
    assert _format_turn("agent", "hi there") == "[Agent]: hi there\n\n"


def test_format_turn_strips_whitespace():
    assert _format_turn("user", "   hello   \n") == "[User]: hello\n\n"


def test_last_turn_returns_final_block():
    transcript = "[User]: hello\n\n[Agent]: hi\n\n[User]: how are you\n\n"
    assert _last_turn(transcript) == "[User]: how are you\n\n"


def test_last_turn_handles_single_turn():
    transcript = "[User]: hello\n\n"
    assert _last_turn(transcript) == "[User]: hello\n\n"


def test_last_turn_empty():
    assert _last_turn("") == ""


def test_role_dataclass_holds_name_and_prompt():
    r = Role(name="agent", system_prompt="Be helpful.")
    assert r.name == "agent"
    assert r.system_prompt == "Be helpful."
