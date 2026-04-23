from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ContextState:
    text: str
    step: int
    length_chars: int
    clip_rule: str

    @classmethod
    def initial(cls, text: str, clip_rule: str = "tail_chars") -> "ContextState":
        return cls(text=text, step=0, length_chars=len(text), clip_rule=clip_rule)


def clip_context(text: str, max_chars: int, rule: str = "tail_chars") -> str:
    """Deterministic bounded-context clip. Currently: tail_chars only."""
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    if rule == "tail_chars":
        return text[-max_chars:]
    if rule == "strict_stop":
        # signal to caller by raising; runner handles early termination
        raise ContextOverflow(f"context length {len(text)} exceeds max {max_chars}")
    raise ValueError(f"unknown clip rule: {rule}")


def append_only_update(
    context_text: str, output_text: str, max_chars: int, rule: str = "tail_chars"
) -> str:
    return clip_context(context_text + output_text, max_chars, rule)


class ContextOverflow(RuntimeError):
    pass
