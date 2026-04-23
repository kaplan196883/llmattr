from __future__ import annotations

import numpy as np

from src.analysis.recurrence import RecurrenceStats, recurrence_for_trajectory


def late_recurrence_for_trajectory(
    points: np.ndarray,
    steps: np.ndarray | None = None,
    start_step: int | None = None,
    start_fraction: float = 0.7,
    epsilon: float = 0.15,
    tau: int = 3,
    metric: str = "cosine",
) -> RecurrenceStats:
    """
    Recurrence restricted to late-time subset. Two ways to specify the cutoff:

    - `start_step` (absolute): only use steps >= start_step.
    - `start_fraction` (relative): only use the last (1 - start_fraction) of points
      if `start_step` is None.

    When `steps` is None we treat the array index as the step number.
    """
    n = len(points)
    if n == 0:
        return RecurrenceStats(0, 0.0, None, None, 0)

    if steps is None:
        steps_arr = np.arange(n)
    else:
        steps_arr = np.asarray(steps)

    T = int(steps_arr.max()) + 1 if n else 0
    if start_step is None:
        cutoff = int(round(start_fraction * T))
    else:
        cutoff = int(start_step)

    mask = steps_arr >= cutoff
    if mask.sum() < 2:
        return RecurrenceStats(0, 0.0, None, None, int(mask.sum()))

    return recurrence_for_trajectory(
        points[mask],
        epsilon=epsilon,
        tau=tau,
        metric=metric,
    )
