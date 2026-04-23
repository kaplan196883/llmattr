import numpy as np

from src.analysis.basin_entry import detect_basin_entry


def test_basin_entry_detects_stable_region():
    # 5 misses, then 5 consecutive hits. Fraction of target in labels[i:]:
    #   i=0: 5/10=.50, i=1: 5/9=.56, i=2: 5/8=.625,
    #   i=3: 5/7≈.714 (first >= 0.7 → entry_step == 3).
    labels = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    steps = np.arange(10)
    res = detect_basin_entry(labels, steps, target_cluster=1, fraction_after=0.7)
    assert res.reached
    assert res.entry_step == 3


def test_basin_entry_none_when_target_never_visited():
    labels = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    steps = np.arange(10)
    res = detect_basin_entry(labels, steps, target_cluster=1, fraction_after=0.7)
    assert not res.reached
    assert res.entry_step is None


def test_basin_entry_none_when_no_stable_suffix():
    # Rare late appearances that don't satisfy the 70% threshold for any suffix
    # (target fraction is 2/15 ≈ .13 overall and every suffix is at most .50).
    labels = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0])
    steps = np.arange(15)
    res = detect_basin_entry(labels, steps, target_cluster=1, fraction_after=0.7)
    assert not res.reached


def test_basin_entry_respects_step_reordering():
    # labels given out of step order; after sorting by step: 0,0,0,0,1,1,1
    # Fractions: 3/7≈.43, 3/6=.5, 3/5=.6, 3/4=.75 ← first ≥ .7
    # so entry_step == 3 (the step number at sorted-index 3).
    labels = np.array([1, 0, 1, 0, 1, 0, 0])
    steps = np.array([4, 1, 5, 2, 6, 0, 3])
    res = detect_basin_entry(labels, steps, target_cluster=1, fraction_after=0.7)
    assert res.reached
    assert res.entry_step == 3


def test_basin_entry_returns_false_for_invalid_target():
    labels = np.array([0, 0, 0])
    res = detect_basin_entry(labels, np.arange(3), target_cluster=-1, fraction_after=0.7)
    assert not res.reached
    assert res.entry_step is None
