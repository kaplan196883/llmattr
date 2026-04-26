"""
Sharpness Dimension (SD) — adapted from Definition 4.2 of Tuci et al.
(arXiv 2604.19740v1, "Generalization at the Edge of Stability").

ORIGINAL DEFINITION
-------------------
Given a Lyapunov spectrum λ_1 ≥ λ_2 ≥ ... ≥ λ_d of an RDS:

    j*   = max { i ∈ {1..d} : Σ_{k=1..i} λ_k ≥ 0 }    (0 if λ_1 < 0)

    SD = { 0                                     if λ_1 < 0
         { j* + (Σ_{k=1..j*} λ_k) / |λ_{j*+1}|   if 1 ≤ j* < d
         { d                                     if j* = d

Intuition: SD counts the effective number of *expanding* directions of the
dynamics on the attractor before global contraction dominates. A pure fixed-
point regime has SD = 0 (no expanding direction); a 2-cycle has SD ≈ 1 (one
neutral/periodic direction); a diffuse topic manifold has fractional SD
between 1 and the ambient dimension.

OUR SETTING
-----------
We feed SD the per-direction finite-time Lyapunov spectrum computed by
`lyapunov.compute_lyapunov_spectrum`, estimated from the inter-run ensemble
spread covariance. λ_k here is an *ensemble expansion rate* rather than a
Jacobian log-singular-value, but the mathematical form of SD is identical.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class SharpnessDimension:
    value: float            # the SD scalar
    j_star: int             # number of fully-expanding directions
    cumulative_sum: float   # Σ_{k=1..j*} λ_k
    next_lambda: float      # λ_{j*+1} (0 if j* == len(spectrum))
    spectrum: np.ndarray    # the input Lyapunov spectrum (copy), for reference


def sharpness_dimension(lambda_spectrum: np.ndarray) -> SharpnessDimension:
    spec = np.asarray(lambda_spectrum, dtype=np.float64)
    d = len(spec)
    if d == 0 or spec[0] < 0:
        return SharpnessDimension(
            value=0.0,
            j_star=0,
            cumulative_sum=0.0,
            next_lambda=0.0,
            spectrum=spec.copy(),
        )

    # Descending sort (defensive — caller is expected to pass sorted spectrum,
    # but a sort here is cheap and removes a footgun).
    spec = np.sort(spec)[::-1]

    cumsum = np.cumsum(spec)
    # j* = max i such that cumsum[i-1] >= 0 (1-indexed definition)
    nonneg_mask = cumsum >= 0
    if not nonneg_mask.any():
        return SharpnessDimension(
            value=0.0,
            j_star=0,
            cumulative_sum=0.0,
            next_lambda=0.0,
            spectrum=spec.copy(),
        )
    j_star = int(np.where(nonneg_mask)[0][-1]) + 1  # convert 0-index to 1-index

    if j_star == d:
        return SharpnessDimension(
            value=float(d),
            j_star=d,
            cumulative_sum=float(cumsum[-1]),
            next_lambda=0.0,
            spectrum=spec.copy(),
        )

    csum_j = float(cumsum[j_star - 1])
    lam_next = float(spec[j_star])  # λ_{j*+1}
    if abs(lam_next) < 1e-18:
        # Edge case: the next eigenvalue is essentially zero → attractor is
        # j*-dimensional to numerical precision.
        sd = float(j_star)
    else:
        sd = float(j_star) + csum_j / abs(lam_next)

    return SharpnessDimension(
        value=sd,
        j_star=j_star,
        cumulative_sum=csum_j,
        next_lambda=lam_next,
        spectrum=spec.copy(),
    )


def effective_rank(lambda_spectrum: np.ndarray, threshold: float = 0.01) -> int:
    """
    Heuristic companion metric: number of Lyapunov exponents in the spectrum
    that are within `threshold` of zero or above. This is NOT the paper's SD
    but a cruder upper bound useful as a sanity check when SD is noisy.
    """
    spec = np.asarray(lambda_spectrum, dtype=np.float64)
    return int(np.sum(spec >= -threshold))
