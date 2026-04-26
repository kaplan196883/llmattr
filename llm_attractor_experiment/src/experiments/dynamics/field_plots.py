"""
High-resolution vector-field visualizations for publication-scale experiments.

Per experiment, produces three field plots in each of PCA-2 and t-SNE-2 space:

  G. Streamlines + trajectory-density heatmap.
     The most legible view of "where does the recursive loop flow".
     Density (log-count per bin) is the background; smooth streamlines run
     across the whole field. Basins appear as regions streamlines curve into;
     2-cycles appear as closed curves; absorbing states as spiral sinks.

  H. Speed-colored streamlines (no background).
     Same streamlines but lines are colored by local |v|. Attractor basins
     stand out as dark/cold lines (slow flow); active transport routes as
     hot. Good for showing that late-time dynamics live on slow manifolds.

  I. Divergence field ∇·v (scalar heatmap).
     Negative divergence = sink (attractor), positive = source (repeller).
     For recursive LLM loops we expect the whole plane to be weakly negative
     with strong local minima at the observed attractors.

All plots are 300 DPI. Reuses _flow_field_for_experiment and
_flow_field_tsne_for_experiment from regime_plots.py so the underlying
binning is consistent.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.experiments.dynamics.plots import DISPLAY, REGIME_COLOR, REGIME_LABEL
from src.experiments.dynamics.regime_plots import (
    _flow_field_for_experiment,
    _flow_field_tsne_for_experiment,
)
from src.utils.io import ensure_dir
from src.utils.logging import get_logger, setup_logging

log = get_logger(__name__)


DPI = 300
FIG_SIZE = (14, 11)


def _clean_uv_for_streamplot(
    X: np.ndarray, Y: np.ndarray, U: np.ndarray, V: np.ndarray, density: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Replace NaN and low-density cells with zero so streamplot can integrate.
    Low-density cells are dropped (flow direction there is ill-estimated)."""
    min_count = 2
    U2 = np.where(~np.isnan(U) & (density >= min_count), U, 0.0)
    V2 = np.where(~np.isnan(V) & (density >= min_count), V, 0.0)
    return U2, V2


