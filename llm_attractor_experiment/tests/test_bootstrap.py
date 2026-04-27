import numpy as np

from src.analysis.bootstrap import bootstrap_mean_ci, permutation_test_mean_diff, wilson_ci


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


# --- Wilson 95% CI ---


def test_wilson_ci_proportion_matches_observed():
    ci = wilson_ci(k=20, n=50, confidence=0.95)
    assert ci.k == 20 and ci.n == 50
    assert abs(ci.p - 0.4) < 1e-12
    # Wilson 95% CI for 20/50: roughly [0.275, 0.539]
    assert 0.26 < ci.lo < 0.30
    assert 0.51 < ci.hi < 0.56
    assert ci.lo < ci.p < ci.hi


def test_wilson_ci_handles_zero_successes():
    # Boundary case: k=0 — normal approximation collapses, but Wilson stays
    # finite and bounded above by ~3/n for small n (rule of three).
    ci = wilson_ci(k=0, n=15)
    assert ci.lo == 0.0
    assert 0.15 < ci.hi < 0.25  # Wilson 95% for 0/15 ≈ 0.205
    assert ci.p == 0.0


def test_wilson_ci_handles_full_successes():
    # Boundary: k=n.
    ci = wilson_ci(k=20, n=20)
    assert ci.hi == 1.0
    assert 0.80 < ci.lo < 0.90
    assert ci.p == 1.0


def test_wilson_ci_zero_n_returns_nans():
    ci = wilson_ci(k=0, n=0)
    assert np.isnan(ci.p)
    assert np.isnan(ci.lo)
    assert np.isnan(ci.hi)


def test_wilson_ci_narrows_with_more_data():
    narrow = wilson_ci(k=200, n=400)
    wide = wilson_ci(k=2, n=4)
    # Same observed proportion (0.5), but more data → tighter CI.
    assert (narrow.hi - narrow.lo) < (wide.hi - wide.lo)
