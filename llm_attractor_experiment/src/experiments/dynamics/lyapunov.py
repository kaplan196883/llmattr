"""
Finite-Time Lyapunov Exponent (FTLE) and per-direction Lyapunov spectrum for
recursive LLM loops. See ARTICLE.md §4.5.5 for the spec. The functional form
is adapted from the RDS framework in Tuci et al. (arXiv 2604.19740) to our
discrete, sampling-based setting; we use the spectrum for diagnostic
comparison only and do not inherit any of Tuci et al.'s generalization
theorems.

KEY ADAPTATION
--------------
The paper defines λ_k = E[sup_w ln σ_k(Dϕ(1, ω, w))] — the expected log-
k-th-singular-value of the Jacobian of the one-step update map. Text generation
has no smooth Jacobian (outputs are discrete samples), so we substitute a
STATISTICAL ANALOG using the ENSEMBLE SPREAD across runs from the same initial
condition.

For each (family, IC) pair we have N runs. At each step t we obtain N
embeddings z_1^t, ..., z_N^t in R^d. Define the ensemble spread covariance:

    Σ_t = (1/N) Σ_i (z_i^t − z̄^t)(z_i^t − z̄^t)^T     ∈ R^{d×d}

Its eigenvalues {μ_k(t)} decompose the inter-run variance along orthogonal
directions. The per-direction finite-time Lyapunov exponent is then

    λ_k = (1/(2T)) · log(μ_k(T) / μ_k(t_0))

where t_0 > 0 is a baseline step (we use t_0 = 1 because t = 0 has zero
spread since all N runs start from the same seed). The factor 1/2 converts
variance-growth to amplitude-growth.

λ_1  (largest exponent) captures the dominant expansion/contraction rate:
    λ_1 < 0  → ensemble contracts; attractor is a basin (regimes I, III)
    λ_1 ≈ 0  → neutral; on the edge of stability
    λ_1 > 0  → ensemble diverges; chaotic / unbounded regime (never observed
               in our gpt-4o-mini experiments)

SD (Sharpness Dimension, Def. 4.2 in the paper) is computed in sharpness_dim.py
from the full Lyapunov spectrum.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.analysis.distances import pairwise_mean_distance


@dataclass
class LyapunovSpectrum:
    lambda_spectrum: np.ndarray     # (k,) per-direction finite-time Lyapunov exponents, descending
    lambda_1: float                 # largest (==lambda_spectrum[0])
    spread_trajectory: np.ndarray   # (T,) mean pairwise distance across runs at each step
    n_runs: int
    n_steps: int
    t_baseline: int
    singular_vals_first: np.ndarray # singular values of Σ_{t_baseline}
    singular_vals_last: np.ndarray  # singular values of Σ_{T-1}


def _top_covariance_eigenvalues(points: np.ndarray, k: int) -> np.ndarray:
    """
    Top-k eigenvalues of the ensemble covariance cov = C^T C / N where C is
    the centered (N, d) point matrix.

    Fast path via low-rank SVD: since rank(cov) ≤ N−1 and N ≪ d here
    (N ≈ 3–5, d = 1536), SVD C directly in O(N²·d) rather than forming the
    d×d covariance and doing O(d³) eigh. ~5000× speedup for our sizes.
    """
    if len(points) < 2:
        return np.zeros(0)
    centered = points - points.mean(axis=0, keepdims=True)
    # C is (N, d). Singular values of C^T C are s_i^2; of cov = C^T C / N
    # they are s_i^2 / N.
    s = np.linalg.svd(centered, full_matrices=False, compute_uv=False)
    eigs = (s**2) / max(1, len(points))  # descending already
    return eigs[:k]


def compute_lyapunov_spectrum(
    runs_by_step: np.ndarray,
    t_baseline: int = 1,
    spectrum_size: int = 10,
) -> LyapunovSpectrum:
    """
    Compute the finite-time Lyapunov spectrum for an ensemble of runs from
    the same initial condition.

    Args
    ----
    runs_by_step : (N, T, d) array of N runs' step-t embeddings. All runs
                   must start from the same initial condition (runs_by_step[:, 0, :]
                   should have zero variance or near-zero, as t=0 is the seed).
    t_baseline   : step at which to anchor the exponent. We default to 1
                   because t=0 has zero ensemble variance.
    spectrum_size: number of top eigenvalues to return (truncated to N-1).

    Returns
    -------
    LyapunovSpectrum
    """
    if runs_by_step.ndim != 3:
        raise ValueError(f"runs_by_step must be 3D (N, T, d); got shape {runs_by_step.shape}")
    N, T, _d = runs_by_step.shape
    if N < 2 or T < t_baseline + 2:
        return LyapunovSpectrum(
            lambda_spectrum=np.zeros(0),
            lambda_1=0.0,
            spread_trajectory=np.zeros(T),
            n_runs=N,
            n_steps=T,
            t_baseline=t_baseline,
            singular_vals_first=np.zeros(0),
            singular_vals_last=np.zeros(0),
        )

    k = min(spectrum_size, N - 1)

    eigs_base = _top_covariance_eigenvalues(runs_by_step[:, t_baseline, :], k)
    eigs_last = _top_covariance_eigenvalues(runs_by_step[:, T - 1, :], k)

    # Per-direction finite-time Lyapunov exponent (amplitude growth rate).
    # We align directions by rank (largest-to-largest) which is an approximation —
    # strictly the paper uses matched eigendirections across time, but since the
    # ensemble is small and we want a robust summary, rank-aligned is adequate.
    eps = 1e-18
    with np.errstate(divide="ignore", invalid="ignore"):
        lam = 0.5 * np.log((eigs_last + eps) / (eigs_base + eps)) / (T - 1 - t_baseline)
    # Clean up any NaNs/infs from zero-spread directions.
    lam = np.where(np.isfinite(lam), lam, 0.0)
    # Sort descending so λ_1 is the largest.
    lam_sorted = np.sort(lam)[::-1]

    spread = np.array(
        [pairwise_mean_distance(runs_by_step[:, t, :]) for t in range(T)]
    )

    return LyapunovSpectrum(
        lambda_spectrum=lam_sorted,
        lambda_1=float(lam_sorted[0]) if len(lam_sorted) > 0 else 0.0,
        spread_trajectory=spread,
        n_runs=N,
        n_steps=T,
        t_baseline=t_baseline,
        singular_vals_first=eigs_base,
        singular_vals_last=eigs_last,
    )


def ftle_from_spread(spread: np.ndarray, t_baseline: int = 1) -> float:
    """
    Scalar Lyapunov exponent from a 1D spread time-series (e.g., mean pairwise
    run-to-run distance as a function of step).

    λ = log(spread[T-1] / spread[t_baseline]) / (T - 1 - t_baseline)

    Note: uses raw distances (not squared), so no 1/2 factor.
    """
    T = len(spread)
    if T < t_baseline + 2:
        return 0.0
    a = float(spread[t_baseline])
    b = float(spread[T - 1])
    if a <= 0 or b <= 0:
        return 0.0
    return float(np.log(b / a) / (T - 1 - t_baseline))
