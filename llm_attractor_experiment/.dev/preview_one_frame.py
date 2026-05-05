"""Render a single preview frame from the YouTube long-trajectory animation
without going through the full multi-process pipeline. Used to iterate on
visual styling fast.

Picks frame index = inject_idx + 15 (mid-perturbation hold), so the
PERTURBATION INJECTED callout is visible at full alpha and trails extend
through the canonical horizon.

Output: data/aggregated/dip_mechanism_B/preview_one_frame.png
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".dev"))

# Reuse all helpers from the main animation script
from youtube_long_trajectory_3d import (  # noqa: E402
    DATA, EXT_HOLD_FRAMES, EXT_START, INJECT_HOLD_FRAMES, INJECT_STEP,
    N_SUBSTEPS, TARGET_DOSE, W, H, DPI,
    _add_iso_meshes_to_axis, _compute_iso_meshes, _fading_trail_data,
    _frame_schedule, _load_long_trajectories, _spline_paths,
)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Line3DCollection
from sklearn.decomposition import PCA

PREVIEW_OUT = DATA / "aggregated" / "dip_mechanism_B" / "preview_one_frame.png"


def main() -> None:
    coords, _ = _load_long_trajectories(10)
    flat = coords.reshape(-1, coords.shape[-1])
    pca = PCA(n_components=3, random_state=42)
    proj_flat = pca.fit_transform(flat)
    proj = proj_flat.reshape(coords.shape[0], coords.shape[1], 3)

    pmin = proj_flat.min(axis=0)
    pmax = proj_flat.max(axis=0)
    pad = 0.08 * (pmax - pmin)
    bounds = (pmin - pad, pmax + pad)

    spline_xyz, sample_t = _spline_paths(proj, N_SUBSTEPS)
    schedule = _frame_schedule(spline_xyz.shape[1])
    meshes = _compute_iso_meshes(proj_flat, bounds)

    # Pick a frame mid-way through the perturbation hold so the callout is
    # visible at peak alpha. inject sample idx = INJECT_STEP * N_SUBSTEPS.
    inject_idx = INJECT_STEP * N_SUBSTEPS
    # Find the inject hold frames — they live right after the first phase
    # of motion ending at inject_idx
    n_phase1 = inject_idx + 1
    target_frame = n_phase1 + INJECT_HOLD_FRAMES // 2
    print(f"target frame: {target_frame} / {len(schedule)}")
    spec = schedule[target_frame]
    print(f"  spec: {spec}")

    # Render
    plt.style.use("dark_background")
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor="#0a0e1a")
    ax = fig.add_subplot(111, projection="3d", facecolor="#0a0e1a")
    try:
        ax.set_proj_type("persp", focal_length=0.35)
    except TypeError:
        ax.set_proj_type("persp")
    lo, hi = bounds
    ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(lo[2], hi[2])
    ax.set_xlabel("PC1", color="#9ba3b4", fontsize=11, labelpad=8)
    ax.set_ylabel("PC2", color="#9ba3b4", fontsize=11, labelpad=8)
    ax.set_zlabel("PC3", color="#9ba3b4", fontsize=11, labelpad=8)
    ax.tick_params(colors="#5a6577", labelsize=8)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.fill = False
        axis.pane.set_edgecolor("#1a2032")
        axis.pane.set_alpha(0.4)

    n_frames = len(schedule)
    azim = 30 + 360 * (target_frame / max(n_frames - 1, 1))
    elev = 22 + 6 * np.sin(2 * np.pi * target_frame / max(n_frames - 1, 1))
    ax.view_init(elev=elev, azim=azim)

    e = np.deg2rad(elev); a = np.deg2rad(azim)
    cam_dir = np.array([
        np.cos(e) * np.sin(a), -np.cos(e) * np.cos(a), np.sin(e),
    ], dtype=np.float64)
    box_center = 0.5 * (np.asarray(lo) + np.asarray(hi))
    box_diag = float(np.linalg.norm(np.asarray(hi) - np.asarray(lo)))
    cam_pos = box_center + cam_dir * (box_diag * 1.6)

    if meshes:
        _add_iso_meshes_to_axis(ax, meshes)

    ax.scatter(proj_flat[:, 0], proj_flat[:, 1], proj_flat[:, 2],
               c="#1f3a5e", s=3, alpha=0.10, zorder=2)

    sample_idx = spec["sample_idx"]
    end_idx = sample_idx + 1
    n_traj = spline_xyz.shape[0]
    trail_color = (1.0, 1.0, 1.0)
    yellow = np.array([1.0, 0.85, 0.20])
    pre_inject = (INJECT_STEP - 1) * N_SUBSTEPS
    inject_idx_seg = INJECT_STEP * N_SUBSTEPS
    for i in range(n_traj):
        xyz = spline_xyz[i, :end_idx]
        if end_idx >= 2:
            segs, colors = _fading_trail_data(xyz, trail_color, 0.10, 0.98)
            n_segs = len(colors)
            for seg_k in range(max(pre_inject, 0), min(inject_idx_seg, n_segs)):
                colors[seg_k, :3] = yellow
            lc = Line3DCollection(segs, colors=colors, linewidths=1.9, zorder=4)
            ax.add_collection3d(lc)
        head_xyz = spline_xyz[i, sample_idx]
        depth = float(np.linalg.norm(cam_pos - head_xyz))
        scale = float(np.clip((box_diag * 1.6) / max(depth, 1e-6), 0.55, 1.7))
        ax.plot([head_xyz[0]], [head_xyz[1]], [head_xyz[2]],
                "o", color="#ffffff", markersize=18 * scale,
                markeredgecolor="none", alpha=0.18, zorder=5)
        ax.plot([head_xyz[0]], [head_xyz[1]], [head_xyz[2]],
                "o", color="#ffffff", markersize=11 * scale,
                markeredgecolor="none", alpha=0.55, zorder=6)
        ax.plot([head_xyz[0]], [head_xyz[1]], [head_xyz[2]],
                "o", color="#ffffff", markersize=5 * scale,
                markeredgecolor="none", alpha=1.0, zorder=7)

    fig.suptitle(
        "Long-horizon recursive LLM trajectory under adversarial perturbation\n"
        f"O1 append-mode loop, dose {TARGET_DOSE} tokens, n={n_traj} trajectories",
        color="#dde3ee", fontsize=15, y=0.96,
    )
    t_now = float(sample_t[sample_idx])
    fig.text(0.04, 0.92, f"step  t = {t_now:5.2f} / 79",
             color="#dde3ee", fontsize=14, family="monospace", weight="bold")
    fig.text(0.04, 0.05, "canonical 30-step horizon (paper §5.1.3)",
             color="#9ba3b4", fontsize=12, family="monospace")
    fig.text(0.5, 0.10, "PERTURBATION INJECTED  (the nudge)",
             color="#ff5a3d", fontsize=20, ha="center",
             weight="bold", alpha=spec.get("alpha", 1.0))

    fig.savefig(PREVIEW_OUT, dpi=DPI, facecolor="#0a0e1a")
    plt.close(fig)
    sz_kb = PREVIEW_OUT.stat().st_size / 1024
    print(f"wrote {PREVIEW_OUT}  ({sz_kb:.0f} KB)")


if __name__ == "__main__":
    main()
