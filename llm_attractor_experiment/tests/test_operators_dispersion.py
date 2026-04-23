import numpy as np

from src.experiments.operators.dispersion import trajectory_dispersion


def test_contracting_trajectory_shows_negative_growth():
    rng = np.random.default_rng(0)
    # First half is spread out, second half collapses toward origin.
    first = rng.normal(scale=3.0, size=(10, 3)).astype(np.float32)
    second = rng.normal(scale=0.05, size=(10, 3)).astype(np.float32)
    pts = np.concatenate([first, second], axis=0)
    res = trajectory_dispersion(pts, metric="euclidean")
    assert res.dispersion_growth < 0
    assert res.final_dispersion < res.initial_dispersion


def test_diverging_trajectory_shows_positive_growth():
    rng = np.random.default_rng(0)
    first = rng.normal(scale=0.05, size=(10, 3)).astype(np.float32)
    second = rng.normal(scale=3.0, size=(10, 3)).astype(np.float32)
    pts = np.concatenate([first, second], axis=0)
    res = trajectory_dispersion(pts, metric="euclidean")
    assert res.dispersion_growth > 0


def test_drift_monotonicity_high_for_linear_drift():
    pts = np.array([[i, 0.0] for i in range(20)], dtype=np.float32)
    res = trajectory_dispersion(pts, metric="euclidean")
    # Every step moves further from the start → monotonicity == 1
    assert res.drift_monotonicity > 0.95


def test_short_trajectory_safe():
    pts = np.zeros((2, 2), dtype=np.float32)
    res = trajectory_dispersion(pts)
    assert res.dispersion_growth == 0.0