def _smooth_density_grid(
    pts: np.ndarray,
    x_bounds: tuple[float, float],
    y_bounds: tuple[float, float],
    grid_n: int = 96,
    sigma_cells: float = 1.5,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute a smoothed density grid for background rendering, separate from the
    (coarser) flow-field grid. Uses a fine 2D histogram then Gaussian-blurs it.

    Returns (X_mesh, Y_mesh, density_smoothed) where all arrays are (grid_n, grid_n).
    """
    from scipy.ndimage import gaussian_filter

    x_min, x_max = x_bounds
    y_min, y_max = y_bounds
    x_edges = np.linspace(x_min, x_max, grid_n + 1)
    y_edges = np.linspace(y_min, y_max, grid_n + 1)
    H, _, _ = np.histogram2d(pts[:, 0], pts[:, 1], bins=(x_edges, y_edges))
    H = H.T  # rows=y, cols=x
    H_smooth = gaussian_filter(H, sigma=sigma_cells, mode="nearest")
    x_c = 0.5 * (x_edges[:-1] + x_edges[1:])
    y_c = 0.5 * (y_edges[:-1] + y_edges[1:])
    X_mesh, Y_mesh = np.meshgrid(x_c, y_c)
    return X_mesh, Y_mesh, H_smooth


def _potential_grid(
    pts: np.ndarray,
    xbounds: tuple[float, float],
    ybounds: tuple[float, float],
    grid_n: int = 96,
    sigma_cells: float = 2.0,
    v_cap: float = 8.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Smoothed-density-derived effective potential V(x) = -log ρ(x).

    Returns (X, Y, V) where V is normalized so V_min=0 and capped at v_cap.
    """
    X, Y, H = _smooth_density_grid(pts, xbounds, ybounds, grid_n=grid_n, sigma_cells=sigma_cells)
    rho = H / max(H.sum(), 1.0)
    eps = max(rho[rho > 0].min(), 1e-9) * 0.1 if (rho > 0).any() else 1e-9
    V = -np.log(rho + eps)
    V = V - V.min()
    V = np.minimum(V, v_cap)
    return X, Y, V


def plot_streamlines_density(
    exp_name: str,
    result: tuple,
    out_dir: Path,
    observable: str,
    space_tag: str,  # 'pca' or 'tsne'
) -> Path:
    X, Y, U, V, density, pts = result
    U2, V2 = _clean_uv_for_streamplot(X, Y, U, V, density)
    regime = REGIME_LABEL.get(exp_name, "unknown")
    title_color = REGIME_COLOR.get(regime, "#333")

    fig, ax = plt.subplots(figsize=FIG_SIZE)
    # Background: smoothed log-density heatmap on a fine (128×128) grid
    Xd, Yd, Hs = _smooth_density_grid(
        pts,
        (X.min(), X.max()),
        (Y.min(), Y.max()),
        grid_n=128,
        sigma_cells=1.8,
    )
    im = ax.pcolormesh(
        Xd, Yd, np.log1p(Hs), cmap="magma", alpha=0.9, shading="gouraud"
    )
    cbar = fig.colorbar(im, ax=ax, pad=0.02, label="log(1 + trajectory-visit count, smoothed)")
    cbar.ax.tick_params(labelsize=10)

    # Foreground: streamlines from coarser flow-field grid
    mag = np.sqrt(U2**2 + V2**2)
    nonzero = mag > 0
    if nonzero.sum() > 10:
        strm = ax.streamplot(
            X, Y, U2, V2,
            color="white", linewidth=1.0, density=2.0, arrowsize=1.4,
            arrowstyle="-|>",
        )

    # Overlay point-cloud faintly
    ax.scatter(pts[:, 0], pts[:, 1], s=0.5, alpha=0.08, color="#cccccc", linewidths=0)

    space_label = "PCA-2" if space_tag == "pca" else "PCA-50 → t-SNE-2"
    ax.set_title(
        f"{DISPLAY.get(exp_name, exp_name)} — {regime}  "
        f"(streamlines + density, {space_label})\n"
        f"white lines = flow direction Y_t → Y_(t+1); "
        f"magma color = trajectory visit density  ({observable}, {len(pts):,} pts)",
        color=title_color, fontsize=12, pad=10,
    )
    ax.set_xlabel(f"{space_label} 1")
    ax.set_ylabel(f"{space_label} 2")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.15, color="#555")

    ensure_dir(out_dir)
    path = out_dir / f"G_streamlines_density_{space_tag}_{exp_name}_{observable}.png"
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", path)
    return path


def plot_speed_colored_streamlines(
    exp_name: str,
    result: tuple,
    out_dir: Path,
    observable: str,
    space_tag: str,
) -> Path:
    X, Y, U, V, density, pts = result
    U2, V2 = _clean_uv_for_streamplot(X, Y, U, V, density)
    regime = REGIME_LABEL.get(exp_name, "unknown")
    title_color = REGIME_COLOR.get(regime, "#333")
    mag = np.sqrt(U2**2 + V2**2)

    fig, ax = plt.subplots(figsize=FIG_SIZE, facecolor="#0a0a0a")
    ax.set_facecolor("#0a0a0a")

    if (mag > 0).sum() > 10:
        # Streamplot expects color as a 2D array same shape as U, V
        strm = ax.streamplot(
            X, Y, U2, V2,
            color=mag, cmap="plasma", linewidth=1.4, density=2.4,
            arrowsize=1.4, arrowstyle="-|>",
        )
        cbar = fig.colorbar(
            strm.lines, ax=ax, pad=0.02,
            label=f"local |velocity| (per-step displacement in {space_tag}-2)",
        )
        cbar.ax.tick_params(labelsize=10, colors="#ddd")
        cbar.ax.yaxis.label.set_color("#ddd")

    ax.scatter(pts[:, 0], pts[:, 1], s=0.8, alpha=0.10, color="#666", linewidths=0)

    space_label = "PCA-2" if space_tag == "pca" else "PCA-50 → t-SNE-2"
    for spine in ax.spines.values():
        spine.set_color("#aaa")
    ax.tick_params(colors="#bbb")
    ax.xaxis.label.set_color("#ddd")
    ax.yaxis.label.set_color("#ddd")
    ax.title.set_color("#eee")

    ax.set_title(
        f"{DISPLAY.get(exp_name, exp_name)} — {regime}  "
        f"(speed-colored streamlines, {space_label})\n"
        f"cold = slow (attractor / basin interior); warm = fast transport  "
        f"({observable}, {len(pts):,} pts)",
        color=title_color, fontsize=12, pad=10,
    )
    ax.set_xlabel(f"{space_label} 1")
    ax.set_ylabel(f"{space_label} 2")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.12, color="#333")

    ensure_dir(out_dir)
    path = out_dir / f"H_speed_streamlines_{space_tag}_{exp_name}_{observable}.png"
    fig.savefig(path, dpi=DPI, bbox_inches="tight", facecolor="#0a0a0a")
    plt.close(fig)
    log.info("wrote %s", path)
    return path


