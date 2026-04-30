"""
Group-aware basin-predictability re-analysis.

Addresses review weakness #7: "Basin-predictability CV may split runs
from the same IC/family across train/test." The existing
basin_predictability code uses sklearn's StratifiedKFold, which
randomly assigns trajectories from the same prompt_family to both
train and test folds. This inflates accuracy because the late-window
basin a trajectory ends up in is partly determined by its prompt
family — and the classifier can exploit that leakage.

GroupKFold(n_splits=k, groups=family) holds out one family at a time.
The accuracy delta (stratified – grouped) quantifies how much of the
reported basin-predictability number was from-family-leakage rather
than genuine basin signal.

Output: a CSV per regime + a summary plot showing acc(stratified) vs
acc(grouped) at the canonical predictor step k=10 (after the
late-window starts).

Note: this script *only re-runs CV* on already-cached PCA-10
embeddings and existing K-means cluster assignments — no new data,
no API calls.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold, StratifiedKFold

REPO = Path(__file__).resolve().parent.parent

DEFAULT_EXPERIMENTS = [
    "exp_pub_O1_continue",
    "exp_pub_O2_paraphrase_replace",
    "exp_pub_O3_summarize_negate",
    "exp_pub_D1_dialog_curious_helpful_v2",
]
PROBE_STEPS = [5, 10, 20]


def _load_predictor_data(exp_dir: Path, observable: str) -> pd.DataFrame | None:
    """Build PCA-10 + cluster table by merging the cached
    pca_10_<obs>.csv and clusters_<obs>_pca10.csv files (per-experiment
    pipeline outputs, see src/experiments/dynamics/basin_predictability.py)."""
    pca_path = exp_dir / "metrics" / f"pca_10_{observable}.csv"
    clust_path = exp_dir / "metrics" / f"clusters_{observable}_pca10.csv"
    if not pca_path.exists() or not clust_path.exists():
        return None
    pca = pd.read_csv(pca_path)
    clust = pd.read_csv(clust_path)
    key_cols = ["regime", "prompt_family", "initial_condition_id", "run_id", "step"]
    # Restrict to the canonical recursive regime (drop baselines).
    pca = pca[pca["regime"] == "recursive"]
    clust = clust[clust["regime"] == "recursive"]
    # Dialog: pick agent role if present.
    if "role" in pca.columns and "role" in clust.columns:
        roles = sorted(pca["role"].dropna().unique())
        target = "agent" if "agent" in roles else (roles[-1] if roles else None)
        if target:
            pca = pca[pca["role"] == target]
            clust = clust[clust["role"] == target]
    pc_cols = [f"pc{i}" for i in range(1, 11)]
    merged = pca[key_cols + pc_cols].merge(clust[key_cols + ["cluster"]], on=key_cols)
    return merged


def _final_cluster(df: pd.DataFrame, late_lo: float = 0.7) -> pd.Series:
    """Final K-means cluster per (regime, family, ic, run) trajectory,
    averaged over the late window via mode."""
    n_steps = int(df["step"].max()) + 1
    cutoff = int(n_steps * late_lo)
    late = df[df["step"] >= cutoff]
    return (
        late.groupby(["regime", "prompt_family", "initial_condition_id", "run_id"])
        ["cluster"].agg(lambda s: s.mode().iat[0])
        .rename("final_cluster")
    )


def _classify_at_step(
    df: pd.DataFrame, final: pd.Series, regime: str, step: int,
    cv_kind: str,
) -> dict:
    """Run logistic regression at predictor step, with given CV kind."""
    early = df[(df["regime"] == regime) & (df["step"] == step)].copy()
    if len(early) == 0:
        return {"regime": regime, "step": step, "cv": cv_kind, "n": 0, "top1": np.nan}
    early = early.merge(
        final.reset_index(),
        on=["regime", "prompt_family", "initial_condition_id", "run_id"],
    )
    if len(early) == 0:
        return {"regime": regime, "step": step, "cv": cv_kind, "n": 0, "top1": np.nan}

    pc_cols = [c for c in early.columns if c.startswith("pc") and c[2:].isdigit()]
    pc_cols = sorted(pc_cols, key=lambda c: int(c[2:]))[:10]
    X = early[pc_cols].to_numpy()
    y = early["final_cluster"].to_numpy()
    groups = early["prompt_family"].to_numpy()

    # Drop singleton classes for stratified k-fold.
    unique, counts = np.unique(y, return_counts=True)
    keep = unique[counts >= 2]
    mask = np.isin(y, keep)
    X, y, groups = X[mask], y[mask], groups[mask]
    if len(np.unique(y)) < 2:
        return {"regime": regime, "step": step, "cv": cv_kind, "n": len(early), "top1": 1.0}

    if cv_kind == "stratified":
        n_splits = min(5, int(counts[counts >= 2].min()))
        splitter = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        split_iter = splitter.split(X, y)
    elif cv_kind == "group":
        n_groups = len(np.unique(groups))
        n_splits = min(5, n_groups)
        splitter = GroupKFold(n_splits=n_splits)
        split_iter = splitter.split(X, y, groups)
    else:
        raise ValueError(cv_kind)

    accs = []
    for train_idx, test_idx in split_iter:
        try:
            clf = LogisticRegression(max_iter=2000, n_jobs=-1, C=1.0)
            clf.fit(X[train_idx], y[train_idx])
            preds = clf.predict(X[test_idx])
            accs.append(float((preds == y[test_idx]).mean()))
        except Exception:
            continue
    if not accs:
        return {"regime": regime, "step": step, "cv": cv_kind, "n": len(early), "top1": np.nan}
    return {
        "regime": regime, "step": step, "cv": cv_kind,
        "n": int(mask.sum()), "n_splits": n_splits,
        "top1": float(np.mean(accs)),
        "top1_std": float(np.std(accs)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiments", nargs="+", default=DEFAULT_EXPERIMENTS)
    ap.add_argument("--observable", default="context_tail")
    ap.add_argument("--probe-steps", nargs="+", type=int, default=PROBE_STEPS)
    args = ap.parse_args()

    rows = []
    for exp in args.experiments:
        exp_dir = REPO / "data" / exp
        df = _load_predictor_data(exp_dir, args.observable)
        if df is None:
            print(f"skip {exp}: no cached PCA10+clusters file")
            continue
        if "regime" not in df.columns:
            df["regime"] = "recursive"
        regime = df["regime"].mode().iat[0]
        print(f"\n=== {exp} (regime={regime}) ===")
        final = _final_cluster(df)
        for step in args.probe_steps:
            for cv in ("stratified", "group"):
                rec = _classify_at_step(df, final, regime, step, cv)
                rec["experiment"] = exp
                rows.append(rec)
                print(f"  step={step} cv={cv:10s} top1={rec.get('top1', np.nan):.3f} "
                      f"n={rec.get('n', 0)} splits={rec.get('n_splits', 'NA')}")

    out = pd.DataFrame(rows)
    out_path = REPO / "data" / "aggregated" / "group_aware_basin_pred.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)
    print(f"\nwrote {out_path}")

    # Plot: paired bars per regime per step
    if not out.empty:
        pivot = out.pivot_table(
            index=["experiment", "step"], columns="cv", values="top1",
        ).reset_index()
        if "stratified" in pivot.columns and "group" in pivot.columns:
            pivot["delta"] = pivot["stratified"] - pivot["group"]
            print("\nLeakage estimate (stratified – grouped) by experiment × step:")
            print(pivot.to_string(index=False))

            fig, ax = plt.subplots(figsize=(11, 5), facecolor="white")
            x = np.arange(len(pivot))
            ax.bar(x - 0.2, pivot["stratified"], width=0.4, color="#d62728",
                   label="StratifiedKFold (current)", edgecolor="black", linewidth=0.4)
            ax.bar(x + 0.2, pivot["group"], width=0.4, color="#2ca02c",
                   label="GroupKFold by family (leakage-free)", edgecolor="black", linewidth=0.4)
            ax.set_xticks(x)
            ax.set_xticklabels(
                [f"{r['experiment'].replace('exp_pub_','')}\nstep {r['step']}"
                 for _, r in pivot.iterrows()],
                fontsize=8, rotation=0,
            )
            ax.set_ylabel("basin-predictability accuracy (top-1)")
            ax.set_ylim(0, 1)
            ax.axhline(0.5, color="#aaa", linestyle="--", linewidth=0.6)
            ax.set_title("Group-aware vs leak-allowing basin predictability\n"
                         "Δ = leakage from same-family trajectories in train+test")
            ax.legend(loc="lower right", fontsize=9)
            for i, row in pivot.iterrows():
                ax.text(i, max(row["stratified"], row["group"]) + 0.02,
                        f"Δ={row['delta']:+.2f}", ha="center", fontsize=8,
                        color="#333")
            fig.tight_layout()
            fig_path = REPO / "data" / "aggregated" / "group_aware_basin_pred.png"
            fig.savefig(fig_path, dpi=160, facecolor="white", bbox_inches="tight")
            plt.close(fig)
            print(f"wrote {fig_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
