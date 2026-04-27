"""
Three baseline regimes for sanity-checking the recursive loop dynamics
(ARTICLE.md §4.6).

Two of these are *generation-time* providers used only by the operator
runners (`src/experiments/operators/`): they substitute the recursive
context-passing rule with a degenerate non-recursive one.

  - no_feedback: at every step, send the *initial* prompt X_0 instead
    of the accumulated context. Tests whether dynamics depend on the
    feedback loop or are determined by the seed.

  - independent_regeneration: every step uses the family-level system
    prompt and ignores both context and seed. Tests whether observed
    structure is just an artifact of generating from the same prompt
    repeatedly with stochasticity.

The third baseline is post-hoc and lives in
`src/analysis/robustness.py`:

  - time_shuffled: shuffle the time axis of an embedding sequence and
    recompute the metric. Tests whether observed temporal structure
    survives time-randomization.

Dialog scope
------------
Two-agent dialog experiments (`src/experiments/dialog/`) cannot run
no_feedback or independent_regeneration in a way that respects the
alternating-role structure — both providers would degenerate the
two-persona setup into single-persona regeneration. Dialog experiments
therefore use only the post-hoc time_shuffled baseline; the absence of
the other two in dialog runs is intentional, not a regression.
"""
from __future__ import annotations

from typing import Callable


def no_feedback_provider() -> Callable[[int, str, str], str]:
    """
    Baseline: at every step send the original X_0 instead of the accumulated context.
    Operator-mode only (see module docstring for dialog scope).
    """
    def provider(step: int, current_context: str, initial_context: str) -> str:
        return initial_context
    return provider


def independent_regeneration_provider(family_prompt: str) -> Callable[[int, str, str], str]:
    """
    Baseline: every step uses the same family-level prompt, not the initial
    condition and not the accumulated context. Outputs are independent
    samples. Operator-mode only (see module docstring for dialog scope).
    """
    def provider(step: int, current_context: str, initial_context: str) -> str:
        return family_prompt
    return provider


# time_shuffled is a post-processing baseline that operates on embedded
# points rather than on the generation loop; it is implemented in
# analysis/robustness.py as a transform over embedding matrices + metadata
# and is the *only* baseline available for dialog experiments.
