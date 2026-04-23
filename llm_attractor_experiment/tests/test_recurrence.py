import numpy as np

from src.analysis.recurrence import recurrence_for_trajectory, recurrence_matrix


def test_recurrence_positive_when_points_return():
    # A trajectory that oscillates between two clusters will recur.
    rng = np.random.default_rng(0)
    base_a = np.array([0.0, 0.0])
    base_b = np.array([5.0, 0.0])
    pts = []
    for t in range(20):
        center = base_a if t % 2 == 0 else base_b
        pts.append(center + rng.normal(scale=0.01, size=2))
    pts = np.array(pts, dtype=np.float32)
    stats = recurrence_for_trajectory(pts, epsilon=0.2, tau=3, metric="euclidean")
    assert stats.recurrence_count > 0
    assert stats.recurrence_rate > 0


def test_recurrence_zero_when_drifting_away():
    pts = np.array([[i * 10.0, 0.0] for i in range(10)], dtype=np.float32)
    stats = recurrence_for_trajectory(pts, epsilon=0.1, tau=2, metric="euclidean")
    assert stats.recurrence_count == 0
    assert stats.recurrence_rate == 0.0


def test_recurrence_matrix_shape():
    pts = np.random.default_rng(1).normal(size=(8, 3))
    mat = recurrence_matrix(pts, epsilon=0.5, tau=2, metric="euclidean")
    assert mat.shape == (8, 8)
