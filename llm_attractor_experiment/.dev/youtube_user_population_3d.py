"""High-res YouTube 3D animation: 10 named "users" each having their own
conversation with the same LLM, all hit by the same kind of adversarial
perturbation.

Personifies the multi-trajectory video. Each particle gets a human name
label attached to its head. The selection prefers 2 distinct (family, IC)
pairs per prompt family, so the 10 names map to 10 genuinely different
starting prompts — 5 families × 2 ICs = 10 conversations.

Same visual stack as youtube_long_trajectory_3d.py:
  - dark navy background, 5 plasma iso-density shells, faint cohort scatter
  - cubic-spline-smoothed white trails with yellow perturbation arcs
  - 3-layer luminous heads with depth-scaled size + name label
  - perspective projection (focal_length=0.35)
  - staggered entry (0.6 s between successive users)

Output: data/aggregated/dip_mechanism_B/youtube_user_population_3d.mp4
        1920x1080, 30 fps, libx264 + yuv420p.
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
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mpl_toolkits.mplot3d.art3d import Line3DCollection
from PIL import Image
from sklearn.decomposition import PCA

from youtube_long_trajectory_3d import (  # noqa: E402
    DATA, INJECT_STEP, EXT_START, TOTAL_STEPS, FPS, DPI, W, H, N_SUBSTEPS,
    STAGGER_FRAMES, FADE_IN_FRAMES, END_HOLD_FRAMES,
    _add_iso_meshes_to_axis, _compute_iso_meshes, _fading_trail_data,
    _spline_paths,
)

OUT_PATH = DATA / "aggregated" / "dip_mechanism_B" / "youtube_user_population_3d.mp4"
AVATAR_DIR = ROOT / ".dev" / "avatars"

EXP_ORIG = "exp_perturb_O1_ed50_higher_noclip"
EXP_EXT  = "exp_perturb_O1_ed50_higher_noclip_extended"
TARGET_DOSE = 2000
TARGET_REGIME = f"adversarial_dose{TARGET_DOSE}"

# (prompt_family, initial_condition_id, run_id, "Display Name")
# Two unique (family, IC) pairs per family → 10 genuinely different starting
# prompts. Names chosen for diversity (gender, cultural origin); no implied
# identity beyond "this user has this kind of conversation."
USER_PICKS = [
    ("creative_dialog",   "ic_000", "run_000", "Maya"),
    ("creative_dialog",   "ic_001", "run_000", "Diego"),
    ("emotional",         "ic_000", "run_000", "Lila"),
    ("emotional",         "ic_001", "run_000", "Theo"),
    ("philosophy_dialog", "ic_000", "run_000", "Marcus"),
    ("philosophy_dialog", "ic_001", "run_000", "Sofia"),
    ("practical_dialog",  "ic_000", "run_000", "Wei"),
    ("practical_dialog",  "ic_001", "run_000", "Hannah"),
    ("reflective",        "ic_000", "run_000", "Oliver"),
    ("reflective",        "ic_001", "run_000", "Aiko"),
]

N_WORKERS = max(1, (os.cpu_count() or 4))


def _load_user_paths():
    """Load the 10 chosen user trajectories. Returns (coords, names).
    coords shape = (10, 80, 1536)."""
    X_o = np.load(DATA / EXP_ORIG / "embeddings" / "context_tail" / "embeddings.npy")
    M_o = pd.read_parquet(DATA / EXP_ORIG / "embeddings" / "context_tail" / "metadata.parquet").reset_index(drop=True)
    X_e = np.load(DATA / EXP_EXT / "embeddings" / "context_tail" / "embeddings.npy")
    M_e = pd.read_parquet(DATA / EXP_EXT / "embeddings" / "context_tail" / "metadata.parquet").reset_index(drop=True)
    sub_o = M_o[M_o["regime"] == TARGET_REGIME]
    sub_e = M_e[M_e["regime"] == TARGET_REGIME]

    coords = np.zeros((len(USER_PICKS), TOTAL_STEPS, X_o.shape[1]), dtype=np.float32)
    names = []
    for i, (fam, ic, run, name) in enumerate(USER_PICKS):
        rows_o = sub_o[(sub_o.prompt_family == fam)
                       & (sub_o.initial_condition_id == ic)
                       & (sub_o.run_id == run)]
        for idx, r in rows_o.iterrows():
            s = int(r["step"])
            if 0 <= s < EXT_START:
                coords[i, s] = X_o[idx]
        rows_e = sub_e[(sub_e.prompt_family == fam)
                       & (sub_e.initial_condition_id == ic)
                       & (sub_e.run_id == run)]
        for idx, r in rows_e.iterrows():
            s = int(r["step"])
            if EXT_START <= s < TOTAL_STEPS:
                coords[i, s] = X_e[idx]
        # Verify the trajectory is fully populated
        if (coords[i].sum(axis=1) == 0).any():
            print(f"WARNING: incomplete trajectory for {(fam, ic, run, name)}; skipping")
            continue
        names.append(name)
    print(f"loaded {len(names)} user trajectories: {names}")
    return coords, names


def _frame_schedule(n_samples: int, n_traj: int):
    start_offsets = [i * STAGGER_FRAMES for i in range(n_traj)]
    last_traj_end = start_offsets[-1] + (n_samples - 1)
    total = last_traj_end + 1 + END_HOLD_FRAMES
    return [{"animation_frame": f} for f in range(total)], start_offsets


def _load_avatars(names: list[str]) -> list[np.ndarray]:
    """Load avatar PNGs as RGBA numpy arrays (H, W, 4) in [0, 1]."""
    out = []
    for name in names:
        p = AVATAR_DIR / f"{name}.png"
        if not p.exists():
            print(f"WARNING: missing avatar {p}; using blank placeholder")
            out.append(np.zeros((1, 1, 4), dtype=np.float32))
            continue
        img = Image.open(p).convert("RGBA")
        out.append(np.asarray(img, dtype=np.float32) / 255.0)
    return out


# Worker globals
_SPLINE = None
_SAMPLE_T = None
_PROJ_FLAT = None
_BOUNDS = None
_FRAME_SPEC = None
_START_OFFSETS = None
_NAMES = None
_AVATARS = None
_MESHES = None
_TMP = None


def _worker_init(spline, sample_t, proj_flat, bounds, schedule, offsets,
                 names, avatars, meshes, tmp):
    global _SPLINE, _SAMPLE_T, _PROJ_FLAT, _BOUNDS, _FRAME_SPEC
    global _START_OFFSETS, _NAMES, _AVATARS, _MESHES, _TMP
    _SPLINE = spline
    _SAMPLE_T = sample_t
    _PROJ_FLAT = proj_flat
    _BOUNDS = bounds
    _FRAME_SPEC = schedule
    _START_OFFSETS = list(offsets)
    _NAMES = list(names)
    _AVATARS = list(avatars)
    _MESHES = meshes
    _TMP = Path(tmp)


def _render_frame(frame_idx: int) -> str:
    n_traj = _SPLINE.shape[0]
    n_samples = _SPLINE.shape[1]
    n_frames = len(_FRAME_SPEC)
    animation_frame = frame_idx
    pre_inject_local = (INJECT_STEP - 1) * N_SUBSTEPS
    inject_idx_seg_local = INJECT_STEP * N_SUBSTEPS

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

    if _MESHES:
        _add_iso_meshes_to_axis(ax, _MESHES)
    ax.scatter(_PROJ_FLAT[:, 0], _PROJ_FLAT[:, 1], _PROJ_FLAT[:, 2],
               c="#1f3a5e", s=3, alpha=0.10, zorder=2)

    trail_color = (1.0, 1.0, 1.0)
    yellow = np.array([1.0, 0.85, 0.20])
    pre_inject = (INJECT_STEP - 1) * N_SUBSTEPS
    inject_idx_seg = INJECT_STEP * N_SUBSTEPS
    label_z_offset = (hi[2] - lo[2]) * 0.025  # small upward bump for the name

    for i in range(n_traj):
        offset_i = _START_OFFSETS[i]
        if animation_frame < offset_i:
            continue
        local = animation_frame - offset_i
        sample_i = min(local, n_samples - 1)
        fade = float(np.clip(local / max(FADE_IN_FRAMES - 1, 1), 0.0, 1.0))

        xyz = _SPLINE[i, : sample_i + 1]
        if sample_i >= 1:
            segs, colors = _fading_trail_data(xyz, trail_color, 0.10, 0.98)
            n_segs = len(colors)
            for seg_k in range(max(pre_inject, 0), min(inject_idx_seg, n_segs)):
                colors[seg_k, :3] = yellow
            colors[:, 3] *= fade
            lc = Line3DCollection(segs, colors=colors, linewidths=1.9, zorder=4)
            ax.add_collection3d(lc)

        head_xyz = _SPLINE[i, sample_i]
        depth = float(np.linalg.norm(cam_pos - head_xyz))
        scale = float(np.clip((box_diag * 1.6) / max(depth, 1e-6), 0.40, 2.5))
        ax.plot([head_xyz[0]], [head_xyz[1]], [head_xyz[2]],
                "o", color="#ffffff", markersize=18 * scale,
                markeredgecolor="none", alpha=0.18 * fade, zorder=5)
        ax.plot([head_xyz[0]], [head_xyz[1]], [head_xyz[2]],
                "o", color="#ffffff", markersize=11 * scale,
                markeredgecolor="none", alpha=0.55 * fade, zorder=6)
        ax.plot([head_xyz[0]], [head_xyz[1]], [head_xyz[2]],
                "o", color="#ffffff", markersize=5 * scale,
                markeredgecolor="none", alpha=1.0 * fade, zorder=7)

        # (avatar is drawn after the loop so we can pull projected pixel
        #  coords from the now-finalized ax view; see post-loop block)

    # ---- Title + subtitle, then avatars floating ABOVE each head ----
    fig.suptitle(
        "Ten people, one LLM: a synchronized adversarial nudge\n"
        f"O1 append-mode loops, dose {TARGET_DOSE} tokens, "
        f"n={n_traj} simultaneous conversations",
        color="#dde3ee", fontsize=15, y=0.96,
    )
    fig.text(0.04, 0.04,
             "yellow arc = adversarial text injected into each user's loop "
             "(step 14 → step 15)",
             color="#9ba3b4", fontsize=11, family="monospace")

    # IMPORTANT: figimage runs AFTER the canvas is drawn for the axes, so
    # we must force a draw first to get final projection. Then for each
    # visible head, project to 2D pixel coords and stamp the avatar above.
    fig.canvas.draw()
    from mpl_toolkits.mplot3d.proj3d import proj_transform
    proj = ax.get_proj()

    for i in range(n_traj):
        offset_i = _START_OFFSETS[i]
        if animation_frame < offset_i:
            continue
        local = animation_frame - offset_i
        sample_i = min(local, n_samples - 1)
        fade = float(np.clip(local / max(FADE_IN_FRAMES - 1, 1), 0.0, 1.0))
        head_xyz = _SPLINE[i, sample_i]
        # Depth → marker scale (same as head markers)
        depth = float(np.linalg.norm(cam_pos - head_xyz))
        scale = float(np.clip((box_diag * 1.6) / max(depth, 1e-6), 0.40, 2.5))
        # Project 3D head to 2D figure-pixel coords
        x2d, y2d, _ = proj_transform(head_xyz[0], head_xyz[1], head_xyz[2], proj)
        px, py = ax.transData.transform((x2d, y2d))

        if i >= len(_AVATARS) or _AVATARS[i].size <= 4:
            continue
        # Resize avatar PNG to scale-dependent target size
        target = int(np.clip(74 * scale, 36, 150))
        src_uint = (_AVATARS[i] * 255).astype(np.uint8)
        pil = Image.fromarray(src_uint, mode="RGBA").resize(
            (target, target), Image.LANCZOS,
        )
        arr = np.asarray(pil, dtype=np.float32) / 255.0
        arr[..., 3] *= fade  # apply entry fade
        # Position: centered horizontally on head, image bottom 12 px above head
        offset_above = int(38 * scale)  # gap between head and avatar
        xo = int(px - target / 2)
        yo = int(py + offset_above)
        # figimage with origin='upper' draws the array down from yo + h
        # to yo. We want the image's *bottom* at py + offset_above, so
        # in figure pixel coords (y bottom-up), image bottom = yo, top
        # = yo + h. With origin='upper' the array is drawn so its first
        # row is at the top, which is yo + h — correct for the desired
        # placement.
        try:
            fig.figimage(arr, xo=xo, yo=yo, origin="upper")
        except Exception:
            pass  # off-canvas or other matplotlib edge case

        # Name text just below the avatar, in figure-pixel coords
        name_y = yo - 14  # 14 px below image bottom
        fig.text(
            (xo + target / 2) / W, name_y / H,
            _NAMES[i],
            color="#ffe7c8",
            fontsize=10,
            weight="bold",
            ha="center", va="top",
            alpha=0.95 * fade,
        )

        # Speech bubble during the perturbation window: yellow round bubble
        # to the upper-right of the avatar, with a tail pointing back
        # toward the avatar's edge, and a "→ LLM" text inside (signaling
        # this user is currently sending text to the LLM).
        if pre_inject_local <= sample_i <= inject_idx_seg_local + 6:
            bubble_w_px = max(int(target * 1.05), 80)
            bubble_h_px = max(int(target * 0.55), 38)
            # Anchor: top-right of avatar, with small gap
            bx_left_px = xo + target + 6
            by_bottom_px = yo + target - bubble_h_px // 2
            bx_left = bx_left_px / W
            by_bottom = by_bottom_px / H
            bw = bubble_w_px / W
            bh = bubble_h_px / H

            # Bubble body: rounded yellow rectangle
            bubble = mpatches.FancyBboxPatch(
                (bx_left, by_bottom),
                bw, bh,
                boxstyle="round,pad=0.0,rounding_size=0.012",
                facecolor="#ffd633",
                edgecolor="#0a0e1a",
                linewidth=1.6,
                alpha=0.97,
                transform=fig.transFigure,
                zorder=22,
            )
            fig.add_artist(bubble)

            # Tail: small triangle pointing from the bubble's lower-left
            # back toward the avatar (its lower-right edge).
            tail_apex_px = (xo + target - 4, yo + target * 0.40)
            tail_b1_px = (bx_left_px + 6,            by_bottom_px + bubble_h_px * 0.15)
            tail_b2_px = (bx_left_px + bubble_h_px * 0.5, by_bottom_px + 6)
            tail_pts_fig = [
                (tail_apex_px[0] / W, tail_apex_px[1] / H),
                (tail_b1_px[0]   / W, tail_b1_px[1]   / H),
                (tail_b2_px[0]   / W, tail_b2_px[1]   / H),
            ]
            tail = mpatches.Polygon(
                tail_pts_fig,
                closed=True,
                facecolor="#ffd633",
                edgecolor="#0a0e1a",
                linewidth=1.4,
                alpha=0.97,
                transform=fig.transFigure,
                zorder=22,
            )
            fig.add_artist(tail)

            # Bubble text: "→ LLM"
            text_x = (bx_left_px + bubble_w_px / 2) / W
            text_y = (by_bottom_px + bubble_h_px / 2) / H
            fig.text(
                text_x, text_y,
                "→ LLM",
                color="#0a0e1a",
                fontsize=max(int(target * 0.18), 10),
                weight="bold",
                ha="center", va="center",
            )

    out = _TMP / f"f{frame_idx:06d}.png"
    fig.savefig(out, dpi=DPI, facecolor="#0a0e1a")
    plt.close(fig)
    return str(out)


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    coords, names = _load_user_paths()
    flat = coords.reshape(-1, coords.shape[-1])
    pca = PCA(n_components=3, random_state=42)
    proj_flat = pca.fit_transform(flat)
    proj = proj_flat.reshape(coords.shape[0], coords.shape[1], 3)
    print(f"explained variance ratio: {pca.explained_variance_ratio_}  "
          f"(sum {pca.explained_variance_ratio_.sum():.3f})")

    pmin = proj_flat.min(axis=0)
    pmax = proj_flat.max(axis=0)
    pad = 0.08 * (pmax - pmin)
    bounds = (pmin - pad, pmax + pad)

    spline_xyz, sample_t = _spline_paths(proj, N_SUBSTEPS)
    n_samples = spline_xyz.shape[1]

    schedule, start_offsets = _frame_schedule(n_samples, len(names))
    n_frames = len(schedule)
    print(f"frame plan: {n_frames} frames @ {FPS}fps = {n_frames / FPS:.1f}s")

    print("computing iso-surface clouds (cohort) ...")
    meshes = _compute_iso_meshes(proj_flat, bounds)
    print(f"  built {len(meshes)} iso-surface layers")

    print("loading avatars ...")
    avatars = _load_avatars(names)
    print(f"  loaded {sum(1 for a in avatars if a.size > 4)} / {len(avatars)} avatars")

    with tempfile.TemporaryDirectory(prefix="user_pop_3d_") as tmp:
        tmp_dir = Path(tmp)
        print(f"rendering {n_frames} frames in parallel across {N_WORKERS} workers ...")
        with ProcessPoolExecutor(
            max_workers=N_WORKERS,
            initializer=_worker_init,
            initargs=(spline_xyz, sample_t, proj_flat, bounds,
                      schedule, start_offsets, names, avatars, meshes, str(tmp_dir)),
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
