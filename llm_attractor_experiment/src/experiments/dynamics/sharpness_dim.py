"""
Sharpness Dimension (SD) — fractional effective dimension of an ordered
finite-time-Lyapunov spectrum, used as a regime-comparison diagnostic.
See ARTICLE.md §4.5.6 for the spec.

DEFINITION (functional form borrowed from Tuci et al., arXiv 2604.19740 Def 4.2)
--------------------------------------------------------------------------------
Given a Lyapunov spectrum λ_1 ≥ λ_2 ≥ ... ≥ λ_d:

    j*   = max { i ∈ {1..d} : Σ_{k=1..i} λ_k ≥ 0 }    (0 if λ_1 < 0)

    SD = { 0                                     if λ_1 < 0
         { j* + (Σ_{k=1..j*} λ_k) / |λ_{j*+1}|   if 1 ≤ j* < d
         { d                                     if j* = d

Intuition: SD counts the effective number of *expanding* directions of the
dynamics on the attractor before global contraction dominates. The
fractional part adds a soft interpolation: a near-neutral next direction
pushes SD toward j*+1, a sharply contracting one keeps SD near j*.

WHY THIS FORM (and not e.g. participation ratio)
------------------------------------------------
Participation ratio (Σσ)²/Σσ² over the singular-value spectrum is the
"obvious" alternative, but our ensembles have only N = 3 runs per IC, so
the covariance rank is ≤ 2 and the PR ceiling is 2. Every regime
saturates near 2.0 and the metric loses its ability to differentiate
regimes. The Tuci form uses the *ratio* of expansion to next contraction,
giving an unbounded fractional dimension that actually distinguishes
contractive (SD ~ 1.5), oscillatory (SD ~ 6), and divergent (SD ~ 4.7)
regimes in our data.

WHAT WE DO NOT INHERIT FROM TUCI
---------------------------------
Tuci et al.'s SD is anchored to a generalization-bound theorem (Th. 4.5)
for SGD optimization on parameter space. We use the *functional form*
only — our λ_k come from inter-run ensemble spread, not from a Jacobian
linearization, and we have no training, no loss landscape, and no
PAC-style bound. SD here is a comparative diagnostic across regimes, not
a complexity bound. ARTICLE.md §4.5.6 makes this caveat explicit.
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
    """
    Compute the sharpness dimension of an ordered finite-time-Lyapunov
    spectrum. See module docstring for the definition.

    Args
    ----
    lambda_spectrum : 1-D array of Lyapunov exponents. The function sorts
        descending internally, so callers don't need to pre-sort.

    Returns
    -------
    SharpnessDimension(value, j_star, cumulative_sum, next_lambda, spectrum)
    """
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

    # Defensive: caller is expected to pass sorted spectrum, but a sort
    # here is cheap and removes a footgun.
    spec = np.sort(spec)[::-1]

    cumsum = np.cumsum(spec)
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
    lam_next = float(spec[j_star])
    if abs(lam_next) < 1e-18:
        # Edge case: next eigenvalue essentially zero → attractor is
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
    Hard-count companion to SD: number of Lyapunov exponents within
    `threshold` of zero or above. Where SD weights all directions softly,
    effective rank gives a discrete count of "active" directions.
    """
    spec = np.asarray(lambda_spectrum, dtype=np.float64)
    return int(np.sum(spec >= -threshold))
