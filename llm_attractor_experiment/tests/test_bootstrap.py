import numpy as np

from src.analysis.bootstrap import bootstrap_mean_ci, permutation_test_mean_diff


def test_bootstrap_ci_contains_mean():
    rng = np.random.default_rng(0)
    values = rng.normal(loc=5.0, scale=1.0, size=200)
    ci = bootstrap_mean_ci(values, n_resamples=500, confidence=0.95, seed=0)
    assert ci.n == 200
    assert ci.lo < ci.mean < ci.hi
    assert 4.5 < ci.mean < 5.5


def test_bootstrap_handles_empty():
    ci = bootstrap_mean_ci(np.array([]), n_resamples=100, confidence=0.95, seed=0)
    assert ci.n == 0
    assert np.isnan(ci.mean)


def test_permutation_detects_real_difference():
    rng = np.random.default_rng(42)
    a = rng.normal(loc=2.0, size=60)
    b = rng.normal(loc=0.0, size=60)
    res = permutation_test_mean_diff(a, b, n_resamples=500, seed=0)
    assert res["p_value"] < 0.05
    assert res["mean_diff"] > 0


def test_permutation_tolerates_no_difference():
    rng = np.random.default_rng(42)
    a = rng.normal(loc=0.0, size=80)
    b = rng.normal(loc=0.0, size=80)
    res = permutation_test_mean_diff(a, b, n_resamples=500, seed=0)
    assert res["p_value"] >= 0.05
