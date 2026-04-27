"""
Isolated context-update module for the operator experiments.

Implements the nudge N_f from ARTICLE.md §3.1 / §4.1 for the two
non-dialog architectures. `loop_mode` is the YAML key for N_f
(alias `nudge:` is also accepted, see src/config.py).

Kept separate from src/core/context.py so the original experiments
(exp_default, exp_long, exp_noclip) can be rerun against the unmodified
shared code.
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
    Nudge N_f applied to (X_t, Y_t) to produce X_{t+1} (ARTICLE.md §3.1).

    loop_mode='append'  → N_append:  X_{t+1} = clip(X_t || f(Y_t))
    loop_mode='replace' → N_replace: X_{t+1} = clip(f(Y_t))

    The content operator f is identity here (the operator prompt that
    defines f is applied at generation time, not update time).
    """
    if loop_mode == "replace":
        return clip_context(output_text, max_chars, rule)
    if loop_mode == "append":
        return clip_context(context_text + output_text, max_chars, rule)
    raise ValueError(f"unknown loop_mode: {loop_mode}")
