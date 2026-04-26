"""
Grid + displacement-field primitives shared across the dynamics and
perturbation plot modules.

This module is a leaf of the import graph (no project imports) so it
can be safely imported by both regime_plots and field_plots without
introducing cycles.
"""
from __future__ import annotations

import numpy as np


def make_grid_edges(
    bounds_pts: np.ndarray,
    grid_n: int,
    pad_frac: float = 0.05,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return (X_mesh, Y_mesh, x_edges, y_edges) covering bounds_pts with padding.

    bounds_pts: (M, 2) array used to derive [x_min, x_max] and [y_min, y_max].
    Both coordinate axes are padded by pad_frac (default 5%) of their range.
    """
    x_min, x_max = float(bounds_pts[:, 0].min()), float(bounds_pts[:, 0].max())
    y_min, y_max = float(bounds_pts[:, 1].min()), float(bounds_pts[:, 1].max())
    xpad = pad_frac * (x_max - x_min + 1e-9)
    ypad = pad_frac * (y_max - y_min + 1e-9)
    x_edges = np.linspace(x_min - xpad, x_max + xpad, grid_n + 1)
    y_edges = np.linspace(y_min - ypad, y_max + ypad, grid_n + 1)
    x_c = 0.5 * (x_edges[:-1] + x_edges[1:])
    y_c = 0.5 * (y_edges[:-1] + y_edges[1:])
    X_mesh, Y_mesh = np.meshgrid(x_c, y_c)
    return X_mesh, Y_mesh, x_edges, y_edges


def bin_displacement_field(
    starts: np.ndarray,
    deltas: np.ndarray,
    x_edges: np.ndarray,
    y_edges: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Average per-bin (du, dv) over starts on grid(x_edges, y_edges).

    Returns (U, V) of shape (grid_n, grid_n) with NaN where the bin is empty.
    """
    grid_n = len(x_edges) - 1
    ix = np.clip(np.digitize(starts[:, 0], x_edges) - 1, 0, grid_n - 1)
    iy = np.clip(np.digitize(starts[:, 1], y_edges) - 1, 0, grid_n - 1)
    count = np.zeros((grid_n, grid_n))
    sum_u = np.zeros((grid_n, grid_n))
    sum_v = np.zeros((grid_n, grid_n))
    for xi, yi, du, dv in zip(ix, iy, deltas[:, 0], deltas[:, 1]):
        count[yi, xi] += 1
        sum_u[yi, xi] += du
        sum_v[yi, xi] += dv
    with np.errstate(invalid="ignore", divide="ignore"):
        U = sum_u / np.where(count > 0, count, np.nan)
        V = sum_v / np.where(count > 0, count, np.nan)
    return U, V


def bin_density(
    pts: np.ndarray,
    x_edges: np.ndarray,
    y_edges: np.ndarray,
) -> np.ndarray:
    """Count points per bin on grid(x_edges, y_edges). Returns (grid_n, grid_n)."""
    grid_n = len(x_edges) - 1
    ix = np.clip(np.digitize(pts[:, 0], x_edges) - 1, 0, grid_n - 1)
    iy = np.clip(np.digitize(pts[:, 1], y_edges) - 1, 0, grid_n - 1)
    density = np.zeros((grid_n, grid_n))
    for xi, yi in zip(ix, iy):
        density[yi, xi] += 1
    return density
