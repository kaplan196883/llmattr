"""
Perturbation-response analysis:

  - Compute a shared PCA-10 across ALL condition embeddings (so the 4 conditions
    live in the same geometric space for fair comparison).
  - Compute joint K-means (k=12) across all conditions for switching analysis.
  - For each (family, ic, run), compute the "original" basin centroid from
    steps 10–14 (pre-perturbation window), separately for the control run.
  - For each perturbed run (neutral / lorem / adversarial), compute:
      * distance_from_origin[t] = ||pca10[t] - control_centroid|| for t >= override_step
      * switching indicator = cluster[29] != control_cluster[29]
  - Plot:
      * Relaxation curves: mean distance-from-origin vs step, by condition
      * Switching rates: per condition, fraction of trajectories ending in a
        different cluster than their paired control
      * 2D projection of trajectories (PCA-2) grouped by condition

Writes to data/{experiment_id}/reports/perturbation/.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

from src.analysis.bootstrap import wilson_ci
from src.config import Config
from src.utils.io import ensure_dir, read_jsonl
from src.utils.logging import get_logger

log = get_logger(__name__)


OBSERVABLE = "context_tail"  # the information-rich canonical observable
N_CLUSTERS = 12


def _load_embeddings(cfg: Config) -> tuple[np.ndarray, pd.DataFrame]:
    emb_path = cfg.embeddings_dir / OBSERVABLE / "embeddings.npy"
    meta_path = cfg.embeddings_dir / OBSERVABLE / "metadata.parquet"
    if not emb_path.exists():
        raise FileNotFoundError(f"missing embeddings at {emb_path}; run embed first")
    X = np.load(emb_path)
    meta = pd.read_parquet(meta_path)
    assert len(X) == len(meta), f"shape mismatch {X.shape} vs {len(meta)}"
    return X, meta


def _compute_pca_and_clusters(X: np.ndarray, meta: pd.DataFrame, out_dir: Path) -> pd.DataFrame:
    """Joint PCA-10 + K-means across ALL conditions, so they share the space."""
    pca = PCA(n_components=10, random_state=42)
    Xp = pca.fit_transform(X)
    log.info("joint PCA-10 explained variance: %.3f", float(pca.explained_variance_ratio_.sum()))

    km = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
    clusters = km.fit_predict(Xp)

    out = meta.copy()
    for i in range(10):
        out[f"pc{i+1}"] = Xp[:, i]
    out["cluster"] = clusters
    out.to_csv(out_dir / "joint_pca10_clusters.csv", index=False)
    return out


def _match_perturbation_step(cfg: Config) -> int:
    p = cfg.raw_dict.get("perturbation") or {}
    return int(p.get("override_step", 15))


def _build_relaxation_table(df: pd.DataFrame, override_step: int, is_dialog: bool = True,
                            agent_role: str = "agent") -> pd.DataFrame:
    """
    For each (family, ic, run), find the control run's centroid over steps
    [override_step-5, override_step-1] (pre-perturbation window), and the
    control's cluster at the last step. Then for every perturbed run with
    matching keys, compute:
      * distance-from-control-centroid at each step
      * cluster at last step (for switching)
    """
    pc_cols = [f"pc{i}" for i in range(1, 11)]
    if is_dialog and "role" in df.columns:
        # Restrict to the responder role (agent / expert / role_b)
        df = df[df["role"] == agent_role].copy()
    else:
        df = df.copy()

    pre_lo = max(0, override_step - 5)
    pre_hi = override_step  # exclusive upper bound

    out_rows: list[dict] = []

    group_keys = ["prompt_family", "initial_condition_id", "run_id"]
    for (fam, ic, rid), sub in df.groupby(group_keys):
        # Need control in this tuple
        ctrl = sub[sub["regime"] == "control"].sort_values("step")
        if ctrl.empty:
            continue
        ctrl_pre = ctrl[(ctrl["step"] >= pre_lo) & (ctrl["step"] < pre_hi)]
        if len(ctrl_pre) == 0:
            continue
        centroid = ctrl_pre[pc_cols].mean(axis=0).to_numpy()
        final_ctrl = ctrl.iloc[-1]
        ctrl_last_cluster = int(final_ctrl["cluster"])

        for condition in sub["regime"].unique():
            c_sub = sub[sub["regime"] == condition].sort_values("step")
            if c_sub.empty:
                continue
            for _, row in c_sub.iterrows():
                vec = row[pc_cols].to_numpy()
                dist = float(np.linalg.norm(vec - centroid))
                out_rows.append({
                    "prompt_family": fam,
                    "initial_condition_id": ic,
                    "run_id": rid,
                    "condition": condition,
                    "step": int(row["step"]),
                    "distance_from_origin": dist,
                    "cluster": int(row["cluster"]),
                    "ctrl_last_cluster": ctrl_last_cluster,
                    "is_post_perturb": int(row["step"]) >= override_step,
                })
    return pd.DataFrame(out_rows)


def _auto_condition_order_and_colors(conds: list[str]) -> tuple[list[str], dict[str, str]]:
    """Generate a stable ordering + color map for any condition set.
    'control' first, then named ('neutral', 'lorem', 'adversarial'), then
    dose-variants (e.g. 'neutral_dose20') in ascending numeric order."""
    fixed_order = ["control", "neutral", "lorem", "adversarial"]
    fixed_colors = {"control": "#4a90e2", "neutral": "#8b5cf6",
                    "lorem": "#ff9800", "adversarial": "#d62728"}
    # Split conds into (in fixed_order) vs (dose variants) vs other
    present_fixed = [c for c in fixed_order if c in conds]
    dose_conds = sorted(
        [c for c in conds if "_dose" in c],
        key=lambda c: int(c.split("_dose")[-1]) if c.split("_dose")[-1].isdigit() else 0,
    )
    other = [c for c in conds if c not in present_fixed and c not in dose_conds]
    order = present_fixed + dose_conds + other

    import matplotlib.cm as cm
    n_doses = len(dose_conds)
    # Viridis/plasma ramp for dose levels
    dose_colors = {c: cm.plasma(0.2 + 0.7 * i / max(1, n_doses - 1))
                   for i, c in enumerate(dose_conds)}
    other_colors = {c: "#777" for c in other}
    colors = {**fixed_colors, **dose_colors, **other_colors}
    return order, colors


def _plot_relaxation_curves(rel: pd.DataFrame, override_step: int, out_path: Path) -> None:
    conds_present = list(rel["condition"].unique())
    conditions, colors = _auto_condition_order_and_colors(conds_present)
    fig, ax = plt.subplots(figsize=(10, 6))
    for cond in conditions:
        sub = rel[rel["condition"] == cond]
        if sub.empty:
            continue
        agg = sub.groupby("step")["distance_from_origin"].agg(["mean", "std", "count"]).reset_index()
        ax.errorbar(
            agg["step"], agg["mean"],
            yerr=agg["std"] / np.sqrt(agg["count"].clip(lower=1)),
            label=cond, color=colors[cond], marker="o", lw=1.8, capsize=3,
        )
    ax.axvline(override_step, color="#555", linestyle="--", lw=1.2, alpha=0.8,
               label=f"perturbation @ step {override_step}")
    ax.set_xlabel("step")
    ax.set_ylabel("mean distance from control's pre-perturb centroid (PCA-10)")
    ax.set_title("Perturbation relaxation: does the trajectory return to its basin?")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=10)
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def _plot_switching_rates(rel: pd.DataFrame, override_step: int, out_path: Path) -> pd.DataFrame:
    """Fraction of trajectories that end in a different cluster than their control."""
    last_steps = rel[rel["step"] == rel.groupby(
        ["prompt_family", "initial_condition_id", "run_id", "condition"]
    )["step"].transform("max")]
    last_steps = last_steps.copy()
    last_steps["switched"] = (last_steps["cluster"] != last_steps["ctrl_last_cluster"]).astype(int)

    summary = (
        last_steps.groupby("condition")["switched"]
        .agg(["mean", "sum", "count"])
        .rename(columns={"mean": "switch_rate", "sum": "n_switched", "count": "n_total"})
        .reset_index()
    )
    order, color_map = _auto_condition_order_and_colors(summary["condition"].tolist())
    summary = summary.set_index("condition").reindex(order).reset_index()
    summary = summary.dropna(subset=["switch_rate"])  # drop rows that didn't appear

    # Wilson 95% CI per condition (ARTICLE.md §4.7).
    ci_los, ci_his = [], []
    for _, row in summary.iterrows():
        ci = wilson_ci(int(row["n_switched"]), int(row["n_total"]), confidence=0.95)
        ci_los.append(ci.lo)
        ci_his.append(ci.hi)
    summary["switch_rate_ci_lo"] = ci_los
    summary["switch_rate_ci_hi"] = ci_his

    fig, ax = plt.subplots(figsize=(max(8, 1.5 * len(summary)), 5.5))
    bar_colors = [color_map.get(c, "#777") for c in summary["condition"]]
    bars = ax.bar(summary["condition"], summary["switch_rate"], color=bar_colors, alpha=0.85)
    # Wilson CI error bars: asymmetric, so pass yerr as a 2xN array.
    yerr_lo = (summary["switch_rate"] - summary["switch_rate_ci_lo"]).to_numpy()
    yerr_hi = (summary["switch_rate_ci_hi"] - summary["switch_rate"]).to_numpy()
    ax.errorbar(
        summary["condition"], summary["switch_rate"],
        yerr=np.stack([yerr_lo, yerr_hi]),
        fmt="none", ecolor="#222", capsize=4, lw=1.2,
    )
    for b, (sw, total, lo, hi) in zip(
        bars,
        zip(summary["n_switched"], summary["n_total"],
            summary["switch_rate_ci_lo"], summary["switch_rate_ci_hi"]),
    ):
        pct = (sw / max(1, total)) * 100
        ax.annotate(
            f"{pct:.0f}%\n({int(sw)}/{int(total)})\n[{lo*100:.0f}–{hi*100:.0f}]",
            xy=(b.get_x() + b.get_width() / 2, b.get_height()),
            xytext=(0, 4), textcoords="offset points",
            ha="center", fontsize=9,
        )
    ax.set_ylabel("fraction of trajectories switching basin")
    ax.set_ylim(0, max(0.6, float(summary["switch_rate_ci_hi"].max()) * 1.15))
    ax.set_title(f"Basin-switching rates by perturbation condition (Wilson 95% CI)\n"
                 f"(switch = cluster at step {int(rel['step'].max())} ≠ control's cluster)")
    ax.grid(alpha=0.3, axis="y")
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return summary


def _plot_trajectory_map(df: pd.DataFrame, override_step: int, out_path: Path, is_dialog: bool = True,
                          agent_role: str = "agent") -> None:
    """PCA-2 projection of all trajectories. One panel per condition in a near-square grid."""
    if is_dialog and "role" in df.columns:
        df = df[df["role"] == agent_role].copy()
    else:
        df = df.copy()
    conds_present = list(df["regime"].unique())
    conditions, cond_colors = _auto_condition_order_and_colors(conds_present)
    n = len(conditions)
    ncols = 2 if n <= 4 else int(np.ceil(np.sqrt(n)))
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(7 * ncols, 6 * nrows),
                             sharex=True, sharey=True, squeeze=False)
    for ax, cond in zip(axes.flat, conditions):
        sub = df[df["regime"] == cond]
        if sub.empty:
            ax.set_title(f"{cond} (no data)")
            continue
        pre = sub[sub["step"] < override_step]
        post = sub[sub["step"] >= override_step]
        # trajectory lines
        for _, traj in sub.groupby(["prompt_family", "initial_condition_id", "run_id"]):
            traj = traj.sort_values("step")
            ax.plot(traj["pc1"], traj["pc2"], color="#555", alpha=0.18, lw=0.6)
        # pre-perturbation: gray
        ax.scatter(pre["pc1"], pre["pc2"], c="#999", s=10, alpha=0.35,
                   label=f"steps 0..{override_step-1} (pre)")
        # post-perturbation: colored by condition
        ax.scatter(post["pc1"], post["pc2"], c=cond_colors[cond], s=14, alpha=0.6,
                   edgecolors="white", linewidths=0.3,
                   label=f"steps {override_step}..{int(sub['step'].max())} (post-perturb)")
        # injection points specifically — plot larger black markers
        inj = sub[sub["step"] == override_step]
        ax.scatter(inj["pc1"], inj["pc2"], c="black", s=40, marker="X",
                   edgecolors=cond_colors[cond], linewidths=1.5,
                   label=f"step {override_step} (injection)", zorder=5)
        ax.set_title(f"{cond}  (N={int(sub.groupby(['prompt_family','initial_condition_id','run_id']).ngroups)} trajectories)",
                     fontsize=12)
        ax.set_xlabel("PC1")
        ax.set_ylabel("PC2")
        ax.grid(alpha=0.2)
        ax.legend(fontsize=8, loc="lower right")
    # Hide unused axes
    for ax in axes.flat[len(conditions):]:
        ax.axis("off")
    fig.suptitle("Perturbation response: trajectory projections (joint PCA-2, agent role)\n"
                 f"injection at step {override_step}",
                 fontsize=14, y=1.00)
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def cmd_analyze_perturbation(cfg: Config, is_dialog: bool = True) -> None:
    override_step = _match_perturbation_step(cfg)
    # Pull responder role name from config (defaults to "agent" for D1)
    agent_role = "agent"
    dlg = cfg.raw_dict.get("dialog") or {}
    role_b = dlg.get("role_b") or {}
    if role_b.get("name"):
        agent_role = role_b["name"]
    log.info("perturbation analyze: override_step=%d is_dialog=%s agent_role=%s",
             override_step, is_dialog, agent_role)

    X, meta = _load_embeddings(cfg)
    out_dir = cfg.reports_dir / "perturbation"
    ensure_dir(out_dir)

    df = _compute_pca_and_clusters(X, meta, out_dir)
    rel = _build_relaxation_table(df, override_step, is_dialog=is_dialog,
                                  agent_role=agent_role)
    rel.to_csv(out_dir / "relaxation_table.csv", index=False)
    log.info("wrote relaxation_table.csv (%d rows)", len(rel))

    _plot_relaxation_curves(rel, override_step, out_dir / "relaxation_curves.png")
    log.info("wrote relaxation_curves.png")

    summary = _plot_switching_rates(rel, override_step, out_dir / "switching_rates.png")
    summary.to_csv(out_dir / "switching_summary.csv", index=False)
    log.info("wrote switching_rates.png and switching_summary.csv")
    log.info("switching summary:\n%s", summary.to_string(index=False))

    _plot_trajectory_map(df, override_step, out_dir / "trajectory_map.png",
                         is_dialog=is_dialog, agent_role=agent_role)
    log.info("wrote trajectory_map.png")


__all__ = ["cmd_analyze_perturbation"]
