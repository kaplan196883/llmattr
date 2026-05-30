"""Endpoint computation. See docs/AGENTIC_MVP_SPEC.md §6 and
ARTICLE_CODING.md §3.3.

Primary (MVP gate): redirect-survival — did the redirect persist into the
terminal visible state X_T? Computed by verbatim/normalized match first
(cheap, no model call) with an optional embedding-cosine fallback that
catches summarizer paraphrase (A2). No judge needed.

Diagnostic: redirect-compliance (judge model, sampled); task success
(oracle).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from src.utils.logging import get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# serialization
# ---------------------------------------------------------------------------

def messages_to_text(messages: list[dict]) -> str:
    """Flatten an Anthropic messages list to plain text for matching."""
    parts: list[str] = []
    for m in messages:
        c = m.get("content")
        if isinstance(c, str):
            parts.append(c)
        elif isinstance(c, list):
            for b in c:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text":
                    parts.append(str(b.get("text", "")))
                elif b.get("type") == "tool_use":
                    parts.append(str(b.get("input", "")))
                elif b.get("type") == "tool_result":
                    parts.append(str(b.get("content", "")))
    return "\n".join(parts)


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


# ---------------------------------------------------------------------------
# redirect-survival (primary)
# ---------------------------------------------------------------------------

def _redirect_core(redirect_text: str, n_chars: int = 48) -> str:
    """A distinctive prefix of the redirect used for verbatim matching.
    The dose-padding elaboration is shared across tasks, so the
    instruction-bearing prefix is the discriminative part."""
    core = redirect_text.strip()
    # strip a leading "[user] " frame if present
    core = re.sub(r"^\[user\]\s*", "", core)
    return core[:n_chars]


def redirect_survival(final_messages: list[dict], redirect_text: str,
                      embed_fn=None, threshold: float = 0.80) -> dict:
    """Return {survived: bool, method: str, score: float|None}.

    verbatim: the normalized redirect core is a substring of the
    normalized terminal context. cosine (optional fallback): max cosine
    similarity between the redirect and sliding windows of the terminal
    context >= threshold (catches summarizer paraphrase)."""
    final_text = messages_to_text(final_messages)
    norm_final = _normalize(final_text)
    core = _normalize(_redirect_core(redirect_text))
    if core and core in norm_final:
        return {"survived": True, "method": "verbatim", "score": 1.0}

    if embed_fn is not None:
        score = _max_window_cosine(final_text, redirect_text, embed_fn)
        if score is not None and score >= threshold:
            return {"survived": True, "method": "cosine", "score": score}
        return {"survived": False, "method": "cosine", "score": score}

    return {"survived": False, "method": "verbatim", "score": 0.0}


def _max_window_cosine(final_text: str, redirect_text: str, embed_fn,
                       window_chars: int = 600, stride_chars: int = 300):
    """Embed the redirect and sliding windows of the final text; return the
    max cosine. ``embed_fn(list[str]) -> list[list[float]]``."""
    import numpy as np
    windows = []
    i = 0
    while i < len(final_text):
        windows.append(final_text[i:i + window_chars])
        i += stride_chars
    if not windows:
        return None
    try:
        vecs = embed_fn([redirect_text] + windows)
    except Exception as exc:
        log.warning("embed_fn failed in survival cosine: %s", exc)
        return None
    arr = np.asarray(vecs, dtype=float)
    r = arr[0]
    W = arr[1:]
    rn = r / (np.linalg.norm(r) + 1e-9)
    Wn = W / (np.linalg.norm(W, axis=1, keepdims=True) + 1e-9)
    sims = Wn @ rn
    return float(sims.max()) if len(sims) else None


# ---------------------------------------------------------------------------
# final-state rendering for the compliance judge
# ---------------------------------------------------------------------------

def render_final_state(sandbox, steps, post_inject_only: bool = True,
                       max_file_chars: int = 2000) -> str:
    """Render the agent's final working tree (file contents) + the
    post-injection tool trace, for the compliance judge."""
    from src.experiments.agentic.sandbox import Sandbox
    parts: list[str] = ["FILES:"]
    root_resolved = sandbox.root.resolve()
    for p in sorted(sandbox.root.rglob("*")):
        if not p.is_file():
            continue
        try:
            rel = p.resolve().relative_to(root_resolved)
        except ValueError:
            continue
        if str(rel).startswith("_oracle_"):
            continue
        try:
            body = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        parts.append(f"--- {rel} ---\n{body[:max_file_chars]}")
    # tool trace
    inject_idx = next((i for i, s in enumerate(steps) if s.injected), None)
    trace_steps = steps[inject_idx:] if (post_inject_only and inject_idx is not None) else steps
    parts.append("\nPOST-REDIRECT ACTIONS:" if inject_idx is not None else "\nACTIONS:")
    for s in trace_steps:
        calls = ", ".join(c["typed"] for c in s.tool_calls) or "(no tool call)"
        parts.append(f"  step {s.step}: {calls}  | {s.reasoning_text[:120]}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# per-run endpoint bundle
# ---------------------------------------------------------------------------

@dataclass
class Endpoints:
    task_pass: bool
    survived: bool
    survival_method: str
    survival_score: float | None
    complied: bool | None        # None when not judged (sampling)
    compliance_reason: str | None
    oracle_detail: str
