"""High-res YouTube 3D animation of ONE single trajectory whose narrative
is "comes from a cloud, takes the perturbation kick, lands in a cloud."

Selection (.dev/find_cloud_to_cloud_traj.py): the trajectory that scores
highest on min(density_start, density_end) under the same gaussian-
smoothed PCA-3 density used for iso-surfaces. Top hit: dose 2000,
reflective/ic_001/run_000, with start density 1.99 and end density 3.64
(of max 3.88) — both endpoints sit deep inside the same high-density
attractor region, so the trajectory's full arc is "cloud → kick → cloud".

The full dose-2000 cohort (100 trajectories × 80 steps = 8000 points)
provides PCA-3 + iso-surface backdrop and faint scatter. Only the
chosen trajectory is rendered with luminous trail + yellow perturbation
arc + glowing head.

Output: data/aggregated/dip_mechanism_B/youtube_single_particle_3d.mp4
        1920x1080, 30fps, libx264 + yuv420p.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".dev"))

import imageio_ffmpeg
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mpl_toolkits.mplot3d.art3d import Line3DCollection
from sklearn.decomposition import PCA

# Reuse helpers from the multi-particle script
from youtube_long_trajectory_3d import (  # noqa: E402
    DATA, INJECT_STEP, EXT_START, TOTAL_STEPS, FPS, DPI, W, H,
    _add_iso_meshes_to_axis, _compute_iso_meshes, _fading_trail_data,
    _spline_paths,
)

OUT_PATH = DATA / "aggregated" / "dip_mechanism_B" / "youtube_single_particle_3d_v2.mp4"

EXP_ORIG = "exp_perturb_O1_ed50_higher_noclip"
EXP_EXT  = "exp_perturb_O1_ed50_higher_noclip_extended"
TARGET_DOSE = 2000
TARGET_REGIME = f"adversarial_dose{TARGET_DOSE}"
# Alternative source/destination candidate from .dev/find_cloud_to_cloud_traj.py:
# different prompt family from v1, end-density 3.07/3.88 (extremely strong
# destination cloud), 38% box-diag separation, leap 0.41 in PCA-3. The
# previous v1 was practical_dialog/ic_000/run_001 (separation 45%, end 1.29).
PICK = ("creative_dialog", "ic_004", "run_003")

N_SUBSTEPS = 6
INJECT_HOLD_FRAMES = 60   # 2 s pause at the perturbation
EXT_HOLD_FRAMES = 0
N_WORKERS = max(1, (os.cpu_count() or 4))


def _load_cohort_and_pick() -> tuple[np.ndarray, np.ndarray, dict]:
    """Return (cohort_paths, single_path, meta). cohort_paths shape =
    (n_cohort, 80, 1536); single_path shape = (80, 1536); meta = pick info."""
    X_o = np.load(DATA / EXP_ORIG / "embeddings" / "context_tail" / "embeddings.npy")
    M_o = pd.read_parquet(DATA / EXP_ORIG / "embeddings" / "context_tail" / "metadata.parquet").reset_index(drop=True)
    X_e = np.load(DATA / EXP_EXT / "embeddings" / "context_tail" / "embeddings.npy")
    M_e = pd.read_parquet(DATA / EXP_EXT / "embeddings" / "context_tail" / "metadata.parquet").reset_index(drop=True)

    sub_o = M_o[M_o["regime"] == TARGET_REGIME]
    sub_e = M_e[M_e["regime"] == TARGET_REGIME]
    keys_o = set(sub_o.groupby(["prompt_family", "initial_condition_id", "run_id"]).size().index.tolist())
    keys_e = set(sub_e.groupby(["prompt_family", "initial_condition_id", "run_id"]).size().index.tolist())
    common = sorted(keys_o & keys_e)
    print(f"cohort: {len(common)} trajectories at dose {TARGET_DOSE}")

    cohort = np.zeros((len(common), TOTAL_STEPS, X_o.shape[1]), dtype=np.float32)
    pick_idx = -1
    for i, k in enumerate(common):
        fam, ic, run = k
        rows_o = sub_o[(sub_o.prompt_family == fam)
                       & (sub_o.initial_condition_id == ic)
                       & (sub_o.run_id == run)]
        for idx, r in rows_o.iterrows():
            s = int(r["step"])
            if 0 <= s < EXT_START:
                cohort[i, s] = X_o[idx]
        rows_e = sub_e[(sub_e.prompt_family == fam)
                       & (sub_e.initial_condition_id == ic)
                       & (sub_e.run_id == run)]
        for idx, r in rows_e.iterrows():
            s = int(r["step"])
            if EXT_START <= s < TOTAL_STEPS:
                cohort[i, s] = X_e[idx]
        if k == PICK:
            pick_idx = i
    if pick_idx < 0:
        raise SystemExit(f"PICK {PICK} not found in cohort")
    pick_meta = {
        "fam": PICK[0], "ic": PICK[1], "run": PICK[2],
        "dose": TARGET_DOSE, "cohort_n": len(common),
        "leap_1536d": float(np.linalg.norm(cohort[pick_idx, 15] - cohort[pick_idx, 14])),
    }
    print(f"chosen: {pick_meta}")
    return cohort, cohort[pick_idx], pick_meta


def _frame_schedule(n_samples: int) -> list[dict]:
    inject_idx = INJECT_STEP * N_SUBSTEPS
    ext_idx = EXT_START * N_SUBSTEPS
    last_idx = n_samples - 1
    frames: list[dict] = []
    for ti in range(0, inject_idx + 1):
        frames.append({"sample_idx": ti, "callout": None, "alpha": 0.0})
    for k in range(INJECT_HOLD_FRAMES):
        frac = k / max(INJECT_HOLD_FRAMES - 1, 1)
        a = float(np.clip(2.0 - 2.0 * abs(frac - 0.5), 0.0, 1.0))
        frames.append({"sample_idx": inject_idx, "callout": "inject", "alpha": a})
    for ti in range(inject_idx + 1, ext_idx + 1):
        frames.append({"sample_idx": ti, "callout": None, "alpha": 0.0})
    for k in range(EXT_HOLD_FRAMES):
        frac = k / max(EXT_HOLD_FRAMES - 1, 1)
        a = float(np.clip(2.0 - 2.0 * abs(frac - 0.5), 0.0, 1.0))
        frames.append({"sample_idx": ext_idx, "callout": "ext", "alpha": a})
    for ti in range(ext_idx + 1, last_idx + 1):
        frames.append({"sample_idx": ti, "callout": None, "alpha": 0.0})
    return frames


# Worker globals
_SPLINE: np.ndarray | None = None
_SAMPLE_T: np.ndarray | None = None
_COHORT_FLAT: np.ndarray | None = None
_BOUNDS: tuple | None = None
_FRAME_SPEC: list[dict] | None = None
_MESHES: list[dict] | None = None
_PICK_META: dict | None = None
_TMP: Path | None = None


def _worker_init(spline, sample_t, cohort_flat, bounds, schedule, meshes, pick_meta, tmp):
    global _SPLINE, _SAMPLE_T, _COHORT_FLAT, _BOUNDS, _FRAME_SPEC, _MESHES, _PICK_META, _TMP
    _SPLINE = spline
    _SAMPLE_T = sample_t
    _COHORT_FLAT = cohort_flat
    _BOUNDS = bounds
    _FRAME_SPEC = schedule
    _MESHES = meshes
    _PICK_META = pick_meta
    _TMP = Path(tmp)


def _render_frame(frame_idx: int) -> str:
    spec = _FRAME_SPEC[frame_idx]
    sample_idx = spec["sample_idx"]
    callout = spec.get("callout")
    callout_alpha = float(spec.get("alpha", 0.0))
    n_frames = len(_FRAME_SPEC)
    t_now = float(_SAMPLE_T[sample_idx])

    plt.style.use("dark_background")
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor="#0a0e1a")
    ax = fig.add_subplot(111, projection="3d", facecolor="#0a0e1a")
    try:
        ax.set_proj_type("persp", focal_length=0.35)
    except TypeError:
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

    azim = 30 + 360 * (frame_idx / max(n_frames - 1, 1))
    elev = 22 + 6 * np.sin(2 * np.pi * frame_idx / max(n_frames - 1, 1))
    ax.view_init(elev=elev, azim=azim)

    e = np.deg2rad(elev); a = np.deg2rad(azim)
    cam_dir = np.array([
        np.cos(e) * np.sin(a), -np.cos(e) * np.cos(a), np.sin(e),
    ], dtype=np.float64)
    box_center = 0.5 * (np.asarray(lo) + np.asarray(hi))
    box_diag = float(np.linalg.norm(np.asarray(hi) - np.asarray(lo)))
    cam_pos = box_center + cam_dir * (box_diag * 1.6)

    # Iso-surface clouds (computed once on the cohort)
    if _MESHES:
        _add_iso_meshes_to_axis(ax, _MESHES)

    # Faint cohort background scatter (the cloud's actual data points)
    ax.scatter(_COHORT_FLAT[:, 0], _COHORT_FLAT[:, 1], _COHORT_FLAT[:, 2],
               c="#1f3a5e", s=2, alpha=0.08, zorder=2)

    # The single chosen trajectory's spline trail
    end_idx = sample_idx + 1
    xyz = _SPLINE[:end_idx]
    trail_color = (1.0, 1.0, 1.0)
    yellow = np.array([1.0, 0.85, 0.20])
    pre_inject = (INJECT_STEP - 1) * N_SUBSTEPS
    inject_idx_seg = INJECT_STEP * N_SUBSTEPS
    if end_idx >= 2:
        segs, colors = _fading_trail_data(xyz, trail_color, 0.10, 0.98)
        for seg_k in range(max(pre_inject, 0), min(inject_idx_seg, len(colors))):
            colors[seg_k, :3] = yellow
        # Slightly thicker line for the single-particle case
        lc = Line3DCollection(segs, colors=colors, linewidths=2.4, zorder=4)
        ax.add_collection3d(lc)

    # Single luminous head
    head_xyz = _SPLINE[sample_idx]
    depth = float(np.linalg.norm(cam_pos - head_xyz))
    scale = float(np.clip((box_diag * 1.6) / max(depth, 1e-6), 0.40, 2.5))
    # Outer halo, mid glow, saturated core
    ax.plot([head_xyz[0]], [head_xyz[1]], [head_xyz[2]],
            "o", color="#ffffff", markersize=24 * scale,
            markeredgecolor="none", alpha=0.18, zorder=5)
    ax.plot([head_xyz[0]], [head_xyz[1]], [head_xyz[2]],
            "o", color="#ffffff", markersize=14 * scale,
            markeredgecolor="none", alpha=0.55, zorder=6)
    ax.plot([head_xyz[0]], [head_xyz[1]], [head_xyz[2]],
            "o", color="#ffffff", markersize=7 * scale,
            markeredgecolor="none", alpha=1.0, zorder=7)

    # Headline and overlays
    fig.suptitle(
        "Single-trajectory perturbation jump in a recursive LLM loop\n"
        f"O1 append-mode, dose {_PICK_META['dose']} tokens · "
        f"family: {_PICK_META['fam']} · {_PICK_META['ic']} · {_PICK_META['run']}",
        color="#dde3ee", fontsize=15, y=0.96,
    )
    fig.text(0.04, 0.92, f"step  t = {t_now:5.2f} / {TOTAL_STEPS - 1}",
             color="#dde3ee", fontsize=14, family="monospace", weight="bold")
    fig.text(0.04, 0.88, f"step-15 leap (1536-d) = {_PICK_META['leap_1536d']:.3f}",
             color="#9ba3b4", fontsize=11, family="monospace")
    if t_now < INJECT_STEP:
        horizon = "pre-injection horizon (steps 0-14)"
    elif t_now < EXT_START:
        horizon = "canonical 30-step horizon (paper §5.1.3)"
    else:
        horizon = "extended horizon (steps 30-79)"
    fig.text(0.04, 0.05, horizon,
             color="#9ba3b4", fontsize=12, family="monospace")

    if callout == "inject":
        fig.text(0.5, 0.10, "PERTURBATION INJECTED  (the nudge)",
                 color="#ffd633", fontsize=22, ha="center",
                 weight="bold", alpha=callout_alpha)

    out = _TMP / f"f{frame_idx:06d}.png"
    fig.savefig(out, dpi=DPI, facecolor="#0a0e1a")
    plt.close(fig)
    return str(out)


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    cohort, single_path, pick_meta = _load_cohort_and_pick()
    cohort_flat = cohort.reshape(-1, cohort.shape[-1])
    pca = PCA(n_components=3, random_state=42)
    pca.fit(cohort_flat)
    cohort_proj_flat = pca.transform(cohort_flat)
    single_proj = pca.transform(single_path).astype(np.float32)
    print(f"explained variance ratio: {pca.explained_variance_ratio_}")

    pmin = cohort_proj_flat.min(axis=0)
    pmax = cohort_proj_flat.max(axis=0)
    pad = 0.08 * (pmax - pmin)
    bounds = (pmin - pad, pmax + pad)

    # Spline only the single trajectory
    single_proj_3d = single_proj[None, :, :]  # (1, 80, 3) for the helper
    spline_xyz, sample_t = _spline_paths(single_proj_3d, N_SUBSTEPS)
    single_spline = spline_xyz[0]  # (n_samples, 3)
    n_samples = single_spline.shape[0]

    schedule = _frame_schedule(n_samples)
    n_frames = len(schedule)
    print(f"frame plan: {n_frames} frames @ {FPS}fps = {n_frames / FPS:.1f}s")

    print("computing iso-surface clouds (cohort) ...")
    meshes = _compute_iso_meshes(cohort_proj_flat, bounds)
    print(f"  built {len(meshes)} iso-surface layers")

    with tempfile.TemporaryDirectory(prefix="single_traj_3d_") as tmp:
        tmp_dir = Path(tmp)
        print(f"rendering {n_frames} frames in parallel across {N_WORKERS} workers ...")
        with ProcessPoolExecutor(
            max_workers=N_WORKERS,
            initializer=_worker_init,
            initargs=(single_spline, sample_t, cohort_proj_flat, bounds,
                      schedule, meshes, pick_meta, str(tmp_dir)),
        ) as ex:
            futs = [ex.submit(_render_frame, i) for i in range(n_frames)]
            done = 0
            for fut in as_completed(futs):
                _ = fut.result()
                done += 1
                if done % 30 == 0 or done == n_frames:
                    print(f"  rendered {done}/{n_frames} frames")

        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        cmd = [
            ffmpeg, "-y",
            "-r", str(FPS),
            "-i", str(tmp_dir / "f%06d.png"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-preset", "slow", "-crf", "18",
            "-threads", "0", "-movflags", "+faststart",
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
