"""
Animate trajectories in 3D PCA space (first 3 principal components).

Same multi-trajectory + perturbation-kick logic as the 2D version, lifted
into 3D. Skips the V landscape and streamlines (those are inherently 2D);
background is a faint scatter of all condition's points so the cloud
shape is visible. Camera optionally rotates frame-by-frame.

Output:
  data/<exp>/reports/perturbation/animation3d_<cond>_n<N>_seed<S>.gif
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Line3DCollection, Poly3DCollection
from PIL import Image
from scipy.ndimage import gaussian_filter
from skimage.measure import marching_cubes
from sklearn.decomposition import PCA

from src.experiments.perturbation.flow_plots import _load
from src.utils.io import ensure_dir
from src.utils.logging import get_logger, setup_logging

log = get_logger(__name__)


CONDITIONS = ["control", "neutral", "lorem", "adversarial"]
COND_COLORS = {"control": "#4a90e2", "neutral": "#8b5cf6",
               "lorem": "#ff9800", "adversarial": "#d62728"}


def _compute_iso_meshes(
    pts: np.ndarray,
    xb: tuple[float, float], yb: tuple[float, float], zb: tuple[float, float],
    grid_n: int = 48, sigma: float = 1.8,
    levels_frac: tuple[float, ...] = (0.04, 0.10, 0.20, 0.35, 0.55),
    cmap_name: str = "plasma",
) -> list[dict]:
    """Compute iso-surface meshes from the cloud's 3D density.

    Returns a list of dicts: {verts, faces, color (rgba), alpha} ordered
    outer→inner so callers can add them in alpha-layering order.
    """
    x_edges = np.linspace(*xb, grid_n + 1)
    y_edges = np.linspace(*yb, grid_n + 1)
    z_edges = np.linspace(*zb, grid_n + 1)
    H, _ = np.histogramdd(pts, bins=(x_edges, y_edges, z_edges))
    H = gaussian_filter(H, sigma=sigma)
    h_max = float(H.max())
    out: list[dict] = []
    if h_max <= 0:
        log.warning("density max=%.3f, no isosurfaces drawn", h_max)
        return out

    dx = (xb[1] - xb[0]) / grid_n
    dy = (yb[1] - yb[0]) / grid_n
    dz = (zb[1] - zb[0]) / grid_n
    spacing = (dx, dy, dz)

    cmap = plt.get_cmap(cmap_name)
    n_levels = len(levels_frac)
    for i, frac in enumerate(levels_frac):
        level = h_max * frac
        try:
            verts, faces, _, _ = marching_cubes(H, level=level, spacing=spacing)
        except (ValueError, RuntimeError) as e:
            log.debug("marching_cubes skip level=%.3f: %s", level, e)
            continue
        verts = verts.copy()
        verts[:, 0] += xb[0]
        verts[:, 1] += yb[0]
        verts[:, 2] += zb[0]
        t = i / max(n_levels - 1, 1)
        color_pos = 0.10 + 0.80 * t
        rgba = cmap(color_pos)
        alpha = 0.025 + 0.13 * t  # outer 0.025, inner 0.155 — softer field
        out.append({
            "verts": verts, "faces": faces,
            "color": (rgba[0], rgba[1], rgba[2]), "alpha": alpha,
        })
    log.info("computed %d/%d iso-surfaces", len(out), n_levels)
    return out


def _fading_trail_data(xyz_prefix: np.ndarray, base_alpha: float = 1.0,
                       tail_alpha: float = 0.04) -> tuple[np.ndarray, np.ndarray]:
    """Build (segments, rgba_colors) for a Line3DCollection with alpha
    decreasing from head (most recent) → tail (oldest). White color."""
    n = len(xyz_prefix)
    if n < 2:
        return np.zeros((0, 2, 3)), np.zeros((0, 4))
    segs = np.stack([xyz_prefix[:-1], xyz_prefix[1:]], axis=1)  # (n-1, 2, 3)
    n_segs = len(segs)
    # segment i (0..n_segs-1) is between point i and point i+1; head segment
    # is the last one (index n_segs-1). Linear ramp head=1 → tail=tail_alpha.
    t = np.arange(n_segs) / max(n_segs - 1, 1)  # 0..1, oldest..newest
    alphas = tail_alpha + (base_alpha - tail_alpha) * t
    colors = np.zeros((n_segs, 4))
    colors[:, :3] = 1.0
    colors[:, 3] = alphas
    return segs, colors


def _add_iso_meshes_to_axis(ax, meshes: list[dict]) -> None:
    for m in meshes:
        verts = m["verts"]; faces = m["faces"]
        c = m["color"]; a = m["alpha"]
        mesh = Poly3DCollection(verts[faces])
        mesh.set_facecolor((c[0], c[1], c[2], a))
        mesh.set_edgecolor((1, 1, 1, 0.04))
        mesh.set_linewidth(0.18)
        ax.add_collection3d(mesh)


def _render_one_frame_worker(args: dict) -> str:
    """Pickle-friendly worker: build a fresh figure for one frame, save PNG."""
    import matplotlib  # noqa: F401  (worker process needs Agg backend)
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    frame_idx = args["frame_idx"]
    plan_entry = args["plan_entry"]
    traj_data = args["traj_data"]
    pts = args["pts"]
    meshes = args["meshes"]
    xb = args["xb"]; yb = args["yb"]; zb = args["zb"]
    cond = args["cond"]
    cond_color = args["cond_color"]
    n_total_frames = args["n_total_frames"]
    rotate = args["rotate"]
    steps_g = args["steps_g"]
    i_pre_g = args["i_pre_g"]
    i_post_g = args["i_post_g"]
    out_png = args["out_png"]

    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor("#0d0d0d")
    fig.patch.set_facecolor("#0d0d0d")
    ax.set_xlim(*xb); ax.set_ylim(*yb); ax.set_zlim(*zb)
    ax.set_xlabel("PCA-1", color="#ddd")
    ax.set_ylabel("PCA-2", color="#ddd")
    ax.set_zlabel("PCA-3", color="#ddd")
    ax.tick_params(colors="#aaa", labelsize=7)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor("#181818")
        axis.pane.set_edgecolor("#333")

    if meshes:
        _add_iso_meshes_to_axis(ax, meshes)

    ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2],
               s=1.5, alpha=0.06, color="#dddddd", linewidths=0)

    kind = plan_entry["kind"]
    k = plan_entry["k"]
    interp = plan_entry["interp"]

    KICK_RED = "#ff0040"
    def _draw_kick(p_a, p_b):
        ax.plot([p_a[0], p_b[0]], [p_a[1], p_b[1]], [p_a[2], p_b[2]],
                color=KICK_RED, lw=12, alpha=0.22, solid_capstyle="round")
        ax.plot([p_a[0], p_b[0]], [p_a[1], p_b[1]], [p_a[2], p_b[2]],
                color=KICK_RED, lw=4.0, alpha=1.0, solid_capstyle="round")
        ax.scatter([p_a[0]], [p_a[1]], [p_a[2]], s=160, marker="X",
                   color=KICK_RED, edgecolors="white", linewidths=1.4)

    def _draw_trail(prefix_xyz):
        segs, colors = _fading_trail_data(prefix_xyz)
        if len(segs) > 0:
            ax.add_collection3d(Line3DCollection(segs, colors=colors, linewidths=2.0))

    HEAD_KW = dict(s=70, marker="o", color="white",
                   edgecolors="black", linewidths=0.8)

    for d in traj_data:
        xyz = d["traj_xyz"]
        ip = d["i_pre"]; iq = d["i_post"]
        if kind in ("step", "pre_pause"):
            _draw_trail(xyz[:k+1])
            hp = xyz[k]
            ax.scatter([hp[0]], [hp[1]], [hp[2]], **HEAD_KW)
            if iq is not None and k > iq:
                _draw_kick(xyz[ip], xyz[iq])
        elif kind == "kick" and iq is not None:
            a = xyz[ip]; b = xyz[iq]
            cur = a + interp * (b - a)
            _draw_trail(xyz[:ip+1])
            ax.scatter([cur[0]], [cur[1]], [cur[2]], **HEAD_KW)
            _draw_kick(a, cur)
        elif kind == "post_pause" and iq is not None:
            a = xyz[ip]; b = xyz[iq]
            _draw_trail(xyz[:iq+1])
            ax.scatter([b[0]], [b[1]], [b[2]], **HEAD_KW)
            _draw_kick(a, b)

    if rotate:
        azim = -60 + (frame_idx / max(n_total_frames, 1)) * 120
        ax.view_init(elev=22, azim=azim)
    else:
        ax.view_init(elev=22, azim=-30)

    if kind == "pre_pause":
        label = f"step {int(steps_g[k])}/{int(steps_g[-1])}  ← perturbation incoming"
    elif kind == "kick":
        label = (f"step {int(steps_g[i_pre_g])} → {int(steps_g[i_post_g])}  "
                 f"|  PERTURBATION KICK ({int(interp*100)}%)")
    elif kind == "post_pause":
        label = f"step {int(steps_g[i_post_g])}  |  post-kick"
    else:
        label = f"step {int(steps_g[k])}/{int(steps_g[-1])}"

    ax.set_title(
        f"{cond}  |  N={len(traj_data)} trajectories  |  PCA-3  |  {label}",
        fontsize=12, color=cond_color,
    )

    fig.savefig(out_png, dpi=args["dpi"], facecolor="#0d0d0d")
    plt.close(fig)
    return out_png


def _render_parallel(
    plan: list[dict], traj_data: list[dict], pts: np.ndarray, meshes: list[dict],
    xb: tuple, yb: tuple, zb: tuple, *,
    cond: str, cond_color: str,
    steps_g: np.ndarray, i_pre_g: int | None, i_post_g: int | None,
    rotate: bool, fps: int, out_path: Path, n_workers: int,
    dpi: int = 180, fmt: str = "mp4",
) -> None:
    n_total = len(plan)
    log.info("parallel render: %d frames across %d workers, dpi=%d, fmt=%s",
             n_total, n_workers, dpi, fmt)

    with tempfile.TemporaryDirectory(prefix="anim3d_") as tmpdir:
        tmp = Path(tmpdir)
        args_list = []
        for fi, entry in enumerate(plan):
            args_list.append({
                "frame_idx": fi,
                "plan_entry": entry,
                "traj_data": traj_data,
                "pts": pts,
                "meshes": meshes,
                "xb": xb, "yb": yb, "zb": zb,
                "cond": cond, "cond_color": cond_color,
                "n_total_frames": n_total,
                "rotate": rotate,
                "steps_g": steps_g,
                "i_pre_g": i_pre_g, "i_post_g": i_post_g,
                "out_png": str(tmp / f"frame_{fi:04d}.png"),
                "dpi": dpi,
            })

        completed = 0
        with ProcessPoolExecutor(max_workers=n_workers) as pool:
            futures = [pool.submit(_render_one_frame_worker, a) for a in args_list]
            for fut in as_completed(futures):
                fut.result()
                completed += 1
                if completed % 5 == 0 or completed == n_total:
                    log.info("frames rendered: %d/%d", completed, n_total)

        png_paths = [tmp / f"frame_{fi:04d}.png" for fi in range(n_total)]
        if fmt == "mp4":
            import imageio.v2 as iio
            with iio.get_writer(
                out_path, fps=fps, codec="libx264", quality=8,
                macro_block_size=1,
            ) as writer:
                for p in png_paths:
                    writer.append_data(iio.imread(p))
        elif fmt == "gif":
            images = [Image.open(p).convert("RGB") for p in png_paths]
            first, rest = images[0], images[1:]
            first.save(
                out_path, save_all=True, append_images=rest,
                duration=int(1000 / max(fps, 1)), loop=0, optimize=False,
            )
        else:
            raise ValueError(f"unknown fmt: {fmt}")


def render_animation_3d(
    exp_dir: Path, observable: str, override_step: int, is_dialog: bool,
    cond: str, family: str | None, ic: str | None, run: str | None,
    fps: int = 4, n_trajs: int = 6, traj_seed: int = 0, rotate: bool = True,
    show_field: bool = True, field_grid_n: int = 48, parallel: int = 1,
    frames_per_step: int = 2, dpi: int = 180, fmt: str = "mp4",
    no_kick: bool = False,
) -> None:
    vecs, meta = _load(exp_dir, observable, is_dialog)
    log.info("loaded %d points for %s", len(vecs), exp_dir.name)

    out_dir = exp_dir / "reports" / "perturbation"
    ensure_dir(out_dir)

    pca = PCA(n_components=3, random_state=42).fit(vecs)
    Z = pca.transform(vecs)
    log.info("PCA-3 explained variance: %.3f (per-axis: %s)",
             float(pca.explained_variance_ratio_.sum()),
             [f"{v:.3f}" for v in pca.explained_variance_ratio_])

    sub_idx = (meta["regime"] == cond).values
    if sub_idx.sum() < 30:
        raise ValueError(f"insufficient {cond} data")
    pts = Z[sub_idx]

    # Trajectory selection
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

    # High-contrast palette designed to pop against the plasma iso-surfaces.
    # First 8 hand-picked; for N>8 we sample additional cool-tinted colors
    # from the 'cool' colormap (cyan↔magenta) to keep contrast with plasma.
    base_palette = [
        "#00e5ff", "#b6ff00", "#ffffff", "#80b3ff",
        "#00ff9d", "#bafff8", "#5cffd6", "#cefcff",
    ]
    n_pick = min(n_trajs if (family is None or ic is None or run is None) else 1,
                 50)
    if n_pick <= len(base_palette):
        palette = base_palette
    else:
        cool = plt.get_cmap("cool")
        extra_n = n_pick - len(base_palette)
        palette = base_palette + [
            cool(0.05 + 0.85 * (i / max(extra_n - 1, 1))) for i in range(extra_n)
        ]
    cond_color = COND_COLORS.get(cond, "#cccccc")
    kick_enabled = (not no_kick) and (cond != "control") and (cond in COND_COLORS)

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

    steps = traj_data[0]["steps"]
    i_pre_g = traj_data[0]["i_pre"]
    i_post_g = traj_data[0]["i_post"]
    target = targets[0]

    HOLD_PRE = 4
    HOLD_POST = 3
    KICK_SUBFRAMES = 8

    plan: list[dict] = []
    for k in range(len(steps)):
        # Repeat each trajectory step N times so the camera rotates while the
        # point is held: gives more visible 3D parallax per step.
        for _ in range(max(frames_per_step, 1)):
            plan.append({"kind": "step", "k": k, "interp": 0.0})
        if kick_enabled and i_post_g is not None and k == i_pre_g:
            for _ in range(HOLD_PRE):
                plan.append({"kind": "pre_pause", "k": i_pre_g, "interp": 0.0})
            for s in range(1, KICK_SUBFRAMES + 1):
                plan.append({"kind": "kick", "k": i_pre_g, "interp": s / KICK_SUBFRAMES})
            for _ in range(HOLD_POST):
                plan.append({"kind": "post_pause", "k": i_post_g, "interp": 1.0})

    # Bounds with padding (used by both single + parallel paths)
    def _pad(lo, hi):
        p = 0.05 * (hi - lo + 1e-9)
        return lo - p, hi + p
    xb = _pad(float(Z[:, 0].min()), float(Z[:, 0].max()))
    yb = _pad(float(Z[:, 1].min()), float(Z[:, 1].max()))
    zb = _pad(float(Z[:, 2].min()), float(Z[:, 2].max()))

    # Pre-compute iso-surface meshes once (used by single + parallel paths)
    meshes = (_compute_iso_meshes(pts, xb, yb, zb, grid_n=field_grid_n)
              if show_field else [])

    # ---- Parallel path: render frames to PNGs in a process pool ----
    if parallel > 1:
        ext = fmt
        if len(traj_data) == 1:
            famfrag = target[0].replace(" ", "_")[:16]
            out = out_dir / f"animation3d_{cond}_{famfrag}_{target[1]}_{target[2]}.{ext}"
        else:
            out = out_dir / f"animation3d_{cond}_n{len(traj_data)}_seed{traj_seed}.{ext}"
        _render_parallel(
            plan, traj_data, pts, meshes, xb, yb, zb,
            cond=cond, cond_color=cond_color,
            steps_g=steps, i_pre_g=i_pre_g, i_post_g=i_post_g,
            rotate=rotate, fps=fps, out_path=out, n_workers=parallel,
            dpi=dpi, fmt=fmt,
        )
        log.info("wrote %s (%d frames at %d fps, parallel=%d, dpi=%d)",
                 out, len(plan), fps, parallel, dpi)
        return

    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor("#0d0d0d")
    fig.patch.set_facecolor("#0d0d0d")
    ax.set_xlim(*xb); ax.set_ylim(*yb); ax.set_zlim(*zb)

    # Volumetric density iso-surfaces (drawn once)
    if meshes:
        _add_iso_meshes_to_axis(ax, meshes)

    # Background cloud (this condition's points) — light scatter on top of field
    ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2],
               s=1.5, alpha=0.06, color="#dddddd", linewidths=0)
    ax.set_xlabel("PCA-1", color="#ddd")
    ax.set_ylabel("PCA-2", color="#ddd")
    ax.set_zlabel("PCA-3", color="#ddd")
    ax.tick_params(colors="#aaa", labelsize=7)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor("#181818")
        axis.pane.set_edgecolor("#333")

    title_obj = ax.set_title("", fontsize=12, color=cond_color)

    # Per-trajectory artists — heads white, fading-alpha trails, red kick.
    KICK_RED = "#ff0040"
    for d in traj_data:
        d["trail_lc"] = Line3DCollection([], colors=[], linewidths=2.0)
        ax.add_collection3d(d["trail_lc"])
        d["head"] = ax.scatter([], [], [], s=70, marker="o", color="white",
                               edgecolors="black", linewidths=0.8)
        d["pre_dot"] = ax.scatter([], [], [], s=160, marker="X",
                                  color=KICK_RED, edgecolors="white",
                                  linewidths=1.4)
        d["kick_glow"], = ax.plot([], [], [], color=KICK_RED, lw=12,
                                  alpha=0.22, solid_capstyle="round")
        d["kick_line"], = ax.plot([], [], [], color=KICK_RED, lw=4.0,
                                  alpha=1.0, solid_capstyle="round")

    def init():
        for d in traj_data:
            d["trail_lc"].set_segments([])
            d["trail_lc"].set_color([])
            d["head"]._offsets3d = (np.array([]), np.array([]), np.array([]))
            d["pre_dot"]._offsets3d = (np.array([]), np.array([]), np.array([]))
            d["kick_line"].set_data_3d([], [], [])
            d["kick_glow"].set_data_3d([], [], [])
        return tuple()

    def _set_fading_trail(d, prefix_xyz):
        segs, colors = _fading_trail_data(prefix_xyz)
        d["trail_lc"].set_segments(list(segs))
        d["trail_lc"].set_color(colors)

    def update(frame):
        spec = plan[frame]
        kind = spec["kind"]
        k = spec["k"]
        interp = spec["interp"]

        for d in traj_data:
            xyz = d["traj_xyz"]
            ip = d["i_pre"]; iq = d["i_post"]

            if kind in ("step", "pre_pause"):
                _set_fading_trail(d, xyz[:k+1])
                hp = xyz[k]
                d["head"]._offsets3d = (np.array([hp[0]]), np.array([hp[1]]), np.array([hp[2]]))
                if iq is not None and k > iq:
                    a = xyz[ip]; b = xyz[iq]
                    d["pre_dot"]._offsets3d = (np.array([a[0]]), np.array([a[1]]), np.array([a[2]]))
                    d["kick_line"].set_data_3d([a[0], b[0]], [a[1], b[1]], [a[2], b[2]])
                    d["kick_glow"].set_data_3d([a[0], b[0]], [a[1], b[1]], [a[2], b[2]])
                else:
                    d["pre_dot"]._offsets3d = (np.array([]), np.array([]), np.array([]))
                    d["kick_line"].set_data_3d([], [], [])
                    d["kick_glow"].set_data_3d([], [], [])
            elif kind == "kick" and iq is not None:
                a = xyz[ip]; b = xyz[iq]
                cur = a + interp * (b - a)
                _set_fading_trail(d, xyz[:ip+1])
                d["head"]._offsets3d = (np.array([cur[0]]), np.array([cur[1]]), np.array([cur[2]]))
                d["pre_dot"]._offsets3d = (np.array([a[0]]), np.array([a[1]]), np.array([a[2]]))
                d["kick_line"].set_data_3d([a[0], cur[0]], [a[1], cur[1]], [a[2], cur[2]])
                d["kick_glow"].set_data_3d([a[0], cur[0]], [a[1], cur[1]], [a[2], cur[2]])
            elif kind == "post_pause" and iq is not None:
                a = xyz[ip]; b = xyz[iq]
                _set_fading_trail(d, xyz[:iq+1])
                d["head"]._offsets3d = (np.array([b[0]]), np.array([b[1]]), np.array([b[2]]))
                d["pre_dot"]._offsets3d = (np.array([a[0]]), np.array([a[1]]), np.array([a[2]]))
                d["kick_line"].set_data_3d([a[0], b[0]], [a[1], b[1]], [a[2], b[2]])
                d["kick_glow"].set_data_3d([a[0], b[0]], [a[1], b[1]], [a[2], b[2]])

        # Camera rotation: ~120° sweep over the (now longer) plan
        if rotate:
            azim = -60 + (frame / max(len(plan), 1)) * 120
            ax.view_init(elev=22, azim=azim)

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
            f"{cond}  |  N={len(traj_data)} trajectories  |  PCA-3  |  {label}"
        )
        return tuple()

    n_frames = len(plan)
    ani = animation.FuncAnimation(
        fig, update, init_func=init, frames=n_frames,
        interval=1000 // fps, blit=False, repeat=True,
    )

    if len(traj_data) == 1:
        famfrag = target[0].replace(" ", "_")[:16]
        out = out_dir / f"animation3d_{cond}_{famfrag}_{target[1]}_{target[2]}.gif"
    else:
        out = out_dir / f"animation3d_{cond}_n{len(traj_data)}_seed{traj_seed}.gif"
    ani.save(out, writer=animation.PillowWriter(fps=fps), dpi=120)
    plt.close(fig)
    log.info("wrote %s (%d frames at %d fps)", out, n_frames, fps)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="perturb_trajectory_animation_3d")
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--observable", default="context_tail")
    parser.add_argument("--override-step", type=int, default=15)
    parser.add_argument("--is-dialog", action="store_true")
    parser.add_argument("--condition", default="adversarial",
                        help="condition / regime name (use 'recursive' or "
                             "'no_feedback' for non-perturbation pub experiments)")
    parser.add_argument("--no-kick", action="store_true",
                        help="skip the perturbation-kick animation frames")
    parser.add_argument("--family", default=None)
    parser.add_argument("--ic", default=None)
    parser.add_argument("--run", default=None)
    parser.add_argument("--fps", type=int, default=4)
    parser.add_argument("--n-trajs", type=int, default=6)
    parser.add_argument("--traj-seed", type=int, default=0)
    parser.add_argument("--no-rotate", action="store_true",
                        help="disable camera rotation across frames")
    parser.add_argument("--no-field", action="store_true",
                        help="skip rendering the volumetric density field")
    parser.add_argument("--field-grid", type=int, default=48,
                        help="grid resolution for density iso-surfaces")
    parser.add_argument("--parallel", type=int, default=1,
                        help="render frames in parallel using N processes")
    parser.add_argument("--frames-per-step", type=int, default=2,
                        help="frames held per trajectory step (camera rotates "
                             "during these); higher = more visible 3D parallax")
    parser.add_argument("--dpi", type=int, default=180,
                        help="render DPI per frame (parallel path only)")
    parser.add_argument("--format", choices=["mp4", "gif"], default="mp4",
                        help="output format (parallel path only)")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    setup_logging(args.log_level, None)

    exp_dir = Path(args.data_dir) / args.experiment
    if not exp_dir.exists():
        raise FileNotFoundError(exp_dir)

    render_animation_3d(
        exp_dir, args.observable, args.override_step, args.is_dialog,
        cond=args.condition, family=args.family, ic=args.ic, run=args.run,
        fps=args.fps, n_trajs=args.n_trajs, traj_seed=args.traj_seed,
        rotate=not args.no_rotate,
        show_field=not args.no_field, field_grid_n=args.field_grid,
        parallel=args.parallel, frames_per_step=args.frames_per_step,
        dpi=args.dpi, fmt=args.format, no_kick=args.no_kick,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
