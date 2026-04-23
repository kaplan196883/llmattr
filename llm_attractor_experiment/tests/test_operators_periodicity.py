import numpy as np

from src.experiments.operators.periodicity import trajectory_periodicity


def test_period_2_detected_for_2cycle():
    # Strict 2-cycle: alternate between two unit-length points.
    a = np.array([1.0, 0.0])
    b = np.array([0.0, 1.0])
    pts = np.array([a if i % 2 == 0 else b for i in range(20)], dtype=np.float32)
    res = trajectory_periodicity(pts, metric="cosine")
    # At lag 1: distance ~1.0 (orthogonal). At lag 2: distance ~0.0 (same point).
    # period_2_score = dist(lag=1) - dist(lag=2) → strongly positive.
    assert res.period_2_score > 0.5
    assert res.best_period == 2


def test_period_fixed_point():
    # All identical points. All pairwise distances zero → no periodicity signature.
    pts = np.ones((20, 3), dtype=np.float32)
    res = trajectory_periodicity(pts, metric="cosine")
    assert abs(res.period_2_score) < 1e-6


def test_drifting_trajectory_no_orbit():
    # Points drifting linearly outward.
    pts = np.array([[i, 0.0] for i in range(20)], dtype=np.float32)
    res = trajectory_periodicity(pts, metric="euclidean")
    # lag-1 distance is smallest (consecutive points closest),
    # so period_2_score should be NEGATIVE (distant lags are larger).
    assert res.period_2_score < 0


def test_short_trajectory_returns_zero():
    pts = np.zeros((2, 2), dtype=np.float32)
    res = trajectory_periodicity(pts)
    assert res.best_period is None
