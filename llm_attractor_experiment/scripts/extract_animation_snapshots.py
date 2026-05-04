"""
Extract a representative frame from each of the four 3D PCA animation
MP4s (control / neutral / lorem / adversarial) and compose them into a
single 2x2 grid PNG suitable for inclusion as a paper figure.

Why this exists: the perturbation visualization toolkit produces MP4
flythroughs of the 3D PCA flow with iso-density shells, trajectory
walks, and red kick beams at the injection step. The MP4s are too
large for the paper and a paper can't embed video. A single static
snapshot per condition that captures the post-perturbation flow state
is the static analog.

Frame selection: we extract a frame at ~70% of the animation duration —
after the perturbation injection (which happens around step 15 of 30,
i.e. mid-animation) so the diverging post-perturbation flow is visible.

Usage:
    python -m scripts.extract_animation_snapshots
        [--exp exp_perturb_O1_pilot]      # source experiment dir
        [--frac 0.70]                      # fraction of duration to sample

Output:
    data/<exp>/reports/perturbation/animation3d_snapshots.png
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import imageio.v3 as iio
import numpy as np

REPO = Path(__file__).resolve().parent.parent
CONDITIONS = ("control", "neutral", "lorem", "adversarial")


def _load_frame(mp4_path: Path, frac: float) -> np.ndarray:
    """Read the frame at frac (0..1) of the video duration.

    imageio's improps reports `inf` frames for some streamed MP4
    encodings, so we materialize all frames into a list and index in.
    The animation MP4s are short (~75 frames at DPI 180), so memory
    cost is bounded and predictable."""
    frames = list(iio.imiter(mp4_path))
    if not frames:
        raise RuntimeError(f"no frames in {mp4_path}")
    target_idx = max(0, min(len(frames) - 1,
                            int(round(frac * (len(frames) - 1)))))
    return frames[target_idx]


def _compose_grid(frames: list[np.ndarray]) -> np.ndarray:
    """Stack 4 frames into a 2x2 grid. Frames must be the same shape."""
    if len(frames) != 4:
        raise ValueError(f"expected 4 frames, got {len(frames)}")
    # Pad smaller frames to the largest H, W if shapes differ.
    h_max = max(f.shape[0] for f in frames)
    w_max = max(f.shape[1] for f in frames)
    padded = []
    for f in frames:
        if f.shape[0] != h_max or f.shape[1] != w_max:
            ph = h_max - f.shape[0]
            pw = w_max - f.shape[1]
            f = np.pad(f, ((0, ph), (0, pw), (0, 0)), constant_values=255)
        padded.append(f)
    top = np.concatenate([padded[0], padded[1]], axis=1)
    bottom = np.concatenate([padded[2], padded[3]], axis=1)
    return np.concatenate([top, bottom], axis=0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", default="exp_perturb_O1_pilot",
                    help="experiment directory under data/")
    ap.add_argument("--frac", type=float, default=0.70,
                    help="fraction (0..1) of animation duration to sample")
    args = ap.parse_args()

    src_dir = REPO / "data" / args.exp / "reports" / "perturbation"
    if not src_dir.is_dir():
        print(f"error: {src_dir} not found")
        return 1

    frames: list[np.ndarray] = []
    for cond in CONDITIONS:
        # Prefer the smallest-ensemble MP4 we can find — n=6 gives
        # readable flow without 50-trajectory overcrowding; n=1 is too
        # sparse to show "flow" at all; n=50 is the busy default. The
        # single-trajectory filename embeds family/ic/run.
        single_glob = sorted(src_dir.glob(
            f"animation3d_{cond}_*_ic_*_run_*.mp4"
        ))
        candidates = [
            src_dir / f"animation3d_{cond}_n6_seed0.mp4",
            src_dir / f"animation3d_{cond}_n8_seed0.mp4",
            *single_glob,
            src_dir / f"animation3d_{cond}_n25_seed0.mp4",
            src_dir / f"animation3d_{cond}_n50_seed0.mp4",
        ]
        mp4 = next((p for p in candidates if p.exists()), None)
        if mp4 is None:
            print(f"error: no animation3d_{cond}_*.mp4 found in {src_dir}")
            return 2
        frame = _load_frame(mp4, args.frac)
        frames.append(frame)
        print(f"  {cond}: {mp4.name} (H={frame.shape[0]}, W={frame.shape[1]})")

    grid = _compose_grid(frames)
    out_path = src_dir / "animation3d_snapshots.png"
    iio.imwrite(out_path, grid)
    print(f"\nwrote {out_path} ({grid.shape[1]}x{grid.shape[0]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