def plot_divergence_field(
    exp_name: str,
    result: tuple,
    out_dir: Path,
    observable: str,
    space_tag: str,
) -> Path:
    X, Y, U, V, density, pts = result
    U2, V2 = _clean_uv_for_streamplot(X, Y, U, V, density)
    regime = REGIME_LABEL.get(exp_name, "unknown")
    title_color = REGIME_COLOR.get(regime, "#333")

    # Divergence: ∂U/∂x + ∂V/∂y via finite differences
    dx = X[0, 1] - X[0, 0]
    dy = Y[1, 0] - Y[0, 0]
    dUdx = np.gradient(U2, dx, axis=1)
    dVdy = np.gradient(V2, dy, axis=0)
    div = dUdx + dVdy

    # Mask low-density cells so we don't color noisy/empty bins
    mask = density >= 2
    div_masked = np.where(mask, div, np.nan)

    # Symmetric color scale around 0
    finite = div_masked[np.isfinite(div_masked)]
    if finite.size > 0:
        vmax = float(np.nanpercentile(np.abs(finite), 98))
    else:
        vmax = 1.0

    fig, ax = plt.subplots(figsize=FIG_SIZE)
    im = ax.pcolormesh(
        X, Y, div_masked, cmap="RdBu_r", vmin=-vmax, vmax=vmax, shading="auto"
    )
    cbar = fig.colorbar(im, ax=ax, pad=0.02, label="∇·v  (per step)")
    cbar.ax.tick_params(labelsize=10)

    # Thin streamlines overlay to show context
    if (np.sqrt(U2**2 + V2**2) > 0).sum() > 10:
        ax.streamplot(
            X, Y, U2, V2,
            color="black", linewidth=0.6, density=1.4, arrowsize=0.8,
            arrowstyle="-|>",
        )

    ax.scatter(pts[:, 0], pts[:, 1], s=0.6, alpha=0.10, color="#333", linewidths=0)

    space_label = "PCA-2" if space_tag == "pca" else "PCA-50 → t-SNE-2"
    ax.set_title(
        f"{DISPLAY.get(exp_name, exp_name)} — {regime}  "
        f"(divergence field ∇·v, {space_label})\n"
        f"blue = sink (attractor: trajectories converge here); "
        f"red = source (repeller: trajectories leave)  "
        f"({observable}, {len(pts):,} pts)",
        color=title_color, fontsize=12, pad=10,
    )
    ax.set_xlabel(f"{space_label} 1")
    ax.set_ylabel(f"{space_label} 2")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.15, color="#555")

    ensure_dir(out_dir)
    path = out_dir / f"I_divergence_{space_tag}_{exp_name}_{observable}.png"
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", path)
    return path


