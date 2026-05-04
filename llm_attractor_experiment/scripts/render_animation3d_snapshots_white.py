"""
Render a 2x2 grid of static 3D-PCA snapshots on a *white* background,
one panel per perturbation condition. Bypasses the MP4 pipeline used by
`trajectory_animation_3d.py` — for paper figures we only need a single
post-kick frame per condition, not the full flythrough.

Output:
    data/<exp>/reports/perturbation/animation3d_snapshots_white.png

The heavy bits (data load, PCA-3, trajectory selection, iso-mesh
construction) are reused from `src.experiments.perturbation.trajectory_animation_3d`;
we just re-style for paper-friendly white background and skip the
animation loop.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Line3DCollection, Poly3DCollection
from sklearn.decomposition import PCA

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from src.experiments.perturbation.flow_plots import _load
from src.experiments.perturbation.trajectory_animation_3d import (  # noqa: E402
    _compute_iso_meshes,
)

CONDITIONS = ("control", "neutral", "lorem", "adversarial")
COND_COLORS = {"control": "#4a90e2", "neutral": "#8b5cf6",
               "lorem": "#ff9800", "adversarial": "#d62728"}
KICK_RED = "#d62728"


def _fading_trail_white_bg(
    xyz_prefix: np.ndarray, color_rgb: tuple[float, float, float],
    base_alpha: float = 0.95, tail_alpha: float = 0.10,
) -> tuple[np.ndarray, np.ndarray]:
    """Like the animation's fading trail, but colored for white-bg readability.

    Returns (segments, rgba_colors) for a Line3DCollection with the
    given trajectory color and alpha decreasing from head → tail."""
    n = len(xyz_prefix)
    if n < 2:
        return np.zeros((0, 2, 3)), np.zeros((0, 4))
    segs = np.stack([xyz_prefix[:-1], xyz_prefix[1:]], axis=1)
    n_segs = len(segs)
    t = np.arange(n_segs) / max(n_segs - 1, 1)
    alphas = tail_alpha + (base_alpha - tail_alpha) * t
    colors = np.zeros((n_segs, 4))
    colors[:, 0] = color_rgb[0]
    colors[:, 1] = color_rgb[1]
    colors[:, 2] = color_rgb[2]
    colors[:, 3] = alphas
    return segs, colors


def _add_meshes_white_bg(ax, meshes: list[dict]) -> None:
    """Add iso-density shells; on white bg we drop edge-color overlay
    (the white edges from the dark-bg version are invisible)."""
    for m in meshes:
        verts = m["verts"]; faces = m["faces"]
        c = m["color"]; a = m["alpha"]
        mesh = Poly3DCollection(verts[faces])
        mesh.set_facecolor((c[0], c[1], c[2], a))
        mesh.set_edgecolor((0.4, 0.4, 0.4, 0.05))
        mesh.set_linewidth(0.18)
        ax.add_collection3d(mesh)


def _render_panel(
    ax, *, pts: np.ndarray, traj_data: list[dict], meshes: list[dict],
    xb: tuple, yb: tuple, zb: tuple, cond: str, cond_color: str,
    n_post_steps: int = 24,
) -> None:
    ax.set_facecolor("white")
    ax.set_xlim(*xb); ax.set_ylim(*yb); ax.set_zlim(*zb)
    ax.set_xlabel("PCA-1", color="#333", labelpad=2)
    ax.set_ylabel("PCA-2", color="#333", labelpad=2)
    ax.set_zlabel("PCA-3", color="#333", labelpad=2)
    ax.tick_params(colors="#333", labelsize=7)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor((1, 1, 1, 0))
        axis.pane.set_edgecolor("#bbbbbb")

    if meshes:
        _add_meshes_white_bg(ax, meshes)

    # background scatter — light grey dots so volume is hinted at without
    # overwhelming the trajectory traces.
    ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2],
               s=1.2, alpha=0.10, color="#666666", linewidths=0)

    for d in traj_data:
        xyz = d["traj_xyz"]
        ip = d["i_pre"]; iq = d["i_post"]
        # how many steps to show post-kick: bound by available steps
        if iq is not None:
            stop = min(iq + n_post_steps, len(xyz) - 1)
        else:
            stop = len(xyz) - 1
        rgb_hex = d["color"].lstrip("#")
        rgb = tuple(int(rgb_hex[i:i+2], 16) / 255.0 for i in (0, 2, 4))
        segs, cols = _fading_trail_white_bg(xyz[:stop+1], rgb)
        if len(segs) > 0:
            ax.add_collection3d(Line3DCollection(segs, colors=cols, linewidths=2.0))
        # head dot at current position
        head = xyz[stop]
        ax.scatter([head[0]], [head[1]], [head[2]], s=70, marker="o",
                   color=rgb, edgecolors="black", linewidths=0.7, zorder=10)

        # kick beam: pre-kick → post-kick displacement
        if iq is not None:
            a = xyz[ip]; b = xyz[iq]
            ax.plot([a[0], b[0]], [a[1], b[1]], [a[2], b[2]],
                    color=KICK_RED, lw=10, alpha=0.18, solid_capstyle="round")
            ax.plot([a[0], b[0]], [a[1], b[1]], [a[2], b[2]],
                    color=KICK_RED, lw=3.0, alpha=1.0, solid_capstyle="round",
                    zorder=11)
            ax.scatter([a[0]], [a[1]], [a[2]], s=120, marker="X",
                       color=KICK_RED, edgecolors="black", linewidths=1.0,
                       zorder=12)

    ax.view_init(elev=22, azim=-30)
    ax.set_title(f"{cond}", fontsize=12, color=cond_color, pad=2)


def _select_trajectories(
    Z: np.ndarray, meta, cond: str, override_step: int, n_trajs: int = 6,
    seed: int = 0,
) -> tuple[list[dict], np.ndarray]:
    sub_idx = (meta["regime"] == cond).values
    if sub_idx.sum() < 30:
        return [], np.zeros((0, 3))
    pts = Z[sub_idx]
    sub_meta = meta[sub_idx].reset_index(drop=True).copy()
    sub_meta["_orig_idx"] = meta.index[sub_idx]
    groups = sub_meta.groupby(["prompt_family", "initial_condition_id", "run_id"])
    keys = list(groups.groups.keys())
    rng = np.random.default_rng(seed)
    n_pick = min(n_trajs, len(keys))
    idxs = rng.choice(len(keys), size=n_pick, replace=False)
    targets = [keys[int(i)] for i in idxs]

    palette = ["#0066cc", "#cc6600", "#009933", "#990099",
               "#cc0066", "#666633", "#003366", "#663300"]

    kick_enabled = (cond != "control")
    traj_data = []
    for ti, t in enumerate(targets):
        grp = groups.get_group(t).sort_values("step").reset_index(drop=True)
        orig_idxs = grp["_orig_idx"].to_numpy()
        traj_xyz = Z[orig_idxs]
        steps_t = grp["step"].to_numpy()
        if kick_enabled:
            post = [(i, s) for i, s in enumerate(steps_t) if s >= override_step]
            if post:
                i_post = post[0][0]
                i_pre = max(0, i_post - 1)
            else:
                i_post = i_pre = None
        else:
            i_post = i_pre = None
        traj_data.append({
            "target": t, "traj_xyz": traj_xyz, "steps": steps_t,
            "i_pre": i_pre, "i_post": i_post,
            "color": palette[ti % len(palette)],
        })
    return traj_data, pts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", default="exp_perturb_O1_pilot")
    ap.add_argument("--observable", default="context_tail")
    ap.add_argument("--override-step", type=int, default=15)
    ap.add_argument("--n-trajs", type=int, default=6)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--field-grid", type=int, default=48)
    ap.add_argument("--n-post", type=int, default=10,
                    help="trajectory steps to show after the kick")
    args = ap.parse_args()

    exp_dir = REPO / "data" / args.exp
    if not exp_dir.is_dir():
        print(f"error: {exp_dir} not found")
        return 1

    vecs, meta = _load(exp_dir, args.observable, is_dialog=False)
    print(f"loaded {len(vecs)} points")

    pca = PCA(n_components=3, random_state=42).fit(vecs)
    Z = pca.transform(vecs)
    print(f"PCA-3 explained variance: {float(pca.explained_variance_ratio_.sum()):.3f}")

    def _pad(lo, hi):
        p = 0.05 * (hi - lo + 1e-9)
        return lo - p, hi + p
    xb = _pad(float(Z[:, 0].min()), float(Z[:, 0].max()))
    yb = _pad(float(Z[:, 1].min()), float(Z[:, 1].max()))
    zb = _pad(float(Z[:, 2].min()), float(Z[:, 2].max()))

    fig = plt.figure(figsize=(18, 14), facecolor="white")
    fig.patch.set_facecolor("white")

    for i, cond in enumerate(CONDITIONS):
        ax = fig.add_subplot(2, 2, i + 1, projection="3d")
        traj_data, pts = _select_trajectories(
            Z, meta, cond, args.override_step,
            n_trajs=args.n_trajs, seed=args.seed,
        )
        if len(traj_data) == 0:
            ax.set_title(f"{cond} (no data)")
            continue
        meshes = _compute_iso_meshes(pts, xb, yb, zb, grid_n=args.field_grid)
        _render_panel(
            ax, pts=pts, traj_data=traj_data, meshes=meshes,
            xb=xb, yb=yb, zb=zb,
            cond=cond, cond_color=COND_COLORS[cond],
            n_post_steps=args.n_post,
        )

    fig.suptitle(
        "3D PCA flow snapshots — post-kick mid-recovery (white background)\n"
        "iso-density shells (plasma)  |  fading trails colored per trajectory  "
        "|  red beam = perturbation kick (step 14→15)",
        fontsize=14, y=0.99, color="#222",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))

    out_dir = exp_dir / "reports" / "perturbation"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "animation3d_snapshots_white.png"
    fig.savefig(out_path, dpi=180, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
