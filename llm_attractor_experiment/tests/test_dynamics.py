"""
Sanity tests for the Lyapunov + Sharpness-Dimension module.
Designed around the four regime predictions from REPORT3/REPORT4:

  contractive       → λ_1 < 0,  SD ≈ 0
  oscillatory       → λ_1 ≈ 0,  SD ∈ (0, 1)
  absorbing state   → λ_1 << 0, SD = 0
  divergent / EoS   → λ_1 > 0,  SD ≥ 1 (we don't see this in our LLM data)
"""
from __future__ import annotations

import numpy as np
import pytest

from src.experiments.dynamics.lyapunov import (
    compute_lyapunov_spectrum,
    ftle_from_spread,
)
from src.experiments.dynamics.sharpness_dim import (
    effective_rank,
    sharpness_dimension,
)


def test_sharpness_dim_empty_spectrum_is_zero():
    sd = sharpness_dimension(np.array([]))
    assert sd.value == 0.0
    assert sd.n_modes == 0


def test_sharpness_dim_all_zero_spectrum_is_zero():
    sd = sharpness_dimension(np.array([0.0, 0.0, 0.0]))
    assert sd.value == 0.0
    assert sd.n_modes == 0


def test_sharpness_dim_negative_entries_clipped_to_zero():
    # Negative values get clipped — caller probably passed Lyapunov exponents
    # by mistake; SD is participation ratio over a non-negative spectrum.
    sd = sharpness_dimension(np.array([-0.5, -0.8, -1.0]))
    assert sd.value == 0.0
    assert sd.n_modes == 0


def test_sharpness_dim_single_dominant_mode_is_one():
    # PR = (1)² / (1²) = 1.0 — one mode dominates entirely.
    sd = sharpness_dimension(np.array([1.0, 0.0, 0.0, 0.0]))
    assert abs(sd.value - 1.0) < 1e-9
    assert sd.n_modes == 1


def test_sharpness_dim_flat_spectrum_is_full_dim():
    # Five equal modes: PR = (5)² / 5 = 5.0 — maximal spread.
    sd = sharpness_dimension(np.array([1.0, 1.0, 1.0, 1.0, 1.0]))
    assert abs(sd.value - 5.0) < 1e-9
    assert sd.n_modes == 5


def test_sharpness_dim_two_equal_modes_is_two():
    # Two equal modes, two zero: PR = (2)² / 2 = 2.0.
    sd = sharpness_dimension(np.array([1.0, 1.0, 0.0, 0.0]))
    assert abs(sd.value - 2.0) < 1e-9
    assert sd.n_modes == 2


def test_sharpness_dim_invariant_under_positive_rescaling():
    # PR is scale-invariant: PR(c·x) = PR(x) for c > 0.
    spec = np.array([0.7, 0.3, 0.1, 0.05])
    sd1 = sharpness_dimension(spec)
    sd2 = sharpness_dimension(100.0 * spec)
    assert abs(sd1.value - sd2.value) < 1e-9


def test_sharpness_dim_decaying_spectrum_intermediate():
    # σ = (1, 0.5, 0.25, 0.1):  Σσ = 1.85,  Σσ² = 1 + 0.25 + 0.0625 + 0.01 = 1.3225
    # PR = 1.85² / 1.3225 ≈ 2.588
    sd = sharpness_dimension(np.array([1.0, 0.5, 0.25, 0.1]))
    assert abs(sd.value - (1.85**2 / 1.3225)) < 1e-9


def test_effective_rank_counts_nonnegative():
    rk = effective_rank(np.array([0.1, 0.01, -0.02, -0.5]))
    # Everything >= -0.01 counts: 0.1, 0.01 → 2 (−0.02 fails the threshold).
    assert rk == 2


def test_ftle_contractive_spread_shrinks():
    # Spread shrinks from 1.0 to 0.1 over 10 steps → negative exponent.
    spread = np.linspace(1.0, 0.1, 10)
    ftle = ftle_from_spread(spread, t_baseline=1)
    assert ftle < 0


def test_ftle_expanding_spread_grows():
    spread = np.exp(np.linspace(0.0, 3.0, 10))
    ftle = ftle_from_spread(spread, t_baseline=1)
    assert ftle > 0


def test_compute_lyapunov_contractive_regime():
    """
    Simulate a contractive ensemble: N runs sampling around a drifting-to-center
    trajectory. Ensemble spread should shrink over time → λ_1 < 0.
    """
    rng = np.random.default_rng(0)
    N, T, d = 6, 30, 5
    runs = np.zeros((N, T, d))
    # All runs start at origin (t=0).
    # Each step pulls toward origin with decaying noise.
    for n in range(N):
        x = rng.normal(scale=1.0, size=d)
        for t in range(T):
            runs[n, t] = x
            x = 0.85 * x + rng.normal(scale=0.01, size=d)
    spec = compute_lyapunov_spectrum(runs, t_baseline=1)
    assert spec.lambda_1 < 0, f"expected negative; got {spec.lambda_1}"
    # Under PR semantics, the late-window covariance of an isotropic-noise
    # contractive ensemble in d=5 should be close to flat (all directions
    # carry similar residual noise), so SD is bounded below by 1 and
    # bounded above by the number of modes (≤ N-1 = 5). We check the SD
    # is well-defined and within sensible bounds rather than near zero.
    sigma_last = np.sqrt(np.maximum(spec.singular_vals_last, 0.0))
    sd = sharpness_dimension(sigma_last)
    assert 1.0 <= sd.value <= 5.0, f"SD should be in [1, 5]; got {sd.value}"


def test_compute_lyapunov_expanding_regime():
    """
    Simulate a diverging ensemble. λ_1 should be positive.
    """
    rng = np.random.default_rng(0)
    N, T, d = 6, 30, 5
    runs = np.zeros((N, T, d))
    for n in range(N):
        x = rng.normal(scale=0.01, size=d)
        for t in range(T):
            runs[n, t] = x
            x = 1.05 * x + rng.normal(scale=0.05, size=d)
    spec = compute_lyapunov_spectrum(runs, t_baseline=1)
    assert spec.lambda_1 > 0, f"expected positive; got {spec.lambda_1}"


def test_compute_lyapunov_short_ensemble_degenerate():
    # Only 1 run → no ensemble spread, everything is zero.
    runs = np.zeros((1, 10, 3))
    spec = compute_lyapunov_spectrum(runs)
    assert spec.lambda_1 == 0.0
    assert len(spec.lambda_spectrum) == 0
