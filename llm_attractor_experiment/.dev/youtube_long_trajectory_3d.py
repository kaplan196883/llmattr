"""High-res YouTube 3D animation of long-horizon adversarial trajectories
at dose 2000.

Stitches each (family, ic, run) trajectory's original 30-step path
(exp_perturb_O1_ed50_higher_noclip, steps 0-29) with its 50-step
continuation (exp_perturb_O1_ed50_higher_noclip_extended, steps 30-79)
into a single 80-step path. Picks N=10 trajectories at dose 2000, fits
joint PCA-3 across all selected points, and renders an animation that
marches the trajectory heads from step 0 to step 79 with a slow camera
rotation.

Visual design (YouTube-oriented):
  - dark navy background
  - faint background scatter of all 80x10 = 800 trajectory points
  - per-trajectory orange trail extending as time progresses
  - bright head marker on each trajectory's current step
  - PERTURBATION INJECTED callout at step 15 (the "nudge")
  - EXTENDED HORIZON callout at step 30 (where continuation begins)
  - step counter overlay
  - slow camera rotation (~1 full turn per video)

Parallelism: per-frame rendering is independent, so we spread frames
across cpu_count() worker processes (this machine: 40 cores). Each
worker writes a PNG; ffmpeg then concatenates with `-threads 0` (all
cores) for encoding. Bundled ffmpeg from imageio-ffmpeg is used directly
so PATH doesn't need to contain a system ffmpeg.

Output: data/aggregated/dip_mechanism_B/youtube_long_trajectory_3d.mp4
        1920x1080, 30 fps, libx264 + yuv420p (YouTube-compatible).

Set RES_4K = True for 3840x2160.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import imageio_ffmpeg
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mpl_toolkits.mplot3d.art3d import Line3DCollection, Poly3DCollection
from scipy.interpolate import CubicSpline
from scipy.ndimage import gaussian_filter
from skimage.measure import marching_cubes
from sklearn.decomposition import PCA

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT_PATH = DATA / "aggregated" / "dip_mechanism_B" / "youtube_long_trajectory_3d.mp4"

EXP_ORIG = "exp_perturb_O1_ed50_higher_noclip"
EXP_EXT  = "exp_perturb_O1_ed50_higher_noclip_extended"
TARGET_DOSE = 2000
TARGET_REGIME = f"adversarial_dose{TARGET_DOSE}"
N_TRAJ = 10
INJECT_STEP = 15
EXT_START = 30
TOTAL_STEPS = 80

RES_4K = False
W, H = (3840, 2160) if RES_4K else (1920, 1080)
DPI = 100
FPS = 30
N_SUBSTEPS = 6        # spline samples per integer data step → 6 frames per step
FRAMES_PER_SUBSTEP = 1
STAGGER_FRAMES = 18   # delay between successive trajectory starts (0.6 s @ 30 fps)
FADE_IN_FRAMES = 10   # gradual alpha ramp when a new trajectory enters
END_HOLD_FRAMES = 30  # 1 s settle at the final state

N_WORKERS = max(1, (os.cpu_count() or 4))


def _load_long_trajectories(n: int) -> tuple[np.ndarray, list[dict]]:
    X_orig = np.load(DATA / EXP_ORIG / "embeddings" / "context_tail" / "embeddings.npy")
    M_orig = pd.read_parquet(DATA / EXP_ORIG / "embeddings" / "context_tail" / "metadata.parquet").reset_index(drop=True)
    X_ext = np.load(DATA / EXP_EXT / "embeddings" / "context_tail" / "embeddings.npy")
    M_ext = pd.read_parquet(DATA / EXP_EXT / "embeddings" / "context_tail" / "metadata.parquet").reset_index(drop=True)

    orig_subset = M_orig[M_orig["regime"] == TARGET_REGIME]
    ext_subset = M_ext[M_ext["regime"] == TARGET_REGIME]

    orig_keys = set(orig_subset.groupby(
        ["prompt_family", "initial_condition_id", "run_id"]
    ).size().index.tolist())
    ext_keys = set(ext_subset.groupby(
        ["prompt_family", "initial_condition_id", "run_id"]
    ).size().index.tolist())
    common = sorted(orig_keys & ext_keys)
    print(f"common (fam, ic, run) keys at dose {TARGET_DOSE}: {len(common)}")

    selected: list[tuple] = []
    seen = set()
    for k in common:
        fam = k[0]
        if fam not in seen:
            selected.append(k)
            seen.add(fam)
    for k in common:
        if len(selected) >= n:
            break
        if k not in selected:
            selected.append(k)
    selected = selected[:n]
    print(f"selected {len(selected)}: {selected}")

    coords = np.zeros((len(selected), TOTAL_STEPS, X_orig.shape[1]), dtype=np.float32)
    for i, key in enumerate(selected):
        fam, ic, run = key
        # original 0..29
        rows = orig_subset[
            (orig_subset["prompt_family"] == fam)
            & (orig_subset["initial_condition_id"] == ic)
            & (orig_subset["run_id"] == run)
        ]
        for idx, row in rows.iterrows():
            s = int(row["step"])
            if 0 <= s < EXT_START:
                coords[i, s] = X_orig[idx]
        # extended 30..79
        rows = ext_subset[
            (ext_subset["prompt_family"] == fam)
            & (ext_subset["initial_condition_id"] == ic)
            & (ext_subset["run_id"] == run)
        ]
        for idx, row in rows.iterrows():
            s = int(row["step"])
            if EXT_START <= s < TOTAL_STEPS:
                coords[i, s] = X_ext[idx]
    meta_list = [{"prompt_family": k[0], "initial_condition_id": k[1], "run_id": k[2]}
                 for k in selected]
    return coords, meta_list


def _spline_paths(proj: np.ndarray, n_substeps: int) -> tuple[np.ndarray, np.ndarray]:
    """Fit a cubic spline through each trajectory's (t=0..79, xyz) points
    and sample at n_substeps per integer step.

    Returns:
      spline_xyz: shape (n_traj, n_samples, 3)  smooth positions
      sample_t:   shape (n_samples,)            float step index per sample
    """
    n_traj, n_steps, _ = proj.shape
    t_data = np.arange(n_steps, dtype=np.float64)
    n_samples = (n_steps - 1) * n_substeps + 1
    sample_t = np.linspace(0.0, n_steps - 1, n_samples, dtype=np.float64)
    out = np.zeros((n_traj, n_samples, 3), dtype=np.float32)
    for i in range(n_traj):
        cs = CubicSpline(t_data, proj[i], bc_type="natural")
        out[i] = cs(sample_t).astype(np.float32)
    return out, sample_t


def _frame_schedule(n_samples: int, n_traj: int) -> tuple[list[dict], list[int]]:
    """Build frame plan with STAGGERED trajectory entries.

    Each trajectory i starts entering the scene at frame i * STAGGER_FRAMES
    and runs its full spline (n_samples points) at one sub-step per frame
    from there. The last trajectory finishes at frame:
        (n_traj - 1) * STAGGER_FRAMES + (n_samples - 1)
    plus an END_HOLD_FRAMES tail so the final state lingers.

    Returns:
      frames: list of dicts with keys {"animation_frame": int}
      start_offsets: per-trajectory start frame (length n_traj)
    """
    start_offsets = [i * STAGGER_FRAMES for i in range(n_traj)]
    last_traj_end = start_offsets[-1] + (n_samples - 1)
    total = last_traj_end + 1 + END_HOLD_FRAMES
    return ([{"animation_frame": f} for f in range(total)], start_offsets)


def _compute_iso_meshes(
    pts: np.ndarray,
    bounds: tuple[np.ndarray, np.ndarray],
    grid_n: int = 56,
    sigma: float = 1.6,
    levels_frac: tuple[float, ...] = (0.04, 0.10, 0.20, 0.35, 0.55),
    cmap_name: str = "plasma",
) -> list[dict]:
    """Compute layered iso-surface meshes from the cloud's 3D density.

    Mirrors src/experiments/perturbation/trajectory_animation_3d.py so the
    YouTube version uses the same gel-cloud aesthetic. Each level is a
    semi-transparent shell of the density histogram (gaussian-smoothed,
    marching-cubes extracted). Returns a list of dicts ordered outer-to-
    inner so the renderer can layer them with increasing alpha.
    """
    lo, hi = bounds
    xb, yb, zb = (lo[0], hi[0]), (lo[1], hi[1]), (lo[2], hi[2])
    x_edges = np.linspace(*xb, grid_n + 1)
    y_edges = np.linspace(*yb, grid_n + 1)
    z_edges = np.linspace(*zb, grid_n + 1)
    H, _ = np.histogramdd(pts, bins=(x_edges, y_edges, z_edges))
    H = gaussian_filter(H, sigma=sigma)
    h_max = float(H.max())
    out: list[dict] = []
    if h_max <= 0:
        return out
    spacing = (
        (xb[1] - xb[0]) / grid_n,
        (yb[1] - yb[0]) / grid_n,
        (zb[1] - zb[0]) / grid_n,
    )
    cmap = plt.get_cmap(cmap_name)
    n_levels = len(levels_frac)
    for i, frac in enumerate(levels_frac):
        level = h_max * frac
        try:
            verts, faces, _, _ = marching_cubes(H, level=level, spacing=spacing)
        except (ValueError, RuntimeError):
            continue
        verts = verts.copy()
        verts[:, 0] += xb[0]
        verts[:, 1] += yb[0]
        verts[:, 2] += zb[0]
        t = i / max(n_levels - 1, 1)
        rgba = cmap(0.10 + 0.80 * t)
        alpha = 0.030 + 0.16 * t  # outer 0.03, inner 0.19
        out.append({
            "verts": verts.astype(np.float32),
            "faces": faces.astype(np.int32),
            "color": (float(rgba[0]), float(rgba[1]), float(rgba[2])),
            "alpha": float(alpha),
        })
    return out


def _add_iso_meshes_to_axis(ax, meshes: list[dict]) -> None:
    for m in meshes:
        verts = m["verts"]
        faces = m["faces"]
        c = m["color"]
        a = m["alpha"]
        mesh = Poly3DCollection(verts[faces])
        mesh.set_facecolor((c[0], c[1], c[2], a))
        mesh.set_edgecolor((1, 1, 1, 0.04))
        mesh.set_linewidth(0.18)
        ax.add_collection3d(mesh)


def _fading_trail_data(xyz: np.ndarray,
                       base_color: tuple[float, float, float],
                       tail_alpha: float = 0.05,
                       head_alpha: float = 0.95) -> tuple[np.ndarray, np.ndarray]:
    """Build (segments, rgba) for a Line3DCollection with alpha ramp from
    tail (oldest, faint) to head (newest, bright). Color is a tinted base."""
    n = len(xyz)
    if n < 2:
        return np.zeros((0, 2, 3)), np.zeros((0, 4))
    segs = np.stack([xyz[:-1], xyz[1:]], axis=1)
    n_segs = len(segs)
    t = np.arange(n_segs) / max(n_segs - 1, 1)
    alphas = tail_alpha + (head_alpha - tail_alpha) * t
    colors = np.zeros((n_segs, 4))
    colors[:, 0] = base_color[0]
    colors[:, 1] = base_color[1]
    colors[:, 2] = base_color[2]
    colors[:, 3] = alphas
    return segs, colors


# Worker-side data — populated via initializer
_SPLINE: np.ndarray | None = None        # (n_traj, n_samples, 3)
_SAMPLE_T: np.ndarray | None = None       # (n_samples,) float step indices
_PROJ_FLAT: np.ndarray | None = None      # (n_traj * n_steps, 3) for background scatter
_BOUNDS: tuple[np.ndarray, np.ndarray] | None = None
_FRAME_SPEC: list[dict] | None = None
_START_OFFSETS: list[int] | None = None   # per-trajectory frame offsets
_MESHES: list[dict] | None = None
_TMP_DIR: Path | None = None
_W: int = 1920
_H: int = 1080
_DPI: int = 100


def _worker_init(spline: np.ndarray, sample_t: np.ndarray,
                 proj_flat: np.ndarray,
                 bounds: tuple, schedule: list[dict],
                 start_offsets: list[int],
                 meshes: list[dict],
                 tmp_dir: str, w: int, h: int, dpi: int) -> None:
    global _SPLINE, _SAMPLE_T, _PROJ_FLAT, _BOUNDS, _FRAME_SPEC, _START_OFFSETS
    global _MESHES, _TMP_DIR, _W, _H, _DPI
    _SPLINE = spline
    _SAMPLE_T = sample_t
    _PROJ_FLAT = proj_flat
    _BOUNDS = bounds
    _FRAME_SPEC = schedule
    _START_OFFSETS = list(start_offsets)
    _MESHES = meshes
    _TMP_DIR = Path(tmp_dir)
    _W, _H, _DPI = w, h, dpi


def _render_frame(frame_idx: int) -> str:
    """Render one frame to a PNG file. Returns the file path.

    Each trajectory i starts entering the scene at _START_OFFSETS[i] frames.
    Before that frame, the trajectory is invisible. After it, the
    trajectory's effective spline sample_idx is (frame_idx - offset_i),
    clamped to [0, n_samples - 1]. A short FADE_IN_FRAMES alpha ramp
    keeps newly-appearing trajectories from popping in.
    """
    n_traj = _SPLINE.shape[0]
    n_samples = _SPLINE.shape[1]
    n_frames = len(_FRAME_SPEC)
    animation_frame = frame_idx

    plt.style.use("dark_background")
    fig = plt.figure(figsize=(_W / _DPI, _H / _DPI), dpi=_DPI, facecolor="#0a0e1a")
    ax = fig.add_subplot(111, projection="3d", facecolor="#0a0e1a")
    # Perspective projection so closer things foreshorten naturally
    try:
        ax.set_proj_type("persp", focal_length=0.35)  # wider FOV, more dramatic
    except TypeError:  # older matplotlib without focal_length kwarg
        ax.set_proj_type("persp")
    lo, hi = _BOUNDS
    ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(lo[2], hi[2])
    ax.set_xlabel("PC1", color="#9ba3b4", fontsize=11, labelpad=8)
    ax.set_ylabel("PC2", color="#9ba3b4", fontsize=11, labelpad=8)
    ax.set_zlabel("PC3", color="#9ba3b4", fontsize=11, labelpad=8)
    ax.tick_params(colors="#5a6577", labelsize=8)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.fill = False
        axis.pane.set_edgecolor("#1a2032")
        axis.pane.set_alpha(0.4)

    # Slow camera rotation: ~1 full turn over the video
    azim = 30 + 360 * (frame_idx / max(n_frames - 1, 1))
    elev = 22 + 6 * np.sin(2 * np.pi * frame_idx / max(n_frames - 1, 1))
    ax.view_init(elev=elev, azim=azim)

    # Camera position in data coordinates, used to scale marker sizes by
    # depth. matplotlib's mplot3d places the camera at distance ~10 along
    # the (elev, azim) ray from the box center.
    e = np.deg2rad(elev)
    a = np.deg2rad(azim)
    cam_dir = np.array([
        np.cos(e) * np.sin(a),
        -np.cos(e) * np.cos(a),
        np.sin(e),
    ], dtype=np.float64)
    box_center = 0.5 * (np.asarray(lo) + np.asarray(hi))
    box_diag = float(np.linalg.norm(np.asarray(hi) - np.asarray(lo)))
    cam_pos = box_center + cam_dir * (box_diag * 1.6)  # outside the box

    # Density iso-surface clouds (rendered behind trails)
    if _MESHES:
        _add_iso_meshes_to_axis(ax, _MESHES)

    # Faint background scatter of the actual data points (one per integer step)
    ax.scatter(_PROJ_FLAT[:, 0], _PROJ_FLAT[:, 1], _PROJ_FLAT[:, 2],
               c="#1f3a5e", s=3, alpha=0.10, zorder=2)

    # Spline-interpolated trails up through each trajectory's current
    # sub-step. White-on-dark with yellow perturbation arc per trajectory.
    trail_color = (1.0, 1.0, 1.0)
    yellow = np.array([1.0, 0.85, 0.20])
    pre_inject = (INJECT_STEP - 1) * N_SUBSTEPS
    inject_idx_seg = INJECT_STEP * N_SUBSTEPS
    for i in range(n_traj):
        offset_i = _START_OFFSETS[i]
        if animation_frame < offset_i:
            # this trajectory hasn't entered the scene yet
            continue
        local = animation_frame - offset_i
        sample_i = min(local, n_samples - 1)
        # fade-in alpha ramp
        fade = float(np.clip(local / max(FADE_IN_FRAMES - 1, 1), 0.0, 1.0))

        xyz = _SPLINE[i, : sample_i + 1]
        if sample_i >= 1:
            segs, colors = _fading_trail_data(
                xyz,
                base_color=trail_color,
                tail_alpha=0.10,
                head_alpha=0.98,
            )
            n_segs = len(colors)
            # Yellow perturbation segments: only color them if this
            # trajectory has reached at least the first inject segment.
            for seg_k in range(max(pre_inject, 0), min(inject_idx_seg, n_segs)):
                colors[seg_k, :3] = yellow
            # Apply fade-in to all alpha values
            colors[:, 3] *= fade
            lc = Line3DCollection(segs, colors=colors, linewidths=1.9, zorder=4)
            ax.add_collection3d(lc)

        # Layered particle head with depth-scaled size + fade-in alpha
        head_xyz = _SPLINE[i, sample_i]
        depth = float(np.linalg.norm(cam_pos - head_xyz))
        scale = float(np.clip((box_diag * 1.6) / max(depth, 1e-6), 0.40, 2.5))
        ax.plot([head_xyz[0]], [head_xyz[1]], [head_xyz[2]],
                "o", color="#ffffff",
                markersize=18 * scale, markeredgecolor="none",
                alpha=0.18 * fade, zorder=5)
        ax.plot([head_xyz[0]], [head_xyz[1]], [head_xyz[2]],
                "o", color="#ffffff",
                markersize=11 * scale, markeredgecolor="none",
                alpha=0.55 * fade, zorder=6)
        ax.plot([head_xyz[0]], [head_xyz[1]], [head_xyz[2]],
                "o", color="#ffffff",
                markersize=5 * scale, markeredgecolor="none",
                alpha=1.0 * fade, zorder=7)

    # Headline only (no global step counter / horizon labels because each
    # trajectory has its own time origin under staggered entry)
    fig.suptitle(
        "Recursive LLM trajectories with staggered adversarial nudge\n"
        f"O1 append-mode loop, dose {TARGET_DOSE} tokens, n={n_traj} trajectories",
        color="#dde3ee", fontsize=15, y=0.96,
    )
    fig.text(0.04, 0.05,
             "yellow arcs = the perturbation (kicks step 14 → 15 of each trajectory)",
             color="#9ba3b4", fontsize=11, family="monospace")

    out_path = _TMP_DIR / f"f{frame_idx:06d}.png"
    fig.savefig(out_path, dpi=_DPI, facecolor="#0a0e1a")
    plt.close(fig)
    return str(out_path)


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    coords, _ = _load_long_trajectories(N_TRAJ)
    flat = coords.reshape(-1, coords.shape[-1])
    print(f"flat embedding cloud: {flat.shape}")
    pca = PCA(n_components=3, random_state=42)
    proj_flat = pca.fit_transform(flat)
    proj = proj_flat.reshape(coords.shape[0], coords.shape[1], 3)
    print(f"explained variance ratio: {pca.explained_variance_ratio_}  "
          f"(sum {pca.explained_variance_ratio_.sum():.3f})")

    pmin = proj_flat.min(axis=0)
    pmax = proj_flat.max(axis=0)
    pad = 0.08 * (pmax - pmin)
    bounds = (pmin - pad, pmax + pad)

    print(f"fitting cubic splines per trajectory at {N_SUBSTEPS} sub-steps/step ...")
    spline_xyz, sample_t = _spline_paths(proj, N_SUBSTEPS)
    n_samples = spline_xyz.shape[1]
    n_traj_local = spline_xyz.shape[0]
    print(f"  spline samples per trajectory: {n_samples} "
          f"(dense from t=0 to t={sample_t[-1]:.1f})")

    schedule, start_offsets = _frame_schedule(n_samples, n_traj_local)
    n_frames = len(schedule)
    print(f"staggered entries: trajectory i starts at frame {STAGGER_FRAMES}*i  "
          f"(offsets {start_offsets[0]} .. {start_offsets[-1]})")
    print(f"frame plan: {n_frames} frames @ {FPS}fps = {n_frames / FPS:.1f}s "
          f"(staggered procession + end hold)")

    print("computing iso-surface clouds (once, joint cloud) ...")
    meshes = _compute_iso_meshes(proj_flat, bounds)
    print(f"  built {len(meshes)} iso-surface layers (outer→inner)")

    with tempfile.TemporaryDirectory(prefix="long_traj_3d_") as tmp:
        tmp_dir = Path(tmp)
        print(f"rendering {n_frames} frames in parallel across {N_WORKERS} workers ...")
        with ProcessPoolExecutor(
            max_workers=N_WORKERS,
            initializer=_worker_init,
            initargs=(spline_xyz, sample_t, proj_flat, bounds,
                      schedule, start_offsets, meshes, str(tmp_dir), W, H, DPI),
        ) as ex:
            futs = [ex.submit(_render_frame, i) for i in range(n_frames)]
            done = 0
            for fut in as_completed(futs):
                _ = fut.result()
                done += 1
                if done % 30 == 0 or done == n_frames:
                    print(f"  rendered {done}/{n_frames} frames")

        # Encode to mp4 with bundled ffmpeg, all cores
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        cmd = [
            ffmpeg,
            "-y",
            "-r", str(FPS),
            "-i", str(tmp_dir / "f%06d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "slow",
            "-crf", "18",
            "-threads", "0",
            "-movflags", "+faststart",
            str(OUT_PATH),
        ]
        print(f"encoding -> {OUT_PATH.name} (libx264, all cores)")
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            print("ffmpeg failed:")
            print(proc.stderr[-2000:])
            sys.exit(proc.returncode)
        sz_mb = OUT_PATH.stat().st_size / 1024 / 1024
        print(f"wrote {OUT_PATH}  ({sz_mb:.1f} MB)")


if __name__ == "__main__":
    main()
