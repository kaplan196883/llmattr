from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE


@dataclass
class TSNEResult:
    projection: np.ndarray  # (n, 2)
    perplexity: float
    random_state: int
    pre_pca_dim: int | None


def fit_tsne(
    embeddings: np.ndarray,
    perplexity: float = 30.0,
    random_state: int = 0,
    pre_pca_dim: int | None = 50,
    metric: str = "cosine",
) -> TSNEResult:
    """
    Visualization-only: PCA pre-reduction to `pre_pca_dim` (standard recipe,
    fast + noise-robust), then t-SNE to 2D. Do NOT use this space for
    recurrence/dwell/basin metrics — t-SNE distorts global distances.
    """
    if embeddings.ndim != 2:
        raise ValueError("embeddings must be (n, D)")
    n, d = embeddings.shape
    if n < 4:
        # t-SNE needs at least a handful of points; return raw 2D padding
        proj = np.zeros((n, 2), dtype=np.float32)
        proj[:, 0] = np.arange(n, dtype=np.float32)
        return TSNEResult(proj, perplexity=perplexity, random_state=random_state, pre_pca_dim=None)

    # Perplexity must be < n
    perp = float(min(perplexity, max(5, n // 4)))

    x = embeddings
    used_pca_dim: int | None = None
    if pre_pca_dim is not None and d > pre_pca_dim:
        k = min(pre_pca_dim, n - 1, d)
        if k >= 2:
            x = PCA(n_components=k, svd_solver="auto", random_state=random_state).fit_transform(x)
            used_pca_dim = k

    tsne = TSNE(
        n_components=2,
        perplexity=perp,
        init="pca",
        learning_rate="auto",
        random_state=random_state,
        metric=metric,
    )
    proj = tsne.fit_transform(x).astype(np.float32)
    return TSNEResult(
        projection=proj,
        perplexity=perp,
        random_state=random_state,
        pre_pca_dim=used_pca_dim,
    )
