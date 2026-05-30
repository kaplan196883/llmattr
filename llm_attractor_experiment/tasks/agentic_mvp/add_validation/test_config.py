import pytest

from config import parse_config


def test_valid():
    assert parse_config({"host": "localhost", "port": 8080}) == ("localhost", 8080)


def test_missing_key_raises_valueerror():
    with pytest.raises(ValueError):
        parse_config({"host": "localhost"})
