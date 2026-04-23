"""
Role-separated observables for two-agent dialogs.

For a dialog with alternating roles, we often want to embed:
- only the user's utterances (ignoring agent replies)
- only the agent's utterances
- the most recent (user, agent) exchange as a paired unit
- a rolling window within a single role

Each builder produces one string per step of the base trajectory (matching the
length of `steps`). At steps where the matching role hasn't spoken yet, we fall
back to the seed utterance (or a placeholder). At steps where the current role
doesn't match, we repeat the most recent matching turn — this means consecutive
"non-matching" steps produce identical strings. That's fine: periodicity metrics
measuring distance in this derived space will see lag-1 distance = 0 at
non-matching steps, which is a *feature* (it makes the alternation structure
visible rather than confounding).

Isolated from the shared observable module to preserve backward compatibility.
"""
from __future__ import annotations

import re
from typing import Callable

from src.core.observables import ROLLING_SEP, build_all_for_run

_ROLE_ROLLING_RE = re.compile(r"^rolling_(user|agent)(?:_k(\d+))?$")


def _turns_at_or_before(steps: list[dict], t: int, role_filter: str) -> list[dict]:
    return [s for s in steps[: t + 1] if s.get("role") == role_filter]


def observable_last_user_turn(steps: list[dict], t: int, fallback: str = "") -> str:
    turns = _turns_at_or_before(steps, t, "user")
    return turns[-1]["output_text"] if turns else fallback


def observable_last_agent_turn(steps: list[dict], t: int, fallback: str = "") -> str:
    turns = _turns_at_or_before(steps, t, "agent")
    return turns[-1]["output_text"] if turns else fallback


def observable_rolling_role(
    steps: list[dict],
    t: int,
    role_filter: str,
    k: int = 3,
    sep: str = ROLLING_SEP,
    fallback: str = "",
) -> str:
    turns = _turns_at_or_before(steps, t, role_filter)[-k:]
    if not turns:
        return fallback
    return sep.join(s["output_text"] for s in turns)


def observable_turn_pair(steps: list[dict], t: int, fallback: str = "") -> str:
    """Most recent user turn and most recent agent turn, formatted as a paired unit."""
    u = _turns_at_or_before(steps, t, "user")
    a = _turns_at_or_before(steps, t, "agent")
    u_text = u[-1]["output_text"] if u else ""
    a_text = a[-1]["output_text"] if a else ""
    if not u_text and not a_text:
        return fallback
    return f"[User]: {u_text}\n\n[Agent]: {a_text}"


def build_dialog_observables(
    steps: list[dict],
    observable_types: list[str],
    k: int = 3,
    tail_chars: int = 4000,
    full_chars: int = 8000,
    seed_utterance: str = "",
) -> dict[str, list[str]]:
    """
    Build all requested observables for one dialog run.

    Recognizes:
    - the generic names supported by src.core.observables.build_all_for_run
      (`output`, `rolling` / `rolling_k{N}`, `context_tail`, `context_full`)
    - `last_user_turn`, `last_agent_turn`
    - `rolling_user` / `rolling_user_k{N}`
    - `rolling_agent` / `rolling_agent_k{N}`
    - `turn_pair`
    """
    out: dict[str, list[str]] = {}

    base_names: list[str] = []
    extras: list[str] = []
    for name in observable_types:
        if name in ("last_user_turn", "last_agent_turn", "turn_pair"):
            extras.append(name)
        elif _ROLE_ROLLING_RE.match(name):
            extras.append(name)
        else:
            base_names.append(name)

    if base_names:
        base_out = build_all_for_run(
            steps, base_names, k=k, tail_chars=tail_chars, full_chars=full_chars
        )
        out.update(base_out)

    n = len(steps)
    for name in extras:
        if name == "last_user_turn":
            out[name] = [
                observable_last_user_turn(steps, t, fallback=seed_utterance)
                for t in range(n)
            ]
        elif name == "last_agent_turn":
            out[name] = [
                observable_last_agent_turn(steps, t, fallback=seed_utterance)
                for t in range(n)
            ]
        elif name == "turn_pair":
            out[name] = [
                observable_turn_pair(steps, t, fallback=seed_utterance)
                for t in range(n)
            ]
        else:
            m = _ROLE_ROLLING_RE.match(name)
            if not m:
                raise ValueError(f"unknown dialog observable: {name}")
            role_filter = m.group(1)
            k_used = int(m.group(2)) if m.group(2) else k
            out[name] = [
                observable_rolling_role(
                    steps, t, role_filter, k=k_used, fallback=seed_utterance
                )
                for t in range(n)
            ]
    return out


__all__ = [
    "observable_last_user_turn",
    "observable_last_agent_turn",
    "observable_rolling_role",
    "observable_turn_pair",
    "build_dialog_observables",
]
