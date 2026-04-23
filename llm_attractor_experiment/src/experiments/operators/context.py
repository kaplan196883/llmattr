"""
Isolated context-update module for the operator experiments.

Adds a `loop_mode` parameter that the base src/core/context.py does not have.
Kept separate so the original experiments (exp_default, exp_long, exp_noclip)
can be rerun against the unmodified shared code.
"""
from __future__ import annotations

from src.core.context import clip_context  # reuse shared clip logic unchanged


def update_context(
    context_text: str,
    output_text: str,
    max_chars: int,
    rule: str = "tail_chars",
    loop_mode: str = "append",
) -> str:
    """
    loop_mode='append'  → X_{t+1} = clip(X_t || Y_t)  (accumulate history)
    loop_mode='replace' → X_{t+1} = clip(Y_t)         (total replacement — paraphrase loop)
    """
    if loop_mode == "replace":
        return clip_context(output_text, max_chars, rule)
    if loop_mode == "append":
        return clip_context(context_text + output_text, max_chars, rule)
    raise ValueError(f"unknown loop_mode: {loop_mode}")
