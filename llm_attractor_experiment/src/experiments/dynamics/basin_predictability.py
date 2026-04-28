"""
Basin-predictability analysis. See ARTICLE.md §4.5.3 / §5.3 for the spec.

Question: given a trajectory's embedding at early step k, how accurately can
we predict which K-means cluster it will occupy at late steps?

If early-step accuracy is near random (1/n_clusters), the attractor landscape
is stochastic-at-runtime — the seed doesn't commit to a basin immediately.
If early-step accuracy is near 1.0, the basin is determined by the seed and
the recursion is doing basin-maintenance rather than basin-selection.

We compare recursive vs no_feedback as a control. For no_feedback the late-
step cluster is essentially the same as the early-step cluster (no dynamics),
so any classifier will trivially succeed. For recursive, gains in accuracy
over step k quantify how quickly fate is locked in.

Runs on already-computed PCA-10 embeddings and K-means cluster labels from the
analyze phase of an experiment. No API calls.

Usage:
    python -m src.experiments.dynamics.basin_predictability \\
        --config configs/operators/O1_pub.yaml \\
        --observables output,rolling_k3,context_tail
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold

from src.config import load_config
from src.utils.io import ensure_dir
from src.utils.logging import get_logger, setup_logging

log = get_logger(__name__)


EARLY_STEPS = [0, 1, 2, 3, 5, 10, 20, 30]
# FINAL_WINDOW is computed adaptively in analyze_observable from
# cfg.basin.target_step_fraction (default 0.7, see ARTICLE.md §4.5.3).
# The "post-t*" late window is [round(t* · T), T-1] inclusive.
DEFAULT_LATE_WINDOW_FRACTION = 0.7


def _load_pca_and_clusters(cfg, observable: str, role: str | None = None) -> pd.DataFrame:
    pca_path = cfg.metrics_dir / f"pca_10_{observable}.csv"
    clust_path = cfg.metrics_dir / f"clusters_{observable}_pca10.csv"
    pca = pd.read_csv(pca_path)
    clust = pd.read_csv(clust_path)
    key_cols = ["regime", "prompt_family", "initial_condition_id", "run_id", "step"]
    if "role" in pca.columns and "role" in clust.columns:
        if role is None:
            role = "agent" if "agent" in pca["role"].unique() else sorted(pca["role"].unique())[0]
        pca = pca[pca["role"] == role]
        clust = clust[clust["role"] == role]
        log.info("filtered to role=%s (%d pca rows, %d cluster rows)", role, len(pca), len(clust))
    pc_cols = [f"pc{i}" for i in range(1, 11)]
    merged = pca[key_cols + pc_cols].merge(clust[key_cols + ["cluster"]], on=key_cols)
    return merged


def _final_cluster_per_trajectory(df: pd.DataFrame, step_lo: int, step_hi: int) -> pd.Series:
    """Majority-vote cluster across steps [step_lo, step_hi] for each trajectory."""
    late = df[(df["step"] >= step_lo) & (df["step"] <= step_hi)]
    maj = (
        late.groupby(["regime", "prompt_family", "initial_condition_id", "run_id"])[
            "cluster"
        ]
        .agg(lambda s: s.value_counts().idxmax())
    )
    maj.name = "final_cluster"
    return maj


def _predict_from_step(
    df: pd.DataFrame, final: pd.Series, step: int, regime: str
) -> dict:
    """
    5-fold CV logistic regression: predict final_cluster from PCA-10 embedding
    at step `step`, restricted to given regime. Returns top-1 accuracy and
    top-3 accuracy averaged across folds.
    """
    early = df[(df["regime"] == regime) & (df["step"] == step)].copy()
    if len(early) == 0:
        return {"regime": regime, "step": step, "n": 0, "top1": np.nan, "top3": np.nan}
    early = early.merge(
        final.reset_index(), on=["regime", "prompt_family", "initial_condition_id", "run_id"]
    )
    if len(early) == 0:
        return {"regime": regime, "step": step, "n": 0, "top1": np.nan, "top3": np.nan}

    X = early[[f"pc{i}" for i in range(1, 11)]].to_numpy()
    y = early["final_cluster"].to_numpy()
    unique, counts = np.unique(y, return_counts=True)
    n_classes = len(unique)
    if n_classes < 2:
        return {
            "regime": regime, "step": step, "n": len(early),
            "top1": 1.0, "top3": 1.0, "n_classes": n_classes,
        }

    # Adaptive n_splits: stratified K-fold needs every class to have at
    # least n_splits members. Small pilots (n=75 split across k=12 clusters)
    # routinely have classes with <5 members; reducing n_splits to the
    # smallest class size is more robust than crashing. If even 2-fold is
    # impossible, return NaN.
    min_class = int(counts.min())
    if min_class < 2:
        return {
            "regime": regime, "step": step, "n": len(early),
            "top1": float("nan"), "top3": float("nan"), "n_classes": n_classes,
            "min_class_size": min_class, "n_splits_used": 0,
        }
    n_splits = min(5, min_class)
    kf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    top1_scores: list[float] = []
    top3_scores: list[float] = []
    for train_idx, test_idx in kf.split(X, y):
        try:
            clf = LogisticRegression(max_iter=2000, n_jobs=-1, C=1.0)
            clf.fit(X[train_idx], y[train_idx])
        except Exception as e:
            log.warning("LR failed (regime=%s step=%d): %s", regime, step, e)
            continue
        probs = clf.predict_proba(X[test_idx])
        labels_sorted_desc = np.argsort(-probs, axis=1)
        class_labels = clf.classes_
        preds_top1 = class_labels[labels_sorted_desc[:, 0]]
        preds_top3 = class_labels[labels_sorted_desc[:, :3]]
        y_test = y[test_idx]
        top1 = float((preds_top1 == y_test).mean())
        top3 = float((preds_top3 == y_test[:, None]).any(axis=1).mean())
        top1_scores.append(top1)
        top3_scores.append(top3)
    if not top1_scores:
        return {"regime": regime, "step": step, "n": len(early), "top1": np.nan, "top3": np.nan}
    return {
        "regime": regime,
        "step": step,
        "n": len(early),
        "n_classes": n_classes,
        "top1": float(np.mean(top1_scores)),
        "top1_std": float(np.std(top1_scores)),
        "top3": float(np.mean(top3_scores)),
        "top3_std": float(np.std(top3_scores)),
    }


def analyze_observable(
    cfg,
    observable: str,
    out_dir: Path,
    role: str | None = None,
    late_window_fraction: float | None = None,
) -> pd.DataFrame:
    log.info("=== %s ===", observable)
    df = _load_pca_and_clusters(cfg, observable, role=role)
    log.info("loaded %d points across %d regimes", len(df), df["regime"].nunique())

    # ARTICLE.md §4.5.3: the late window for the "final cluster" majority
    # vote starts at t* = round(target_step_fraction · T). When unset on the
    # CLI, we read cfg.basin.target_step_fraction (default 0.7).
    if late_window_fraction is None:
        cfg_basin = getattr(cfg, "basin", None)
        late_window_fraction = (
            float(getattr(cfg_basin, "target_step_fraction", DEFAULT_LATE_WINDOW_FRACTION))
            if cfg_basin is not None
            else DEFAULT_LATE_WINDOW_FRACTION
        )
    max_step = int(df["step"].max())
    T = max_step + 1  # zero-indexed → number of steps
    final_lo = int(round(late_window_fraction * T))
    final_lo = max(0, min(final_lo, max_step))
    final_hi = max_step
    log.info(
        "final window: steps %d..%d (max_step=%d, late_fraction=%.2f)",
        final_lo, final_hi, max_step, late_window_fraction,
    )
    final = _final_cluster_per_trajectory(df, final_lo, final_hi)
    log.info("computed final cluster for %d trajectories", len(final))

    rows = []
    # Latest predictor step is the step right before the late window opens.
    last_predictor_step = max(0, final_lo - 1)
    steps_to_probe = [s for s in EARLY_STEPS if s <= last_predictor_step] + [last_predictor_step]
    steps_to_probe = sorted(set(steps_to_probe))
    for regime in ["recursive", "no_feedback"]:
        if regime not in df["regime"].unique():
            continue
        for step in steps_to_probe:
            result = _predict_from_step(df, final, step, regime)
            result["observable"] = observable
            rows.append(result)
            if result.get("top1") is not None and not np.isnan(result.get("top1", np.nan)):
                log.info(
                    "%s step=%d regime=%s: top1=%.3f (±%.3f), top3=%.3f, n=%d, classes=%d",
                    observable, step, regime,
                    result["top1"], result.get("top1_std", 0),
                    result["top3"], result["n"], result.get("n_classes", 0),
                )
    return pd.DataFrame(rows)


def plot_accuracy_curves(df: pd.DataFrame, out_dir: Path, exp_id: str) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    observables = sorted(df["observable"].unique())
    fig, axes = plt.subplots(1, len(observables), figsize=(5 * len(observables), 5), squeeze=False)
    for i, obs in enumerate(observables):
        ax = axes[0, i]
        sub = df[df["observable"] == obs]
        for regime, color in [("recursive", "#ff7043"), ("no_feedback", "#1f77b4")]:
            rsub = sub[sub["regime"] == regime].sort_values("step")
            if len(rsub) == 0:
                continue
            yerr_top1 = rsub["top1_std"].fillna(0) if "top1_std" in rsub.columns else 0
            yerr_top3 = rsub["top3_std"].fillna(0) if "top3_std" in rsub.columns else 0
            ax.errorbar(
                rsub["step"], rsub["top1"],
                yerr=yerr_top1,
                label=f"{regime} top-1", color=color, marker="o", lw=1.6, capsize=3,
            )
            ax.errorbar(
                rsub["step"], rsub["top3"],
                yerr=yerr_top3,
                label=f"{regime} top-3", color=color, marker="s", lw=1.0, alpha=0.6,
                linestyle="--", capsize=3,
            )
        n_classes = sub["n_classes"].dropna().iloc[0] if "n_classes" in sub and sub["n_classes"].notna().any() else 8
        ax.axhline(
            1.0 / n_classes, color="#999", linestyle=":", lw=1,
            label=f"chance (1/{int(n_classes)})",
        )
        ax.set_title(f"{obs}\nfinal-cluster prediction from step k")
        ax.set_xlabel("step k (predictor)")
        ax.set_ylabel("accuracy")
        ax.set_ylim(0, 1.05)
        ax.grid(alpha=0.25)
        ax.legend(fontsize=8, loc="lower right")
    fig.suptitle(
        f"{exp_id} — Basin predictability: how early is the final cluster fixed?",
        fontsize=13, y=1.02,
    )
    path = out_dir / f"basin_predictability_{exp_id}.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", path)
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="basin_predictability")
    parser.add_argument("--config", required=True)
    parser.add_argument(
        "--observables", default="output,rolling_k3,context_tail",
        help="Comma-separated list of observables to analyze.",
    )
    parser.add_argument(
        "--role", default=None,
        help="For dialog experiments: role to restrict to (e.g., 'agent'). Auto-detected.",
    )
    parser.add_argument(
        "--late-window-fraction", type=float, default=None,
        help=(
            "Override cfg.basin.target_step_fraction for the 'final cluster' "
            "late-window definition (per ARTICLE.md §4.5.3). Default: read "
            "from cfg, falling back to 0.7."
        ),
    )
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    setup_logging(args.log_level, None)

    cfg = load_config(args.config)
    out_dir = cfg.reports_dir / "basin_predictability"
    ensure_dir(out_dir)

    all_rows = []
    for obs in args.observables.split(","):
        obs = obs.strip()
        if not obs:
            continue
        df = analyze_observable(
            cfg, obs, out_dir,
            role=args.role,
            late_window_fraction=args.late_window_fraction,
        )
        all_rows.append(df)

    if all_rows:
        full = pd.concat(all_rows, ignore_index=True)
        csv_path = out_dir / "basin_predictability.csv"
        full.to_csv(csv_path, index=False)
        log.info("wrote %s", csv_path)

        # summary JSON
        summary = {
            "experiment_id": cfg.experiment_id,
            "observables": args.observables.split(","),
            "rows": full.to_dict(orient="records"),
        }
        with (out_dir / "basin_predictability_summary.json").open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, default=str)

        plot_accuracy_curves(full, out_dir, cfg.experiment_id)

    return 0


if __name__ == "__main__":
    sys.exit(main())
