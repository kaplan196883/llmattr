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


def test_sharpness_dim_all_negative_spectrum_is_zero():
    sd = sharpness_dimension(np.array([-0.5, -0.8, -1.0]))
    assert sd.value == 0.0
    assert sd.j_star == 0


def test_sharpness_dim_single_neutral_direction_is_one():
    # λ_1 = 0, λ_2 = -1  →  j* = 1, SD = 1 + 0/1 = 1.0
    sd = sharpness_dimension(np.array([0.0, -1.0]))
    assert abs(sd.value - 1.0) < 1e-9
    assert sd.j_star == 1


def test_sharpness_dim_fractional():
    # λ_1 = 0.5, λ_2 = -0.2, λ_3 = -1.0
    # j* candidates: i=1 → cumsum=0.5 ≥ 0; i=2 → cumsum=0.3 ≥ 0;
    # i=3 → cumsum=-0.7 fail. j* = 2.
    # SD = 2 + 0.3/|-1.0| = 2.3
    sd = sharpness_dimension(np.array([0.5, -0.2, -1.0]))
    assert sd.j_star == 2
    assert abs(sd.value - 2.3) < 1e-9


def test_sharpness_dim_all_expanding_is_full_dim():
    sd = sharpness_dimension(np.array([1.0, 0.5, 0.2]))
    assert sd.value == 3.0
    assert sd.j_star == 3


def test_sharpness_dim_two_element_spectrum_with_negative_cumsum():
    # The actual ensemble shape we work with (N=3 runs → 2-element spectrum).
    # λ_1 = 0.05, λ_2 = -0.10 → cumsum = [0.05, -0.05]; j*=1, SD = 1 + 0.05/0.10 = 1.5
    sd = sharpness_dimension(np.array([0.05, -0.10]))
    assert sd.j_star == 1
    assert abs(sd.value - 1.5) < 1e-9


def test_sharpness_dim_zero_next_lambda_returns_j_star():
    # If λ_{j*+1} ≈ 0 we treat the attractor as exactly j*-dimensional.
    sd = sharpness_dimension(np.array([0.5, 0.0, 0.0]))
    # All cumsums ≥ 0, so j* = d = 3, SD = 3 (full).
    assert sd.j_star == 3
    assert sd.value == 3.0


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
    sd = sharpness_dimension(spec.lambda_spectrum)
    assert sd.value < 0.5, f"contractive regime should give SD near 0; got {sd.value}"


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
