"""
Animate a single trajectory walking over the V(x) flow-skeleton background.

Background (rendered once):
  - V = -log ρ contour (magma_r)
  - White flow streamlines
  - Basin centers (★)
  - Inter-basin geodesics with V* labels

Foreground (per frame k = 0..max_step):
  - Trail line from step 0 to step k (current trajectory's PCA-2 path)
  - Highlighted dot at step k
  - Vertical line on a small inset showing 'time elapsed'

Picks one (condition, family, ic, run) tuple per CLI invocation.

Output:
  data/<exp>/reports/perturbation/animation_<cond>_<famfrag>_<ic>_<run>.gif
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
from sklearn.decomposition import PCA

from src.experiments.dynamics.field_plots import _clean_uv_for_streamplot
from src.experiments.perturbation.field_plots import _compute_per_condition_fields
from src.experiments.perturbation.flow_plots import _load
from src.experiments.perturbation.geodesic_skeleton import (
    _find_basin_centers, _grid_dijkstra, _potential_grid,
)
from src.utils.io import ensure_dir
from src.utils.logging import get_logger, setup_logging

log = get_logger(__name__)


CONDITIONS = ["control", "neutral", "lorem", "adversarial"]
COND_COLORS = {"control": "#4a90e2", "neutral": "#8b5cf6",
               "lorem": "#ff9800", "adversarial": "#d62728"}


def _draw_background(
    ax, X, Y, V, flow_field, pts, cond, n_basins=4,
):
    color = COND_COLORS[cond]
    ax.contourf(X, Y, V, levels=20, cmap="magma_r", alpha=0.85)
    ax.contour(X, Y, V, levels=10, colors="white", linewidths=0.3, alpha=0.35)
    if flow_field is not None:
        Xf, Yf, U, Vf, density, _ = flow_field
        U2, V2 = _clean_uv_for_streamplot(Xf, Yf, U, Vf, density)
        if (np.sqrt(U2**2 + V2**2) > 0).sum() > 10:
            ax.streamplot(
                Xf, Yf, U2, V2,
                color="white", linewidth=0.7, density=1.4, arrowsize=0.9,
                arrowstyle="-|>",
            )
    ax.scatter(pts[:, 0], pts[:, 1], s=0.4, alpha=0.06, color="#222", linewidths=0)

    centers = _find_basin_centers(V, n_max=n_basins)
    for (r, c) in centers:
        ax.scatter(X[r, c], Y[r, c], s=140, marker="*",
                   color=color, edgecolors="white", linewidths=1.0, zorder=12)
    for i in range(len(centers)):
        for j in range(i + 1, len(centers)):
            path = _grid_dijkstra(V, centers[i], centers[j])
            if not path:
                continue
            xs = np.array([X[r, c] for r, c in path])
            ys = np.array([Y[r, c] for r, c in path])
            v_path = np.array([V[r, c] for r, c in path])
            v_max = float(v_path.max())
            ax.plot(xs, ys, color=color, lw=1.2, alpha=0.6, zorder=10)
            mid = len(path) // 2
            ax.annotate(
                f"V*={v_max:.1f}",
                xy=(xs[mid], ys[mid]),
                xytext=(5, 5), textcoords="offset points",
                fontsize=7, color=color,
                bbox=dict(boxstyle="round,pad=0.2",
                          fc="white", ec=color, alpha=0.85, lw=0.5),
                zorder=14,
            )


def render_animation(
    exp_dir: Path, observable: str, override_step: int, is_dialog: bool,
    cond: str, family: str | None, ic: str | None, run: str | None,
    fps: int = 4, n_basins: int = 4, grid_n_v: int = 96, grid_n_flow: int = 32,
    n_trajs: int = 1, traj_seed: int = 0,
) -> None:
    vecs, meta = _load(exp_dir, observable, is_dialog)
    log.info("loaded %d points for %s", len(vecs), exp_dir.name)

    out_dir = exp_dir / "reports" / "perturbation"
    ensure_dir(out_dir)

    Z = PCA(n_components=2, random_state=42).fit_transform(vecs)
    x_min, x_max = float(Z[:, 0].min()), float(Z[:, 0].max())
    y_min, y_max = float(Z[:, 1].min()), float(Z[:, 1].max())
    xpad = 0.05 * (x_max - x_min + 1e-9)
    ypad = 0.05 * (y_max - y_min + 1e-9)
    xb = (x_min - xpad, x_max + xpad)
    yb = (y_min - ypad, y_max + ypad)

    flow_fields = _compute_per_condition_fields(Z, meta, grid_n=grid_n_flow)

    sub_idx = (meta["regime"] == cond).values
    if sub_idx.sum() < 30:
        raise ValueError(f"insufficient {cond} data")
    pts = Z[sub_idx]
    X, Y, V = _potential_grid(pts, xb, yb, grid_n=grid_n_v)

    # Build candidate trajectory list
    sub_meta = meta[sub_idx].reset_index(drop=True).copy()
    sub_meta["_orig_idx"] = meta.index[sub_idx]
    groups = sub_meta.groupby(["prompt_family", "initial_condition_id", "run_id"])
    keys = list(groups.groups.keys())
    if family is not None and ic is not None and run is not None:
        target = (family, ic, run)
        if target not in groups.groups:
            log.warning("requested key %s not found, picking first", target)
            target = keys[0]
        targets = [target]
    elif n_trajs <= 1:
        targets = [keys[0]]
    else:
        rng = np.random.default_rng(traj_seed)
        n_pick = min(n_trajs, len(keys))
        idxs = rng.choice(len(keys), size=n_pick, replace=False)
        targets = [keys[int(i)] for i in idxs]
    log.info("animating %d trajectories", len(targets))

    # Color palette: use tab10 for trajectory IDs, but condition color stays
    # the dominant theme via the kick arrows.
    palette = plt.get_cmap("tab10").colors
    cond_color = COND_COLORS[cond]

    # Build per-trajectory data
    traj_data = []
    for ti, t in enumerate(targets):
        grp = groups.get_group(t).sort_values("step").reset_index(drop=True)
        orig_idxs = grp["_orig_idx"].to_numpy()
        traj_xy = Z[orig_idxs]
        steps_t = grp["step"].to_numpy()
        post = [(i, s) for i, s in enumerate(steps_t) if s >= override_step]
        if post:
            i_post = post[0][0]
            i_pre = max(0, i_post - 1)
        else:
            i_post = i_pre = None
        traj_data.append({
            "target": t, "traj_xy": traj_xy, "steps": steps_t,
            "i_pre": i_pre, "i_post": i_post,
            "color": palette[ti % len(palette)],
        })

    # For frame-plan logic, use the first trajectory's step array (assumed
    # same across all in a given experiment).
    steps = traj_data[0]["steps"]
    i_pre_g = traj_data[0]["i_pre"]
    i_post_g = traj_data[0]["i_post"]
    color = cond_color  # kept for compatibility with title text below
    target = targets[0]
    traj_xy = traj_data[0]["traj_xy"]  # used by title labelling only

    # Build expanded frame plan:
    #   for each frame: (kind, traj_index, alpha_kick)
    #   kind ∈ {"step", "pre_pause", "kick", "post_pause", "post_step"}
    HOLD_PRE = 4
    HOLD_POST = 3
    KICK_SUBFRAMES = 8

    plan: list[dict] = []
    n_steps = len(steps)
    for k in range(n_steps):
        plan.append({"kind": "step", "k": k, "interp": 0.0})
        if i_post_g is not None and k == i_pre_g and (cond != "control"):
            for _ in range(HOLD_PRE):
                plan.append({"kind": "pre_pause", "k": i_pre_g, "interp": 0.0})
            for s in range(1, KICK_SUBFRAMES + 1):
                plan.append({
                    "kind": "kick", "k": i_pre_g,
                    "interp": s / KICK_SUBFRAMES,
                })
            for _ in range(HOLD_POST):
                plan.append({"kind": "post_pause", "k": i_post_g, "interp": 1.0})

    fig, ax = plt.subplots(figsize=(11, 9))
    _draw_background(ax, X, Y, V, flow_fields.get(cond), pts, cond,
                     n_basins=n_basins)
    ax.set_xlim(xb); ax.set_ylim(yb)
    ax.set_xlabel("PCA-1"); ax.set_ylabel("PCA-2")
    ax.grid(alpha=0.15)
    title_obj = ax.set_title("", fontsize=12, color=cond_color)

    # Build per-trajectory artist sets
    for d in traj_data:
        c = d["color"]
        d["trail"], = ax.plot([], [], color=c, lw=1.6, alpha=0.95, zorder=20)
        d["head"] = ax.scatter([], [], s=120, marker="o", color=c,
                               edgecolors="white", linewidths=1.0, zorder=23)
        d["pre_dot"] = ax.scatter([], [], s=50, marker="o", color="white",
                                  edgecolors=c, linewidths=1.0, zorder=21)
        d["kick_line"], = ax.plot(
            [], [], color="white", lw=2.0, alpha=0.95, zorder=22,
        )
        d["kick_arrow"] = ax.annotate(
            "", xy=(0, 0), xytext=(0, 0),
            arrowprops=dict(arrowstyle="-|>", color="white",
                            mutation_scale=18, lw=0),
            zorder=24,
        )
        d["kick_arrow"].set_visible(False)

    def init():
        for d in traj_data:
            d["trail"].set_data([], [])
            d["head"].set_offsets(np.empty((0, 2)))
            d["pre_dot"].set_offsets(np.empty((0, 2)))
            d["kick_line"].set_data([], [])
            d["kick_arrow"].set_visible(False)
        return (title_obj,) + tuple(
            a for d in traj_data
            for a in (d["trail"], d["head"], d["pre_dot"], d["kick_line"], d["kick_arrow"])
        )

    def update(frame):
        spec = plan[frame]
        kind = spec["kind"]
        k = spec["k"]
        interp = spec["interp"]

        for d in traj_data:
            xy = d["traj_xy"]
            ip = d["i_pre"]; iq = d["i_post"]

            if kind in ("step", "pre_pause"):
                d["trail"].set_data(xy[:k+1, 0], xy[:k+1, 1])
                d["head"].set_offsets(xy[k:k+1])
                if iq is not None and k > iq:
                    a = xy[ip]; b = xy[iq]
                    d["pre_dot"].set_offsets([a])
                    d["kick_line"].set_data([a[0], b[0]], [a[1], b[1]])
                    d["kick_arrow"].xy = (b[0], b[1])
                    d["kick_arrow"].set_position((a[0], a[1]))
                    d["kick_arrow"].set_visible(True)
                else:
                    d["pre_dot"].set_offsets(np.empty((0, 2)))
                    d["kick_line"].set_data([], [])
                    d["kick_arrow"].set_visible(False)
            elif kind == "kick" and iq is not None:
                a = xy[ip]; b = xy[iq]
                cur = a + interp * (b - a)
                d["trail"].set_data(xy[:ip+1, 0], xy[:ip+1, 1])
                d["head"].set_offsets([cur])
                d["pre_dot"].set_offsets([a])
                d["kick_line"].set_data([a[0], cur[0]], [a[1], cur[1]])
                d["kick_arrow"].set_visible(False)
            elif kind == "post_pause" and iq is not None:
                a = xy[ip]; b = xy[iq]
                d["trail"].set_data(xy[:iq+1, 0], xy[:iq+1, 1])
                d["head"].set_offsets(xy[iq:iq+1])
                d["pre_dot"].set_offsets([a])
                d["kick_line"].set_data([a[0], b[0]], [a[1], b[1]])
                d["kick_arrow"].xy = (b[0], b[1])
                d["kick_arrow"].set_position((a[0], a[1]))
                d["kick_arrow"].set_visible(True)

        if kind == "pre_pause":
            label = f"step {int(steps[k])}/{int(steps[-1])}  ← perturbation incoming"
        elif kind == "kick":
            label = (f"step {int(steps[i_pre_g])} → {int(steps[i_post_g])}  "
                     f"|  PERTURBATION KICK ({int(interp*100)}%)")
        elif kind == "post_pause":
            label = f"step {int(steps[i_post_g])}  |  post-kick"
        else:
            label = f"step {int(steps[k])}/{int(steps[-1])}"

        title_obj.set_text(
            f"{cond}  |  N={len(traj_data)} trajectories  |  {label}"
        )
        return (title_obj,) + tuple(
            a for d in traj_data
            for a in (d["trail"], d["head"], d["pre_dot"], d["kick_line"], d["kick_arrow"])
        )

    n_frames = len(plan)
    ani = animation.FuncAnimation(
        fig, update, init_func=init, frames=n_frames,
        interval=1000 // fps, blit=False, repeat=True,
    )

    if len(traj_data) == 1:
        famfrag = target[0].replace(" ", "_")[:16]
        out = out_dir / f"animation_{cond}_{famfrag}_{target[1]}_{target[2]}.gif"
    else:
        out = out_dir / f"animation_{cond}_n{len(traj_data)}_seed{traj_seed}.gif"
    ani.save(out, writer=animation.PillowWriter(fps=fps), dpi=120)
    plt.close(fig)
    log.info("wrote %s (%d frames at %d fps)", out, n_frames, fps)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="perturb_trajectory_animation")
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--observable", default="context_tail")
    parser.add_argument("--override-step", type=int, default=15)
    parser.add_argument("--is-dialog", action="store_true")
    parser.add_argument("--condition", default="adversarial",
                        choices=CONDITIONS)
    parser.add_argument("--family", default=None,
                        help="prompt family name (default: first available)")
    parser.add_argument("--ic", default=None, help="initial condition id")
    parser.add_argument("--run", default=None, help="run id")
    parser.add_argument("--fps", type=int, default=4)
    parser.add_argument("--n-trajs", type=int, default=1,
                        help="number of trajectories to animate together (default 1)")
    parser.add_argument("--traj-seed", type=int, default=0,
                        help="seed for trajectory sampling when n-trajs > 1")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    setup_logging(args.log_level, None)

    exp_dir = Path(args.data_dir) / args.experiment
    if not exp_dir.exists():
        raise FileNotFoundError(exp_dir)

    render_animation(
        exp_dir, args.observable, args.override_step, args.is_dialog,
        cond=args.condition, family=args.family, ic=args.ic, run=args.run,
        fps=args.fps, n_trajs=args.n_trajs, traj_seed=args.traj_seed,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
