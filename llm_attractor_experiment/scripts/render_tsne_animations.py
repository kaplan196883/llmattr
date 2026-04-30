"""
Two t-SNE animations for a perturbation experiment, written side-by-side
to show two complementary views of trajectory dynamics:

  Version A — "joint flow":
      Run ONE t-SNE on the full point cloud (all conditions × all
      trajectories × all steps) → fixed 2-D coordinate system. Animate
      step-by-step: each frame k shows where every trajectory is at
      step k as a marker, with a fading trail of the recent steps.
      Watching the animation, you see trajectories *flow through* the
      fixed t-SNE manifold; the perturbation kick at step 15 is the
      moment perturbed clouds visibly tear away from the control cloud.

  Version B — "per-step refit":
      For every step k, refit t-SNE on JUST that step's points
      (per-condition: 50 points per fit, no warm-start). The
      coordinate system jumps frame-to-frame — that's intentional. The
      animation reveals how the *cluster structure* itself evolves: at
      step 0 points are roughly uniform (seed-determined); by mid-run
      the per-step t-SNE resolves tight basins. Discontinuity is the
      point — it stops the animation from hiding structure changes
      under a global frame.

Both versions are saved as 4-panel MP4s (one panel per perturbation
condition, identical layout to fig11) plus a single static composite
PNG sampled at a post-kick step for paper inclusion.

Output (default exp = exp_perturb_O1_pilot):
    data/<exp>/reports/perturbation/tsne_anim_joint.mp4
    data/<exp>/reports/perturbation/tsne_anim_joint_snapshot.png
    data/<exp>/reports/perturbation/tsne_anim_refit.mp4
    data/<exp>/reports/perturbation/tsne_anim_refit_snapshot.png

Usage:
    python -m scripts.render_tsne_animations
    python -m scripts.render_tsne_animations --exp exp_perturb_O1_pilot \
        --observable context_tail --fps 4 --snapshot-step 24

Notes:
- Joint fit: single t-SNE on ~6,000 points. Takes ~30 s.
- Per-step refit: 30 × 4 = 120 t-SNE fits on 50 points each. Fast (<1 min).
- We use `init="pca"` for both to get reproducible-ish layouts; the
  per-step refit accepts whatever rotation/reflection t-SNE picks for
  each step (the user explicitly asked for "accept the jumps").
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from src.experiments.perturbation.flow_plots import _load  # noqa: E402

CONDITIONS = ("control", "neutral", "lorem", "adversarial")
COND_COLORS = {"control": "#4a90e2", "neutral": "#8b5cf6",
               "lorem": "#ff9800", "adversarial": "#d62728"}
KICK_STEP = 15  # injection occurs between step 14 and step 15


def _build_panel_grid(fig):
    axes = []
    for i in range(4):
        ax = fig.add_subplot(2, 2, i + 1)
        axes.append(ax)
    return axes


def _style_axis(ax, cond: str, k: int, n_steps: int, kicked: bool):
    ax.set_facecolor("white")
    ax.set_xticks([]); ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_edgecolor("#aaaaaa")
        spine.set_linewidth(0.6)
    label = f"{cond}  |  step {k}/{n_steps - 1}"
    if kicked:
        label += "  ← post-kick"
    ax.set_title(label, fontsize=11, color=COND_COLORS[cond], pad=2)


def _fading_trail_segments(
    xy_prefix: np.ndarray, base_color: tuple[float, float, float],
    base_alpha: float = 0.95, tail_alpha: float = 0.05,
):
    """Return (segments, rgba) for a LineCollection with alpha decreasing
    head→tail. xy_prefix is (n_steps_so_far, 2)."""
    n = len(xy_prefix)
    if n < 2:
        return np.zeros((0, 2, 2)), np.zeros((0, 4))
    segs = np.stack([xy_prefix[:-1], xy_prefix[1:]], axis=1)
    n_segs = len(segs)
    t = np.arange(n_segs) / max(n_segs - 1, 1)
    alphas = tail_alpha + (base_alpha - tail_alpha) * t
    rgba = np.zeros((n_segs, 4))
    rgba[:, 0] = base_color[0]
    rgba[:, 1] = base_color[1]
    rgba[:, 2] = base_color[2]
    rgba[:, 3] = alphas
    return segs, rgba


def _hex_to_rgb(h: str) -> tuple[float, float, float]:
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))


def _build_traj_index(meta) -> dict[str, list[tuple[int, np.ndarray]]]:
    """Return {condition: [(traj_id, indices_in_step_order)]} where indices
    point into the full vecs/meta arrays. Each trajectory's indices are
    sorted by step ascending."""
    out: dict[str, list[tuple[int, np.ndarray]]] = {c: [] for c in CONDITIONS}
    for cond in CONDITIONS:
        sub = meta[meta["regime"] == cond].copy()
        if len(sub) == 0:
            continue
        sub["_orig_idx"] = sub.index
        groups = sub.groupby(["prompt_family", "initial_condition_id", "run_id"])
        for tid, (_, grp) in enumerate(groups):
            ordered = grp.sort_values("step")
            out[cond].append((tid, ordered["_orig_idx"].to_numpy()))
    return out


def _ensure_kick_dot(ax, x, y, color="#d62728"):
    ax.scatter([x], [y], s=140, marker="X", color=color,
               edgecolors="black", linewidths=0.9, zorder=15)


def render_joint_flow(
    vecs: np.ndarray, meta, n_steps: int,
    out_mp4: Path, snapshot_step: int, snapshot_png: Path,
    fps: int = 4,
) -> None:
    """Version A: one joint t-SNE → fixed coords, animate over step k."""
    print(f"[joint] running t-SNE on {len(vecs)} points...")
    Z = TSNE(
        n_components=2, init="pca", learning_rate="auto",
        perplexity=min(30, max(5, len(vecs) // 50)), random_state=42,
        max_iter=1500,
    ).fit_transform(vecs)
    print(f"[joint] done. coord range: x∈[{Z[:,0].min():.1f},{Z[:,0].max():.1f}] "
          f"y∈[{Z[:,1].min():.1f},{Z[:,1].max():.1f}]")

    def _pad(lo, hi):
        p = 0.05 * (hi - lo + 1e-9)
        return lo - p, hi + p
    xlim = _pad(float(Z[:, 0].min()), float(Z[:, 0].max()))
    ylim = _pad(float(Z[:, 1].min()), float(Z[:, 1].max()))

    traj_idx = _build_traj_index(meta)

    # Build per-condition per-trajectory step-ordered xy arrays once.
    cond_trajs: dict[str, list[np.ndarray]] = {c: [] for c in CONDITIONS}
    for cond, items in traj_idx.items():
        for _tid, idxs in items:
            cond_trajs[cond].append(Z[idxs])  # (n_steps, 2)

    fig = plt.figure(figsize=(14, 12), facecolor="white")
    axes = _build_panel_grid(fig)
    for ax in axes:
        ax.set_xlim(*xlim); ax.set_ylim(*ylim)

    fig.suptitle(
        "Joint t-SNE flow: one shared embedding, trajectories animated step-by-step\n"
        "fading trail = recent steps  |  red X = kick injection point  "
        "|  perturbation injection at step 15",
        fontsize=13, color="#222", y=0.99,
    )

    def _render_frame(k: int) -> None:
        for ax, cond in zip(axes, CONDITIONS):
            ax.clear()
            ax.set_xlim(*xlim); ax.set_ylim(*ylim)
            kicked = (k >= KICK_STEP) and (cond != "control")
            _style_axis(ax, cond, k, n_steps, kicked)

            base_rgb = _hex_to_rgb(COND_COLORS[cond])
            trajs = cond_trajs[cond]
            # Faint full-cloud scatter for context.
            full = np.concatenate(trajs, axis=0) if trajs else np.zeros((0, 2))
            if len(full):
                ax.scatter(full[:, 0], full[:, 1], s=2, alpha=0.05,
                           color="#888888", linewidths=0)

            # Per-trajectory fading trails to step k + head dot.
            all_segs = []
            all_cols = []
            head_x, head_y = [], []
            for tr in trajs:
                k_clip = min(k, len(tr) - 1)
                prefix = tr[:k_clip + 1]
                segs, cols = _fading_trail_segments(prefix, base_rgb)
                if len(segs) > 0:
                    all_segs.append(segs); all_cols.append(cols)
                head_x.append(tr[k_clip, 0])
                head_y.append(tr[k_clip, 1])

            if all_segs:
                lc = LineCollection(np.concatenate(all_segs, axis=0),
                                    colors=np.concatenate(all_cols, axis=0),
                                    linewidths=1.0)
                ax.add_collection(lc)

            ax.scatter(head_x, head_y, s=22, color=base_rgb,
                       edgecolors="black", linewidths=0.4, zorder=10)

            # Kick markers: at step 15 onward, mark each trajectory's
            # step-14 position with a red X (the launch point of the kick).
            if cond != "control" and k >= KICK_STEP:
                kx = [tr[KICK_STEP - 1, 0] for tr in trajs
                      if len(tr) > KICK_STEP - 1]
                ky = [tr[KICK_STEP - 1, 1] for tr in trajs
                      if len(tr) > KICK_STEP - 1]
                ax.scatter(kx, ky, s=18, marker="x", color="#d62728",
                           alpha=0.6, linewidths=0.8, zorder=8)

    # Snapshot for paper.
    _render_frame(snapshot_step)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(snapshot_png, dpi=170, facecolor="white", bbox_inches="tight")
    print(f"[joint] wrote {snapshot_png}")

    # Animation
    print(f"[joint] rendering MP4 ({n_steps} frames at {fps} fps)...")
    ani = animation.FuncAnimation(
        fig, _render_frame, frames=n_steps, interval=1000 // fps, blit=False,
    )
    try:
        ani.save(out_mp4, writer=animation.FFMpegWriter(
            fps=fps, codec="libx264", bitrate=2400,
        ), dpi=140, savefig_kwargs={"facecolor": "white"})
    except (FileNotFoundError, RuntimeError) as e:
        print(f"[joint] MP4 writer failed ({e}); falling back to GIF")
        out_gif = out_mp4.with_suffix(".gif")
        ani.save(out_gif, writer=animation.PillowWriter(fps=fps), dpi=120)
        print(f"[joint] wrote {out_gif}")
    else:
        print(f"[joint] wrote {out_mp4}")
    plt.close(fig)


def render_per_step_refit(
    vecs: np.ndarray, meta, n_steps: int,
    out_mp4: Path, snapshot_step: int, snapshot_png: Path,
    fps: int = 4,
) -> None:
    """Version B: refit t-SNE *per step, per condition* (no warm start).
    Coordinates jump frame-to-frame — the animation reveals how cluster
    structure evolves at each step independent of a global frame."""
    fig = plt.figure(figsize=(14, 12), facecolor="white")
    axes = _build_panel_grid(fig)

    # Pre-compute per (step, cond) t-SNE coords. ~120 fits on ~50 points.
    print(f"[refit] precomputing {n_steps} × {len(CONDITIONS)} t-SNE fits...")
    cond_step_coords: dict[tuple[str, int], np.ndarray] = {}
    cond_step_meta: dict[tuple[str, int], np.ndarray] = {}  # which traj_id each row is
    for cond in CONDITIONS:
        cond_mask = (meta["regime"] == cond).values
        sub_vecs = vecs[cond_mask]
        sub_meta = meta[cond_mask].reset_index(drop=True)
        # group rows by (prompt_family, ic, run) → traj id, then by step
        sub_meta["_traj_id"] = sub_meta.groupby(
            ["prompt_family", "initial_condition_id", "run_id"]
        ).ngroup()
        for k in range(n_steps):
            row_mask = (sub_meta["step"] == k).values
            pts = sub_vecs[row_mask]
            ids = sub_meta.loc[row_mask, "_traj_id"].to_numpy()
            if len(pts) < 4:
                cond_step_coords[(cond, k)] = np.zeros((0, 2))
                cond_step_meta[(cond, k)] = ids
                continue
            # Pre-reduce dimensionality before t-SNE. With 50 points in
            # 1536-D, all pairwise distances are nearly equal (curse of
            # dimensionality), so t-SNE artificially uniformizes the cloud.
            # Standard fix: PCA → ~30D first, then t-SNE on the dense
            # representation. Cap PCA dim at min(50, n-1) so it always fits.
            pca_dim = min(30, len(pts) - 1, pts.shape[1])
            pts_low = PCA(n_components=pca_dim, random_state=42).fit_transform(pts)
            # Lower perplexity on small samples — keeps t-SNE sensitive to
            # local structure rather than smoothing it away.
            perp = min(8, max(2, len(pts) // 8))
            try:
                xy = TSNE(
                    n_components=2, init="pca", learning_rate="auto",
                    perplexity=perp, random_state=42, max_iter=1000,
                ).fit_transform(pts_low)
            except Exception as e:
                print(f"[refit] step {k} {cond}: t-SNE failed ({e})")
                xy = np.zeros((len(pts), 2))
            cond_step_coords[(cond, k)] = xy
            cond_step_meta[(cond, k)] = ids
        print(f"[refit] {cond} done")

    # Compute per-(cond, step) bounds — accept that they differ across frames.
    fig.suptitle(
        "Per-step refit t-SNE: each frame is an independent fit on that step's points\n"
        "no warm-start, coordinate system jumps frame-to-frame  "
        "|  reveals cluster structure evolution",
        fontsize=13, color="#222", y=0.99,
    )

    def _render_frame(k: int) -> None:
        for ax, cond in zip(axes, CONDITIONS):
            ax.clear()
            kicked = (k >= KICK_STEP) and (cond != "control")
            _style_axis(ax, cond, k, n_steps, kicked)
            xy = cond_step_coords[(cond, k)]
            if len(xy) == 0:
                ax.text(0.5, 0.5, "(insufficient data)",
                        ha="center", va="center", transform=ax.transAxes,
                        color="#888")
                continue
            ids = cond_step_meta[(cond, k)]
            base_rgb = _hex_to_rgb(COND_COLORS[cond])
            ax.scatter(xy[:, 0], xy[:, 1], s=28, color=base_rgb,
                       edgecolors="black", linewidths=0.4, alpha=0.85,
                       zorder=10)
            # autoscale per-frame; pad 5%
            lo_x, hi_x = float(xy[:, 0].min()), float(xy[:, 0].max())
            lo_y, hi_y = float(xy[:, 1].min()), float(xy[:, 1].max())
            px = 0.07 * (hi_x - lo_x + 1e-9); py = 0.07 * (hi_y - lo_y + 1e-9)
            ax.set_xlim(lo_x - px, hi_x + px); ax.set_ylim(lo_y - py, hi_y + py)

    # Snapshot for paper.
    _render_frame(snapshot_step)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(snapshot_png, dpi=170, facecolor="white", bbox_inches="tight")
    print(f"[refit] wrote {snapshot_png}")

    print(f"[refit] rendering MP4 ({n_steps} frames at {fps} fps)...")
    ani = animation.FuncAnimation(
        fig, _render_frame, frames=n_steps, interval=1000 // fps, blit=False,
    )
    try:
        ani.save(out_mp4, writer=animation.FFMpegWriter(
            fps=fps, codec="libx264", bitrate=2400,
        ), dpi=140, savefig_kwargs={"facecolor": "white"})
    except (FileNotFoundError, RuntimeError) as e:
        print(f"[refit] MP4 writer failed ({e}); falling back to GIF")
        out_gif = out_mp4.with_suffix(".gif")
        ani.save(out_gif, writer=animation.PillowWriter(fps=fps), dpi=120)
        print(f"[refit] wrote {out_gif}")
    else:
        print(f"[refit] wrote {out_mp4}")
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", default="exp_perturb_O1_pilot")
    ap.add_argument("--observable", default="context_tail")
    ap.add_argument("--is-dialog", action="store_true")
    ap.add_argument("--fps", type=int, default=4)
    ap.add_argument("--snapshot-step", type=int, default=24,
                    help="step to sample for static PNG snapshot")
    ap.add_argument("--skip-joint", action="store_true")
    ap.add_argument("--skip-refit", action="store_true")
    args = ap.parse_args()

    exp_dir = REPO / "data" / args.exp
    if not exp_dir.is_dir():
        print(f"error: {exp_dir} not found")
        return 1

    vecs, meta = _load(exp_dir, args.observable, is_dialog=args.is_dialog)
    n_steps = int(meta["step"].max()) + 1
    print(f"loaded {len(vecs)} points, {n_steps} steps")

    out_dir = exp_dir / "reports" / "perturbation"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_joint:
        render_joint_flow(
            vecs, meta, n_steps,
            out_mp4=out_dir / "tsne_anim_joint.mp4",
            snapshot_step=args.snapshot_step,
            snapshot_png=out_dir / "tsne_anim_joint_snapshot.png",
            fps=args.fps,
        )
    if not args.skip_refit:
        render_per_step_refit(
            vecs, meta, n_steps,
            out_mp4=out_dir / "tsne_anim_refit.mp4",
            snapshot_step=args.snapshot_step,
            snapshot_png=out_dir / "tsne_anim_refit_snapshot.png",
            fps=args.fps,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
