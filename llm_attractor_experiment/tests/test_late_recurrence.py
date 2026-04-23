import numpy as np

from src.analysis.late_recurrence import late_recurrence_for_trajectory


def test_late_recurrence_uses_late_subset():
    # Early points drift; late points oscillate between two close states.
    rng = np.random.default_rng(0)
    early = np.stack([np.linspace(0, 10, 10), np.zeros(10)], axis=1) + rng.normal(scale=0.01, size=(10, 2))
    late = np.stack([np.zeros(10), np.zeros(10)], axis=1) + rng.normal(scale=0.01, size=(10, 2))
    late[::2] += np.array([0.05, 0.0])
    late[1::2] += np.array([-0.05, 0.0])
    pts = np.concatenate([early, late], axis=0).astype(np.float32)
    # late-only recurrence should be much higher than global recurrence
    late_stats = late_recurrence_for_trajectory(
        pts, start_step=10, epsilon=0.2, tau=2, metric="euclidean"
    )
    global_stats = late_recurrence_for_trajectory(
        pts, start_step=0, epsilon=0.2, tau=2, metric="euclidean"
    )
    assert late_stats.recurrence_rate > global_stats.recurrence_rate


def test_late_recurrence_empty_subset():
    pts = np.random.default_rng(0).normal(size=(5, 3)).astype(np.float32)
    stats = late_recurrence_for_trajectory(pts, start_step=100, epsilon=0.2, tau=2, metric="euclidean")
    assert stats.recurrence_count == 0


def test_late_recurrence_fraction():
    pts = np.arange(20, dtype=np.float32).reshape(-1, 1)
    stats = late_recurrence_for_trajectory(pts, start_fraction=0.5, epsilon=2.0, tau=2, metric="euclidean")
    assert stats.n_points <= 10
