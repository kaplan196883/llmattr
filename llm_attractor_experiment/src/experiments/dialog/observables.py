"""
Role-separated observables for two-agent dialogs.

For a dialog with alternating roles, we often want to embed:
- only role-A's utterances (ignoring role-B replies)
- only role-B's utterances
- the most recent (A, B) exchange as a paired unit
- a rolling window within a single role

Observable names are formed from the configured role names, e.g.
`last_user_turn`, `rolling_agent_k3` for D1 (`role_a=user`, `role_b=agent`),
or `last_explorer_turn`, `rolling_expert_k3` for D2 (`role_a=explorer`,
`role_b=expert`). Role names that are not configured produce a
ValueError so that mistyped observables are caught loudly rather than
silently falling back to the seed utterance.

Each builder produces one string per step of the base trajectory (matching
the length of `steps`). At steps where the matching role hasn't spoken yet,
we fall back to the seed utterance (or a placeholder). At steps where the
current role doesn't match, we repeat the most recent matching turn —
consecutive "non-matching" steps therefore produce identical strings,
which is a *feature* (it makes the alternation structure visible rather
than confounding).

See ARTICLE.md §4.3 for the role-aware observable contract.
"""
from __future__ import annotations

import re
from typing import Callable

from src.core.observables import ROLLING_SEP, build_all_for_run


def _turns_at_or_before(steps: list[dict], t: int, role_filter: str) -> list[dict]:
    return [s for s in steps[: t + 1] if s.get("role") == role_filter]


def observable_last_role_turn(
    steps: list[dict], t: int, role_name: str, fallback: str = ""
) -> str:
    """Return the most recent utterance by `role_name` at or before step t."""
    turns = _turns_at_or_before(steps, t, role_name)
    return turns[-1]["output_text"] if turns else fallback


def observable_last_user_turn(steps: list[dict], t: int, fallback: str = "") -> str:
    """Backward-compat shim for D1-style configs (role_a.name == 'user')."""
    return observable_last_role_turn(steps, t, "user", fallback=fallback)


def observable_last_agent_turn(steps: list[dict], t: int, fallback: str = "") -> str:
    """Backward-compat shim for D1-style configs (role_b.name == 'agent')."""
    return observable_last_role_turn(steps, t, "agent", fallback=fallback)


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


def observable_turn_pair(
    steps: list[dict],
    t: int,
    role_a_name: str = "user",
    role_b_name: str = "agent",
    fallback: str = "",
) -> str:
    """Most recent role_a turn and role_b turn, formatted as a paired unit."""
    a = _turns_at_or_before(steps, t, role_a_name)
    b = _turns_at_or_before(steps, t, role_b_name)
    a_text = a[-1]["output_text"] if a else ""
    b_text = b[-1]["output_text"] if b else ""
    if not a_text and not b_text:
        return fallback
    return f"[{role_a_name.title()}]: {a_text}\n\n[{role_b_name.title()}]: {b_text}"


def build_dialog_observables(
    steps: list[dict],
    observable_types: list[str],
    role_a_name: str = "user",
    role_b_name: str = "agent",
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
    - `last_<role_a_name>_turn`, `last_<role_b_name>_turn`
    - `rolling_<role_a_name>` / `rolling_<role_a_name>_k{N}`
    - `rolling_<role_b_name>` / `rolling_<role_b_name>_k{N}`
    - `turn_pair`

    Defaults preserve D1-era behavior (role_a=user, role_b=agent).
    """
    role_names = (role_a_name, role_b_name)
    last_turn_names = {f"last_{r}_turn" for r in role_names}
    role_alts = "|".join(re.escape(r) for r in role_names)
    role_rolling_re = re.compile(rf"^rolling_({role_alts})(?:_k(\d+))?$")

    out: dict[str, list[str]] = {}

    base_names: list[str] = []
    extras: list[str] = []
    for name in observable_types:
        if name in last_turn_names or name == "turn_pair":
            extras.append(name)
        elif role_rolling_re.match(name):
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
        if name == "turn_pair":
            out[name] = [
                observable_turn_pair(
                    steps, t, role_a_name, role_b_name, fallback=seed_utterance
                )
                for t in range(n)
            ]
        elif name in last_turn_names:
            role_name = name[len("last_") : -len("_turn")]
            out[name] = [
                observable_last_role_turn(
                    steps, t, role_name, fallback=seed_utterance
                )
                for t in range(n)
            ]
        else:
            m = role_rolling_re.match(name)
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
    "observable_last_role_turn",
    "observable_last_user_turn",
    "observable_last_agent_turn",
    "observable_rolling_role",
    "observable_turn_pair",
    "build_dialog_observables",
]
