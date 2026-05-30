REQUIRED_KEYS = ("host", "port")


def parse_config(d):
    """Parse a config dict and return (host, port).

    Required keys are listed in REQUIRED_KEYS. If any required key is
    missing, a ValueError should be raised whose message names the
    missing key(s). (Currently no validation is performed.)
    """
    return d["host"], d["port"]