def _flow_field_for_family_subset(
    vecs: np.ndarray, meta, family: str, grid_n: int = 32, seed: int = 42
) -> tuple[np.ndarray, ...] | None:
    """
    Same contract as _flow_field_for_experiment but restricted to one family's
    recursive points, with a family-local PCA-2 fit so intra-family basin
    structure is visible.
    """
    from sklearn.decomposition import PCA

    mask = (meta["regime"] == "recursive") & (meta["prompt_family"] == family)
    idx = np.where(mask.values)[0]
    if len(idx) < 10:
        return None
    X = vecs[idx]
    meta_f = meta.iloc[idx].reset_index(drop=True)

    pca = PCA(n_components=2, random_state=seed)
    Z = pca.fit_transform(X)

    starts: list[np.ndarray] = []
    deltas: list[np.ndarray] = []
    for _keys, sub in meta_f.groupby(["initial_condition_id", "run_id"]):
        sub_sorted = sub.sort_values("step")
        run_idx = sub_sorted.index.to_numpy()
        z_run = Z[run_idx]
        if len(z_run) < 2:
            continue
        starts.append(z_run[:-1])
        deltas.append(z_run[1:] - z_run[:-1])
    if not starts:
        return None
    S = np.concatenate(starts, axis=0)
    D = np.concatenate(deltas, axis=0)

    x_min, x_max = Z[:, 0].min(), Z[:, 0].max()
    y_min, y_max = Z[:, 1].min(), Z[:, 1].max()
    x_pad = 0.05 * (x_max - x_min + 1e-9)
    y_pad = 0.05 * (y_max - y_min + 1e-9)
    x_edges = np.linspace(x_min - x_pad, x_max + x_pad, grid_n + 1)
    y_edges = np.linspace(y_min - y_pad, y_max + y_pad, grid_n + 1)

    ix = np.clip(np.digitize(S[:, 0], x_edges) - 1, 0, grid_n - 1)
    iy = np.clip(np.digitize(S[:, 1], y_edges) - 1, 0, grid_n - 1)
    count = np.zeros((grid_n, grid_n))
    sum_u = np.zeros((grid_n, grid_n))
    sum_v = np.zeros((grid_n, grid_n))
    for xi, yi, du, dv in zip(ix, iy, D[:, 0], D[:, 1]):
        count[yi, xi] += 1
        sum_u[yi, xi] += du
        sum_v[yi, xi] += dv
    with np.errstate(invalid="ignore", divide="ignore"):
        U = sum_u / np.where(count > 0, count, np.nan)
        V = sum_v / np.where(count > 0, count, np.nan)

    x_c = 0.5 * (x_edges[:-1] + x_edges[1:])
    y_c = 0.5 * (y_edges[:-1] + y_edges[1:])
    X_mesh, Y_mesh = np.meshgrid(x_c, y_c)

    density_ix = np.clip(np.digitize(Z[:, 0], x_edges) - 1, 0, grid_n - 1)
    density_iy = np.clip(np.digitize(Z[:, 1], y_edges) - 1, 0, grid_n - 1)
    density = np.zeros((grid_n, grid_n))
    for xi, yi in zip(density_ix, density_iy):
        density[yi, xi] += 1

    return X_mesh, Y_mesh, U, V, density, Z


