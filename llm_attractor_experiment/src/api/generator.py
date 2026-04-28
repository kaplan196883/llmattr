from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from src.config import Config, ProviderConfig
from src.utils.logging import get_logger

log = get_logger(__name__)


@dataclass
class GenerationResult:
    output_text: str
    model: str
    response_id: str | None
    latency_sec: float
    retries: int
    raw: dict
    logprobs: Any | None = None


_RETRYABLE_HINTS = (
    "rate limit",
    "timeout",
    "temporar",
    "overload",
    "503",
    "502",
    "500",
    "connection",
)


def _is_retryable(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(h in msg for h in _RETRYABLE_HINTS)


# Global throttle: one min-interval lock per (api_key_env, base_url)
# pair so all in-process workers driving the same provider share the
# rate budget. Used by `_throttle()` below.
_throttle_locks: dict[tuple[str, str | None], threading.Lock] = {}
_throttle_last: dict[tuple[str, str | None], float] = {}


def _throttle(provider: ProviderConfig) -> None:
    """Sleep just enough to keep the global request rate ≤
    `provider.requests_per_minute` across every worker that shares
    this (api_key_env, base_url) combination. No-op when the field
    is None (default for the OpenAI Responses path)."""
    rpm = provider.requests_per_minute
    if not rpm or rpm <= 0:
        return
    key = (provider.api_key_env, provider.base_url)
    lock = _throttle_locks.setdefault(key, threading.Lock())
    min_interval = 60.0 / rpm
    with lock:
        last = _throttle_last.get(key, 0.0)
        wait = (last + min_interval) - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _throttle_last[key] = time.monotonic()


def generate_step(
    client: OpenAI,
    context_text: str,
    config: Config,
    system_prompt: str | None = None,
    max_retries: int = 5,
    base_delay: float = 2.0,
) -> GenerationResult:
    """Single recursive step. Dispatches to the OpenAI Responses API
    (`config.generation_provider.api == "responses"`) or to the
    OpenAI-compatible Chat Completions API (`"chat_completions"`).
    Both paths use client-side context only (`store=False` /
    no conversation state), so trajectories remain pure
    state-generator-nudge under the formalism in §3.1.
    """
    if not context_text.strip():
        raise ValueError("context_text must be non-empty")

    system = system_prompt or "Continue the text naturally. Do not summarize or explain."
    api = config.generation_provider.api
    if api == "responses":
        return _generate_responses(
            client, context_text, system, config, max_retries, base_delay
        )
    if api == "chat_completions":
        return _generate_chat_completions(
            client, context_text, system, config, max_retries, base_delay
        )
    raise ValueError(f"unknown generation_provider.api: {api!r}")


def _generate_responses(
    client: OpenAI,
    context_text: str,
    system: str,
    config: Config,
    max_retries: int,
    base_delay: float,
) -> GenerationResult:
    """OpenAI native Responses API (used by every existing exp_pub_*
    experiment in this repo)."""
    request: dict[str, Any] = {
        "model": config.generation_model,
        "input": [
            {"role": "developer", "content": system},
            {"role": "user", "content": context_text},
        ],
        "max_output_tokens": config.max_output_tokens,
        "store": False,
    }
    # Some newer reasoning models reject temperature/top_p; only include if set.
    if config.temperature is not None:
        request["temperature"] = config.temperature
    if config.top_p is not None:
        request["top_p"] = config.top_p
    if config.include_logprobs:
        request["include"] = ["message.output_text.logprobs"]

    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        t0 = time.monotonic()
        try:
            resp = client.responses.create(**request)
            latency = time.monotonic() - t0
            text = _extract_output_text(resp)
            logprobs = _extract_logprobs(resp) if config.include_logprobs else None
            raw = _response_to_dict(resp)
            return GenerationResult(
                output_text=text,
                model=getattr(resp, "model", config.generation_model),
                response_id=getattr(resp, "id", None),
                latency_sec=latency,
                retries=attempt,
                raw=raw,
                logprobs=logprobs,
            )
        except Exception as exc:
            last_exc = exc
            if attempt >= max_retries or not _is_retryable(exc):
                log.error("responses.create failed (attempt %d): %s", attempt, exc)
                raise
            delay = base_delay * (2**attempt) + random.uniform(0, 0.5)
            log.warning(
                "responses.create retryable error (attempt %d, sleeping %.1fs): %s",
                attempt,
                delay,
                exc,
            )
            time.sleep(delay)

    raise RuntimeError(f"generate_step exhausted retries: {last_exc}")


def _generate_chat_completions(
    client: OpenAI,
    context_text: str,
    system: str,
    config: Config,
    max_retries: int,
    base_delay: float,
) -> GenerationResult:
    """OpenAI-compatible Chat Completions API. Used for cross-vendor
    generators (MiniMax, DeepSeek, …) that don't implement Responses."""
    request: dict[str, Any] = {
        "model": config.generation_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": context_text},
        ],
        "max_tokens": config.max_output_tokens,
    }
    if config.temperature is not None:
        request["temperature"] = config.temperature
    if config.top_p is not None:
        request["top_p"] = config.top_p
    # Logprobs format differs across vendors; we keep the request flag
    # but don't force-extract — most cross-model runs don't need them.
    if config.include_logprobs:
        request["logprobs"] = True

    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        _throttle(config.generation_provider)
        t0 = time.monotonic()
        try:
            resp = client.chat.completions.create(**request)
            latency = time.monotonic() - t0
            choice = resp.choices[0] if resp.choices else None
            text = (choice.message.content or "") if choice is not None else ""
            raw = _response_to_dict(resp)
            logprobs_obj: Any | None = None
            if config.include_logprobs and choice is not None:
                lp = getattr(choice, "logprobs", None)
                if lp is not None:
                    try:
                        logprobs_obj = lp.model_dump()
                    except Exception:
                        logprobs_obj = None
            return GenerationResult(
                output_text=text,
                model=getattr(resp, "model", config.generation_model),
                response_id=getattr(resp, "id", None),
                latency_sec=latency,
                retries=attempt,
                raw=raw,
                logprobs=logprobs_obj,
            )
        except Exception as exc:
            last_exc = exc
            if attempt >= max_retries or not _is_retryable(exc):
                log.error("chat.completions.create failed (attempt %d): %s", attempt, exc)
                raise
            delay = base_delay * (2**attempt) + random.uniform(0, 0.5)
            log.warning(
                "chat.completions.create retryable error (attempt %d, sleeping %.1fs): %s",
                attempt,
                delay,
                exc,
            )
            time.sleep(delay)

    raise RuntimeError(f"generate_step exhausted retries: {last_exc}")


def _extract_output_text(resp: Any) -> str:
    text = getattr(resp, "output_text", None)
    if text:
        return text
    # Fallback: walk resp.output for content blocks
    out = getattr(resp, "output", None) or []
    chunks: list[str] = []
    for item in out:
        content = getattr(item, "content", None) or []
        for c in content:
            t = getattr(c, "text", None)
            if isinstance(t, str):
                chunks.append(t)
            elif hasattr(t, "value"):
                chunks.append(t.value)
    return "".join(chunks)


def _extract_logprobs(resp: Any) -> Any | None:
    out = getattr(resp, "output", None) or []
    for item in out:
        content = getattr(item, "content", None) or []
        for c in content:
            lp = getattr(c, "logprobs", None)
            if lp is not None:
                try:
                    return lp if isinstance(lp, (list, dict)) else lp.model_dump()
                except Exception:
                    return None
    return None


def _response_to_dict(resp: Any) -> dict:
    try:
        return resp.model_dump()
    except Exception:
        try:
            return dict(resp)
        except Exception:
            return {"repr": repr(resp)}
