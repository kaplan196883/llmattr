import hashlib


def sha1_short(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="replace")).hexdigest()[:16]


def truncate_for_display(text: str, n: int = 120) -> str:
    if len(text) <= n:
        return text
    return text[: n - 1] + "…"


def approx_token_count(text: str) -> int:
    # rough 4 chars/token estimator, no tokenizer dependency
    return max(1, len(text) // 4)
