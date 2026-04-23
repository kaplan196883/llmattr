import numpy as np

from src.analysis.basin import basin_score_for_condition, find_target_cluster


def test_find_target_cluster_picks_late_majority():
    labels = np.array([0, 0, 0, 1, 1, 1, 1, 1])
    steps = np.arange(8)
    target = find_target_cluster(labels, steps, late_fraction=0.5)
    assert target == 1


def test_find_target_cluster_ignores_noise():
    labels = np.array([-1, -1, 0, 0, -1, 0])
    steps = np.arange(6)
    target = find_target_cluster(labels, steps, late_fraction=0.5)
    assert target == 0


def test_basin_score_fully_converged():
    runs_labels = [np.array([0, 0, 1, 1]), np.array([0, 1, 1, 1])]
    runs_steps = [np.arange(4), np.arange(4)]
    n_conv, n = basin_score_for_condition(runs_labels, runs_steps, target_cluster=1, target_step=2)
    assert (n_conv, n) == (2, 2)


def test_basin_score_partial():
    runs_labels = [
        np.array([0, 0, 0, 0]),  # never enters cluster 1
        np.array([0, 0, 1, 1]),  # converges
    ]
    runs_steps = [np.arange(4), np.arange(4)]
    n_conv, n = basin_score_for_condition(runs_labels, runs_steps, target_cluster=1, target_step=2)
    assert (n_conv, n) == (1, 2)