def _flow_field_for_family_subset_tsne(
    vecs: np.ndarray, meta, family: str, grid_n: int = 28,
    perplexity: float = 30.0, pre_pca: int = 50, seed: int = 42,
) -> tuple[np.ndarray, ...] | None:
    """
    Same as _flow_field_for_family_subset but uses PCA-50 → t-SNE-2 instead of
    PCA-2 for projection. t-SNE better reveals non-linear basin structure.
    """
    from sklearn.decomposition import PCA
    from sklearn.manifold import TSNE

    mask = (meta["regime"] == "recursive") & (meta["prompt_family"] == family)
    idx = np.where(mask.values)[0]
    if len(idx) < 10:
        return None
    X = vecs[idx]
    meta_f = meta.iloc[idx].reset_index(drop=True)

    k = min(pre_pca, X.shape[1], len(X) - 1)
    X_prep = (
        PCA(n_components=k, random_state=seed).fit_transform(X)
        if X.shape[1] > k and k >= 2
        else X
    )
    perp = min(perplexity, max(5.0, (len(X_prep) - 1) / 4))
    Z = TSNE(
        n_components=2,
        perplexity=perp,
        init="pca",
        learning_rate="auto",
        metric="cosine",
        random_state=seed,
    ).fit_transform(X_prep)

    starts: list[np.ndarray] = []
    deltas: list[np.ndarray] = []
    for _keys, sub in meta_f.groupby(["initial_condition_id", "run_id"]):
        sub_sorted = sub.sort_values("step")
        run_idx = sub_sorted.index.to_numpy()
        z_run = Z[run_idx]
        if len(z_run) < 2:
            continue
        starts.append(z_run[:-1])
        deltas.append(z_run[1:] - z_run[:-1])
    if not starts:
        return None
    S = np.concatenate(starts, axis=0)
    D = np.concatenate(deltas, axis=0)

    x_min, x_max = Z[:, 0].min(), Z[:, 0].max()
    y_min, y_max = Z[:, 1].min(), Z[:, 1].max()
    x_pad = 0.05 * (x_max - x_min + 1e-9)
    y_pad = 0.05 * (y_max - y_min + 1e-9)
    x_edges = np.linspace(x_min - x_pad, x_max + x_pad, grid_n + 1)
    y_edges = np.linspace(y_min - y_pad, y_max + y_pad, grid_n + 1)

    ix = np.clip(np.digitize(S[:, 0], x_edges) - 1, 0, grid_n - 1)
    iy = np.clip(np.digitize(S[:, 1], y_edges) - 1, 0, grid_n - 1)
    count = np.zeros((grid_n, grid_n))
    sum_u = np.zeros((grid_n, grid_n))
    sum_v = np.zeros((grid_n, grid_n))
    for xi, yi, du, dv in zip(ix, iy, D[:, 0], D[:, 1]):
        count[yi, xi] += 1
        sum_u[yi, xi] += du
        sum_v[yi, xi] += dv
    with np.errstate(invalid="ignore", divide="ignore"):
        U = sum_u / np.where(count > 0, count, np.nan)
        V = sum_v / np.where(count > 0, count, np.nan)

    x_c = 0.5 * (x_edges[:-1] + x_edges[1:])
    y_c = 0.5 * (y_edges[:-1] + y_edges[1:])
    X_mesh, Y_mesh = np.meshgrid(x_c, y_c)

    density_ix = np.clip(np.digitize(Z[:, 0], x_edges) - 1, 0, grid_n - 1)
    density_iy = np.clip(np.digitize(Z[:, 1], y_edges) - 1, 0, grid_n - 1)
    density = np.zeros((grid_n, grid_n))
    for xi, yi in zip(density_ix, density_iy):
        density[yi, xi] += 1

    return X_mesh, Y_mesh, U, V, density, Z


