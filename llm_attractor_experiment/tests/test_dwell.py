import numpy as np

from src.analysis.dwell import dwell_runs, dwell_stats_for_trajectory


def test_dwell_runs_basic():
    labels = np.array([0, 0, 1, 1, 1, 0, 2, 2, 0])
    runs = dwell_runs(labels)
    assert runs == [
        (0, 0, 2),
        (1, 2, 3),
        (0, 5, 1),
        (2, 6, 2),
        (0, 8, 1),
    ]


def test_dwell_stats_counts_reentries():
    labels = np.array([0, 0, 1, 1, 1, 0, 2, 2, 0])
    stats = dwell_stats_for_trajectory(labels)
    by_id = {s.cluster: s for s in stats}
    assert by_id[0].reentry_count == 2  # 3 visits -> 2 re-entries
    assert by_id[1].longest_dwell == 3
    assert by_id[2].mean_dwell == 2.0


def test_dwell_ignores_dbscan_noise():
    labels = np.array([-1, -1, 0, 0, -1])
    stats = dwell_stats_for_trajectory(labels)
    assert all(s.cluster != -1 for s in stats)
    assert len(stats) == 1
