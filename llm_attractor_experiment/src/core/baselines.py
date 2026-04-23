from __future__ import annotations

from typing import Callable


def no_feedback_provider() -> Callable[[int, str, str], str]:
    """
    Baseline: at every step send the original X_0 instead of the accumulated context.
    """
    def provider(step: int, current_context: str, initial_context: str) -> str:
        return initial_context
    return provider


def independent_regeneration_provider(family_prompt: str) -> Callable[[int, str, str], str]:
    """
    Baseline: every step uses the same family-level prompt, not the initial condition
    and not the accumulated context. Outputs are independent samples.
    """
    def provider(step: int, current_context: str, initial_context: str) -> str:
        return family_prompt
    return provider


# time-shuffled is a post-processing baseline: it operates on the embedded points,
# not on the generation loop. It is implemented in analysis/robustness.py as a
# transform over embedding matrices and metadata.
