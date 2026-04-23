from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

from src.utils.io import ensure_dir, write_csv


@dataclass
class PCAResult:
    dim: int
    projection: np.ndarray  # (n, dim)
    explained_variance_ratio: np.ndarray  # (dim,)
    components: np.ndarray  # (dim, D)
    mean: np.ndarray  # (D,)


def fit_pca(embeddings: np.ndarray, dim: int) -> PCAResult:
    """
    Fit PCA jointly on all points of one observable. Do not fit per-trajectory.
    """
    if embeddings.ndim != 2:
        raise ValueError("embeddings must be a 2D (n, D) matrix")
    n, d = embeddings.shape
    target_dim = min(dim, n, d)
    if target_dim <= 0:
        raise ValueError(f"cannot fit PCA with n={n}, D={d}")
    pca = PCA(n_components=target_dim, svd_solver="auto", random_state=0)
    proj = pca.fit_transform(embeddings)
    return PCAResult(
        dim=target_dim,
        projection=proj.astype(np.float32),
        explained_variance_ratio=pca.explained_variance_ratio_.astype(np.float32),
        components=pca.components_.astype(np.float32),
        mean=pca.mean_.astype(np.float32),
    )


def save_pca_projection(
    result: PCAResult,
    metadata: pd.DataFrame,
    observable: str,
    metrics_dir: Path,
) -> Path:
    cols = [f"pc{i+1}" for i in range(result.dim)]
    df = metadata.copy().reset_index(drop=True)
    proj_df = pd.DataFrame(result.projection, columns=cols)
    out = pd.concat([df, proj_df], axis=1)
    path = metrics_dir / f"pca_{result.dim}_{observable}.csv"
    write_csv(path, out)

    evr_path = metrics_dir / f"pca_{result.dim}_{observable}_explained_variance.csv"
    write_csv(
        evr_path,
        pd.DataFrame(
            {
                "component": list(range(1, result.dim + 1)),
                "explained_variance_ratio": result.explained_variance_ratio.tolist(),
            }
        ),
    )
    return path


def save_pca_model(result: PCAResult, observable: str, metrics_dir: Path) -> Path:
    ensure_dir(metrics_dir)
    path = metrics_dir / f"pca_{result.dim}_{observable}_model.npz"
    np.savez(
        path,
        components=result.components,
        mean=result.mean,
        explained_variance_ratio=result.explained_variance_ratio,
    )
    return path
