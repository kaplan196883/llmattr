import numpy as np

from src.analysis.exit_return import exit_return_for_trajectory


def test_exit_return_counts_exits_and_returns():
    # Target cluster = 1. Pattern: 0,1,1,0,0,1,0,1,1,1
    labels = np.array([0, 1, 1, 0, 0, 1, 0, 1, 1, 1])
    stats = exit_return_for_trajectory(labels, target_cluster=1)
    # visits (contiguous runs of 1): indices 1-2, 5-5, 7-9 → 3 visits
    assert stats.n_visits == 3
    # exits (1→0 transitions): after index 2 (→ index 3), after index 5 (→ index 6) → 2 exits
    assert stats.n_exits == 2
    # returns: both exits eventually return → 2
    assert stats.n_returns == 2
    assert stats.return_probability == 1.0
    assert stats.total_time_in_target == 6


def test_exit_return_zero_if_never_enters():
    labels = np.array([0, 0, 0, 0])
    stats = exit_return_for_trajectory(labels, target_cluster=1)
    assert stats.n_visits == 0
    assert stats.n_exits == 0
    assert stats.return_probability == 0.0


def test_exit_return_start_step_filter():
    labels = np.array([1, 1, 0, 1, 0, 1])
    steps = np.arange(6)
    # With start_step=3, filtered labels = [1, 0, 1] → visits: 2, exits: 1, returns: 1
    stats = exit_return_for_trajectory(labels, target_cluster=1, steps=steps, start_step=3)
    assert stats.n_points_considered == 3
    assert stats.n_visits == 2
    assert stats.n_exits == 1
    assert stats.n_returns == 1


def test_exit_return_no_return_after_final_exit():
    labels = np.array([1, 1, 0, 0])
    stats = exit_return_for_trajectory(labels, target_cluster=1)
    assert stats.n_exits == 1
    assert stats.n_returns == 0
    assert stats.return_probability == 0.0
