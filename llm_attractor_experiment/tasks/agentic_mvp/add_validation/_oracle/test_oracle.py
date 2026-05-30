import pytest

from config import parse_config


def test_valid_returns_tuple():
    assert parse_config({"host": "localhost", "port": 8080}) == ("localhost", 8080)


def test_missing_port_raises_valueerror():
    with pytest.raises(ValueError):
        parse_config({"host": "localhost"})


def test_missing_host_raises_valueerror():
    with pytest.raises(ValueError):
        parse_config({"port": 8080})


def test_error_message_names_missing_key():
    with pytest.raises(ValueError) as exc:
        parse_config({"host": "localhost"})
    assert "port" in str(exc.value)