def plot_per_family_field_grid_tsne(
    exp_name: str,
    data_dir: Path,
    out_dir: Path,
    observable: str = "rolling_k3",
    grid_n: int = 28,
) -> Path | None:
    """Same layout as plot_per_family_field_grid but uses family-local t-SNE."""
    from src.utils.io import load_npy, read_parquet

    vec_p = data_dir / exp_name / "embeddings" / observable / "embeddings.npy"
    meta_p = data_dir / exp_name / "embeddings" / observable / "metadata.parquet"
    if not vec_p.exists() or not meta_p.exists():
        log.warning("[%s] missing embeddings/%s", exp_name, observable)
        return None
    vecs = load_npy(vec_p)
    meta = read_parquet(meta_p)

    families = sorted(meta.loc[meta["regime"] == "recursive", "prompt_family"].unique())
    n = len(families)
    ncols = 3
    nrows = int(np.ceil(n / ncols))

    regime = REGIME_LABEL.get(exp_name, "unknown")
    title_color = REGIME_COLOR.get(regime, "#333")

    fig, axes = plt.subplots(
        nrows, ncols,
        figsize=(5.4 * ncols, 4.4 * nrows),
        squeeze=False,
    )

    for i, fam in enumerate(families):
        ax = axes[i // ncols, i % ncols]
        log.info("[%s] per-family tsne field: %s", exp_name, fam)
        result = _flow_field_for_family_subset_tsne(vecs, meta, fam, grid_n=grid_n)
        if result is None:
            ax.set_title(f"{fam}  (no data)", fontsize=9)
            ax.axis("off")
            continue
        X, Y, U, V, density, pts = result
        U2, V2 = _clean_uv_for_streamplot(X, Y, U, V, density)

        Xd, Yd, Hs = _smooth_density_grid(
            pts,
            (X.min(), X.max()),
            (Y.min(), Y.max()),
            grid_n=96,
            sigma_cells=1.5,
        )
        ax.pcolormesh(Xd, Yd, np.log1p(Hs), cmap="magma", alpha=0.9, shading="gouraud")
        if (np.sqrt(U2**2 + V2**2) > 0).sum() > 8:
            ax.streamplot(
                X, Y, U2, V2,
                color="white", linewidth=0.8, density=1.8, arrowsize=1.0,
                arrowstyle="-|>",
            )
        ax.scatter(pts[:, 0], pts[:, 1], s=0.3, alpha=0.08, color="#bbb", linewidths=0)
        ax.set_title(f"{fam}  (n={len(pts):,})", fontsize=10, pad=5)
        ax.set_xlabel("t-SNE 1", fontsize=8)
        ax.set_ylabel("t-SNE 2", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.set_aspect("equal", adjustable="box")
        ax.grid(alpha=0.12, color="#555")

    for i in range(n, nrows * ncols):
        axes[i // ncols, i % ncols].axis("off")

    fig.suptitle(
        f"{DISPLAY.get(exp_name, exp_name)} — {regime}  "
        f"(per-family streamlines + density, family-local PCA-50 → t-SNE-2)\n"
        f"each panel: one family's recursive points only; "
        f"basins visible as high-density clumps streamlines curve into  "
        f"({observable})",
        color=title_color, fontsize=13, y=1.002,
    )

    ensure_dir(out_dir)
    path = out_dir / f"J_per_family_field_tsne_{exp_name}_{observable}.png"
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", path)
    return path


def plot_per_family_field_grid(
    exp_name: str,
    data_dir: Path,
    out_dir: Path,
    observable: str = "rolling_k3",
    grid_n: int = 32,
) -> Path | None:
    """
    Grid of per-family streamlines+density field plots for one experiment.
    Each panel: one family's recursive points, family-local PCA-2, with flow
    field and streamlines. Reveals basin structure that's hidden in the
    experiment-level joint PCA-2.
    """
    from src.utils.io import load_npy, read_parquet

    vec_p = data_dir / exp_name / "embeddings" / observable / "embeddings.npy"
    meta_p = data_dir / exp_name / "embeddings" / observable / "metadata.parquet"
    if not vec_p.exists() or not meta_p.exists():
        log.warning("[%s] missing embeddings/%s", exp_name, observable)
        return None
    vecs = load_npy(vec_p)
    meta = read_parquet(meta_p)

    families = sorted(meta.loc[meta["regime"] == "recursive", "prompt_family"].unique())
    n = len(families)
    ncols = 3 if n > 6 else 3
    nrows = int(np.ceil(n / ncols))

    regime = REGIME_LABEL.get(exp_name, "unknown")
    title_color = REGIME_COLOR.get(regime, "#333")

    fig, axes = plt.subplots(
        nrows, ncols,
        figsize=(5.4 * ncols, 4.4 * nrows),
        squeeze=False,
    )

    for i, fam in enumerate(families):
        ax = axes[i // ncols, i % ncols]
        log.info("[%s] per-family field: %s", exp_name, fam)
        result = _flow_field_for_family_subset(vecs, meta, fam, grid_n=grid_n)
        if result is None:
            ax.set_title(f"{fam}  (no data)", fontsize=9)
            ax.axis("off")
            continue
        X, Y, U, V, density, pts = result
        U2, V2 = _clean_uv_for_streamplot(X, Y, U, V, density)

        # Density background: use a fine smoothed grid (96×96) for display while
        # keeping the flow field on the original coarser grid (stable averages).
        Xd, Yd, Hs = _smooth_density_grid(
            pts,
            (X.min(), X.max()),
            (Y.min(), Y.max()),
            grid_n=96,
            sigma_cells=1.5,
        )
        ax.pcolormesh(Xd, Yd, np.log1p(Hs), cmap="magma", alpha=0.9, shading="gouraud")
        # Streamlines on top (from coarser flow grid)
        if (np.sqrt(U2**2 + V2**2) > 0).sum() > 8:
            ax.streamplot(
                X, Y, U2, V2,
                color="white", linewidth=0.8, density=1.8, arrowsize=1.0,
                arrowstyle="-|>",
            )
        ax.scatter(pts[:, 0], pts[:, 1], s=0.3, alpha=0.08, color="#bbb", linewidths=0)
        ax.set_title(f"{fam}  (n={len(pts):,})", fontsize=10, pad=5)
        ax.set_xlabel("PC 1", fontsize=8)
        ax.set_ylabel("PC 2", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.set_aspect("equal", adjustable="box")
        ax.grid(alpha=0.12, color="#555")

    for i in range(n, nrows * ncols):
        axes[i // ncols, i % ncols].axis("off")

    fig.suptitle(
        f"{DISPLAY.get(exp_name, exp_name)} — {regime}  "
        f"(per-family streamlines + density, family-local PCA-2)\n"
        f"each panel: one family's recursive points only; "
        f"basins visible as high-density clumps streamlines curve into  "
        f"({observable})",
        color=title_color, fontsize=13, y=1.002,
    )

    ensure_dir(out_dir)
    path = out_dir / f"J_per_family_field_{exp_name}_{observable}.png"
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", path)
    return path


def render_all_fields_for_experiment(
    exp_name: str,
    data_dir: Path,
    out_dir: Path,
    observable: str = "rolling_k3",
    grid_n_pca: int = 48,
    grid_n_tsne: int = 40,
    skip_tsne: bool = False,
) -> list[Path]:
    paths: list[Path] = []

    # PCA-2 field
    log.info("[%s] computing PCA-2 flow field (grid=%d)", exp_name, grid_n_pca)
    pca_res = _flow_field_for_experiment(
        data_dir / exp_name, observable, grid_n=grid_n_pca
    )
    if pca_res is None:
        log.warning("[%s] no PCA flow field data available; skipping", exp_name)
    else:
        paths.append(plot_streamlines_density(exp_name, pca_res, out_dir, observable, "pca"))
        paths.append(plot_speed_colored_streamlines(exp_name, pca_res, out_dir, observable, "pca"))
        paths.append(plot_divergence_field(exp_name, pca_res, out_dir, observable, "pca"))

    # t-SNE-2 field
    if skip_tsne:
        return paths
    log.info("[%s] computing t-SNE-2 flow field (grid=%d) — slow", exp_name, grid_n_tsne)
    tsne_res = _flow_field_tsne_for_experiment(
        data_dir / exp_name, observable, grid_n=grid_n_tsne
    )
    if tsne_res is None:
        log.warning("[%s] no t-SNE flow field data available; skipping", exp_name)
    else:
        paths.append(plot_streamlines_density(exp_name, tsne_res, out_dir, observable, "tsne"))
        paths.append(plot_speed_colored_streamlines(exp_name, tsne_res, out_dir, observable, "tsne"))
        paths.append(plot_divergence_field(exp_name, tsne_res, out_dir, observable, "tsne"))
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="field_plots")
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--out-dir", default="data/pub_dynamics_plots")
    parser.add_argument("--observable", default="rolling_k3")
    parser.add_argument("--grid-n-pca", type=int, default=48)
    parser.add_argument("--grid-n-tsne", type=int, default=40)
    parser.add_argument("--skip-tsne", action="store_true")
    parser.add_argument(
        "--mode",
        choices=["global", "per-family", "per-family-tsne", "both"],
        default="global",
        help="'global' = experiment-level PCA+t-SNE field plots (G/H/I); "
             "'per-family' = family-local PCA-2 grid (J); "
             "'per-family-tsne' = family-local t-SNE-2 grid; "
             "'both' = global + per-family (not tsne, that one's slower).",
    )
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    setup_logging(args.log_level, None)

    if args.mode in ("global", "both"):
        render_all_fields_for_experiment(
            args.experiment,
            Path(args.data_dir),
            Path(args.out_dir),
            observable=args.observable,
            grid_n_pca=args.grid_n_pca,
            grid_n_tsne=args.grid_n_tsne,
            skip_tsne=args.skip_tsne,
        )
    if args.mode in ("per-family", "both"):
        plot_per_family_field_grid(
            args.experiment,
            Path(args.data_dir),
            Path(args.out_dir),
            observable=args.observable,
            grid_n=args.grid_n_pca,
        )
    if args.mode == "per-family-tsne":
        plot_per_family_field_grid_tsne(
            args.experiment,
            Path(args.data_dir),
            Path(args.out_dir),
            observable=args.observable,
            grid_n=args.grid_n_tsne,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
