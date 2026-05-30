"""Anthropic tool-calling client for the agentic loop.

Wraps the Messages API (anthropic 0.75.0) for the agent-under-test
(claude-haiku-4-5) and the auxiliary models (summarizer, judge). The
agent is driven *one turn at a time* by the loop: the loop owns the
message list (so the Nudge can rewrite it between turns), and this
client just executes a single Messages.create call given the current
message list + tool schemas, returning the structured turn output.

This mirrors the parent repo's `src/api/generator.py` GenerationResult
convention (output text, model, response id, latency, retries, raw) but
adds the tool-use channel.
"""
from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import anthropic
from dotenv import load_dotenv

from src.utils.logging import get_logger

log = get_logger(__name__)


@dataclass
class ToolCall:
    id: str            # Anthropic tool_use block id (for the tool_result)
    name: str
    params: dict


@dataclass
class AgentTurn:
    """One agent turn: assistant text (reasoning) + ordered tool calls.
    `stop_reason` == 'tool_use' means the agent wants tool results back;
    'end_turn' (with no tool calls) is the terminal signal."""
    text: str
    tool_calls: list[ToolCall]
    stop_reason: str
    model: str
    response_id: str | None
    latency_sec: float
    retries: int
    usage: dict
    raw_assistant_content: list  # the assistant content blocks, verbatim

    @property
    def is_terminal(self) -> bool:
        return self.stop_reason != "tool_use" and not self.tool_calls


# Retry by EXCEPTION TYPE (robust) rather than substring matching the
# message. The 429 rate-limit, transient 5xx, connection, and timeout
# errors are retryable; auth/permission/4xx-other are not.
_RETRYABLE_TYPES = (
    anthropic.RateLimitError,
    anthropic.APIConnectionError,
    anthropic.APITimeoutError,
    anthropic.InternalServerError,
)


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, _RETRYABLE_TYPES):
        return True
    # APIStatusError covers other status codes; retry on 429/5xx/529.
    if isinstance(exc, anthropic.APIStatusError):
        code = getattr(exc, "status_code", None)
        return code in (429, 500, 502, 503, 529)
    return False


def _retry_after_seconds(exc: Exception, default: float) -> float:
    """Honor the server's retry-after header on a 429 when present."""
    resp = getattr(exc, "response", None)
    if resp is not None:
        headers = getattr(resp, "headers", {}) or {}
        for key in ("retry-after", "Retry-After"):
            val = headers.get(key)
            if val:
                try:
                    return float(val)
                except (TypeError, ValueError):
                    pass
    return default


def _load_env() -> None:
    for parent in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (parent / ".env").exists():
            load_dotenv(parent / ".env", override=False)
            break


def make_anthropic_client(max_retries: int = 8) -> anthropic.Anthropic:
    _load_env()
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY not set (add to .env)")
    # max_retries lets the SDK transparently retry 429/5xx/overloaded
    # while honoring the server's retry-after header — the primary
    # rate-limit defense. Our wrapper below is a secondary net.
    return anthropic.Anthropic(api_key=key, max_retries=max_retries)


def run_turn(
    client: anthropic.Anthropic,
    model: str,
    system: str,
    messages: list[dict],
    tools: list[dict],
    max_tokens: int = 2048,
    temperature: float = 0.8,
    top_p: float = 1.0,
    max_retries: int = 5,
    base_delay: float = 2.0,
) -> AgentTurn:
    """Execute one Messages.create call and parse the assistant turn into
    text + tool calls. The caller owns `messages` and appends the
    assistant turn + tool results itself (so the Nudge can intercept)."""
    request: dict[str, Any] = {
        "model": model,
        "system": system,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    # Claude models reject temperature + top_p together; prefer temperature
    # and only fall back to top_p when temperature is left unset.
    if temperature is not None:
        request["temperature"] = temperature
    elif top_p is not None:
        request["top_p"] = top_p
    if tools:
        request["tools"] = tools

    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        t0 = time.monotonic()
        try:
            resp = client.messages.create(**request)
            latency = time.monotonic() - t0
            text_parts: list[str] = []
            tool_calls: list[ToolCall] = []
            raw_blocks: list = []
            for block in resp.content:
                raw_blocks.append(_block_to_param(block))
                if block.type == "text":
                    text_parts.append(block.text)
                elif block.type == "tool_use":
                    tool_calls.append(ToolCall(
                        id=block.id, name=block.name,
                        params=dict(block.input or {}),
                    ))
            usage = {}
            if getattr(resp, "usage", None) is not None:
                usage = {
                    "input_tokens": getattr(resp.usage, "input_tokens", None),
                    "output_tokens": getattr(resp.usage, "output_tokens", None),
                }
            return AgentTurn(
                text="".join(text_parts),
                tool_calls=tool_calls,
                stop_reason=resp.stop_reason or "",
                model=getattr(resp, "model", model),
                response_id=getattr(resp, "id", None),
                latency_sec=latency,
                retries=attempt,
                usage=usage,
                raw_assistant_content=raw_blocks,
            )
        except Exception as exc:
            last_exc = exc
            if attempt >= max_retries or not _is_retryable(exc):
                log.error("messages.create failed (attempt %d): %s", attempt, exc)
                raise
            backoff = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
            delay = _retry_after_seconds(exc, default=backoff)
            log.warning("messages.create retryable (attempt %d, sleep %.1fs): %s",
                        attempt, delay, type(exc).__name__)
            time.sleep(delay)
    raise RuntimeError(f"run_turn exhausted retries: {last_exc}")


def _block_to_param(block: Any) -> dict:
    """Serialize a response content block back into a request-shaped
    param dict, so it can be appended to `messages` as the assistant
    turn for the next call."""
    if block.type == "text":
        return {"type": "text", "text": block.text}
    if block.type == "tool_use":
        return {"type": "tool_use", "id": block.id,
                "name": block.name, "input": block.input}
    # Fallback: best-effort dump
    try:
        return block.model_dump()
    except Exception:
        return {"type": block.type}


def simple_completion(
    client: anthropic.Anthropic,
    model: str,
    system: str,
    user: str,
    max_tokens: int = 1024,
    temperature: float = 0.0,
    max_retries: int = 5,
    base_delay: float = 2.0,
) -> str:
    """A plain text completion (no tools) for the summarizer, judge, and
    reflector auxiliary models."""
    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            resp = client.messages.create(
                model=model, system=system,
                messages=[{"role": "user", "content": user}],
                max_tokens=max_tokens, temperature=temperature,
            )
            return "".join(b.text for b in resp.content if b.type == "text")
        except Exception as exc:
            last_exc = exc
            if attempt >= max_retries or not _is_retryable(exc):
                raise
            backoff = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
            time.sleep(_retry_after_seconds(exc, default=backoff))
    raise RuntimeError(f"simple_completion exhausted retries: {last_exc}")
