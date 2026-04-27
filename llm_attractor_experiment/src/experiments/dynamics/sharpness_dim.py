"""
Sharpness Dimension (SD) — participation ratio of an ensemble singular-value
spectrum, used as an effective-dimension diagnostic for the on-attractor
geometry. See ARTICLE.md §4.5.6 for the spec.

DEFINITION
----------
For a non-negative spectrum σ_1 ≥ σ_2 ≥ ... ≥ σ_d ≥ 0,

    SD = (Σ_k σ_k)² / Σ_k σ_k²

Two anchoring cases:
- spectrum dominated by one mode (`σ_1 ≫ σ_2`):  SD → 1   (collapsed)
- spectrum perfectly flat (`σ_1 = ... = σ_d`):   SD = d   (maximally spread)

PR is invariant under multiplicative rescaling, so it does not depend on the
absolute magnitude of the singular values, only on their *relative shape*.

INPUTS
------
The expected input is the singular-value spectrum of the centered ensemble
matrix at a fixed step t (or, equivalently, sqrt of the covariance
eigenvalues — the multiplicative √N factor drops out under PR but the
*square* does not). Callers should pass actual singular values, not
covariance eigenvalues, to match the article's definition.

Negative entries (which can arise if a caller passes finite-time Lyapunov
exponents by mistake) are clipped to zero rather than silently
producing nonsense; the PR formula assumes non-negative inputs.

WHY NOT TUCI ET AL.'S DEFINITION
--------------------------------
An earlier version of this module implemented Definition 4.2 of
Tuci et al. (arXiv:2604.19740) — `j* + Σ_{k≤j*}λ_k / |λ_{j*+1}|` over
Lyapunov exponents. That formula is anchored to a generalization-bound
theorem for SGD (Theorem 4.5), which has no analogue in our inference-time
setting (no training, no Hessian, no PAC-style guarantee). We replaced it
with the participation ratio so that SD is a clean, citation-light
spectral-shape diagnostic without inheriting theoretical baggage that
doesn't transfer.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class SharpnessDimension:
    value: float            # SD = (Σ σ)² / Σ σ²
    n_modes: int            # count of strictly positive entries in the input
    spectrum_sum: float     # Σ σ_k (post-clip)
    spectrum_sumsq: float   # Σ σ_k² (post-clip)
    spectrum: np.ndarray    # the (clipped, descending) input spectrum, copied


def sharpness_dimension(spectrum: np.ndarray) -> SharpnessDimension:
    """
    Compute the participation-ratio sharpness dimension of a 1-D
    non-negative spectrum.

    Empty input → SD = 0. All-zero input → SD = 0. Otherwise SD ∈ [1, d]
    where d is the number of strictly positive entries.
    """
    spec = np.asarray(spectrum, dtype=np.float64).flatten()
    if spec.size == 0:
        return SharpnessDimension(
            value=0.0,
            n_modes=0,
            spectrum_sum=0.0,
            spectrum_sumsq=0.0,
            spectrum=spec.copy(),
        )

    # Defensive: clip negatives to zero and sort descending so callers
    # don't need to pre-process.
    spec = np.clip(spec, a_min=0.0, a_max=None)
    spec = np.sort(spec)[::-1]

    s_sum = float(spec.sum())
    s_sumsq = float((spec * spec).sum())
    n_modes = int((spec > 0).sum())

    if s_sumsq < 1e-18 or s_sum <= 0.0:
        sd_value = 0.0
    else:
        sd_value = (s_sum * s_sum) / s_sumsq

    return SharpnessDimension(
        value=sd_value,
        n_modes=n_modes,
        spectrum_sum=s_sum,
        spectrum_sumsq=s_sumsq,
        spectrum=spec.copy(),
    )


def effective_rank(spectrum: np.ndarray, threshold: float = 0.01) -> int:
    """
    Hard-count companion to SD: number of spectrum entries within `threshold`
    of zero or above. Where SD weights all directions softly via PR, effective
    rank gives a discrete count of "active" directions. See ARTICLE.md §4.5.6.

    Note: the threshold is interpreted in the same units as the input
    spectrum (e.g., singular value magnitude), not as a fraction of the
    leading mode.
    """
    spec = np.asarray(spectrum, dtype=np.float64)
    return int(np.sum(spec >= -threshold))
