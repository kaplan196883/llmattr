"""
Why exactly 5 regimes? An unsupervised validation of the taxonomy.

For each experiment with sufficient diagnostics on disk, build a
canonical feature vector:

    [recurrence_rate, sharpness_dim_late, lambda_1_late,
     basin_predictability_acc_k10, adv_switch_rate (if pilot)]

Standardize, then run k-means at k = 2, 3, 4, 5, 6, 7. Report:
  - silhouette score per k
  - Calinski-Harabasz score per k
  - Davies-Bouldin index per k
  - confusion matrix (cluster vs ground-truth regime label) at the
    best k

If our 5-regime claim is mechanistically meaningful, then unsupervised
clustering on diagnostics that were measured *after* the regime labels
were assigned should recover ~5 clusters that match those labels.

Outputs:
  data/aggregated/regime_cluster_analysis/feature_matrix.csv
  data/aggregated/regime_cluster_analysis/cluster_scores.csv
  data/aggregated/regime_cluster_analysis/cluster_scatter.png
  data/aggregated/regime_cluster_analysis/cluster_dendrogram.png
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
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.preprocessing import StandardScaler
from scipy.cluster.hierarchy import linkage, dendrogram

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
OUT_DIR = DATA / "aggregated" / "regime_cluster_analysis"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# (experiment_id, regime_label) — manually curated set of experiments
# with reliable diagnostics. Each row is one independent measurement
# of the regime; multiple rows per regime test cluster cohesion.
EXPERIMENTS = [
    # Phase-1 pilots
    ("exp_op_O1_continue",                 "O1"),
    ("exp_op_O2_paraphrase_replace",       "O2"),
    ("exp_op_O3_summarize_negate",         "O3"),
    ("exp_op_O3b_summarize_negate_replace","O3"),
    ("exp_op_O4_paraphrase_append",        "O1"),  # paraphrase+append → contractive-like
    ("exp_dialog_D1_curious_helpful",      "D1"),
    ("exp_dialog_D3_debate_advocate_skeptic","D1"),  # debate → also stylistic D1-class
    # Phase-2 publication-scale
    ("exp_pub_O1_continue",                       "O1"),
    ("exp_pub_O2_paraphrase_replace",             "O2"),
    ("exp_pub_O3_summarize_negate_replace",       "O3"),
    ("exp_pub_D1_dialog_curious_helpful_v2",      "D1"),
    # T-sweep cells (regime same, T varies — should cluster with parent)
    ("exp_pub_O1_Tsweep_T03", "O1"),
    ("exp_pub_O1_Tsweep_T06", "O1"),
    ("exp_pub_O1_Tsweep_T08", "O1"),
    ("exp_pub_O1_Tsweep_T12", "O1"),
    ("exp_pub_D1_Tsweep_T03", "D1"),
    ("exp_pub_D1_Tsweep_T06", "D1"),
    ("exp_pub_D1_Tsweep_T12", "D1"),
    # Phase-3 perturbation pilots (have adv_switch + canonical diagnostics)
    ("exp_perturb_O1_pilot", "O1"),
    ("exp_perturb_O2_pilot", "O2"),
    ("exp_perturb_O3_pilot", "O3"),
    ("exp_perturb_D1_pilot", "D1"),
    ("exp_perturb_D2_exploratory", "D2"),
    # D2 publication-scale
    ("exp_D2_exploratory_drilldown", "D2"),
]

REGIME_COLORS = {
    "O1": "#4a90e2", "O2": "#e24a4a", "O3": "#8b5cf6",
    "D1": "#5fa85f", "D2": "#d4a017",
}


def load_features(exp_id: str) -> dict | None:
    """Return canonical feature dict for one experiment (or None if data missing).

    Perturbation experiments have regime ∈ {control, neutral, lorem,
    adversarial} (per-condition) rather than the standard {recursive,
    no_feedback}. For those, we use the `control` condition as the
    canonical "this regime running without perturbation" comparison
    point (same operator, same prompts, just no injection)."""
    base = DATA / exp_id
    out = {"experiment_id": exp_id}
    is_perturb = "perturb" in exp_id or "drilldown" in exp_id

    # 1. recurrence_rate (pca10, context_tail). Use recursive for
    # standard experiments, control for perturbation experiments.
    canonical_regime = "control" if is_perturb else "recursive"
    rec_path = base / "metrics" / "recurrence.csv"
    if not rec_path.exists():
        return None
    rec = pd.read_csv(rec_path)
    sub_r = rec[(rec.observable == "context_tail") & (rec.space == "pca10") & (rec.regime == canonical_regime)]
    if not len(sub_r):
        # last-resort: any regime, take mean
        sub_r = rec[(rec.observable == "context_tail") & (rec.space == "pca10")]
    out["recurrence_rate"] = float(sub_r.recurrence_rate.mean()) if len(sub_r) else float("nan")

    # 2. sharpness_dim_late + lambda_1_late from dynamics.csv
    dyn_path = base / "metrics" / "dynamics.csv"
    if not dyn_path.exists():
        return None
    dyn = pd.read_csv(dyn_path)
    sub_d = dyn[(dyn.observable == "context_tail") & (dyn.regime == canonical_regime)]
    if not len(sub_d):
        sub_d = dyn[dyn.observable == "context_tail"]
    if not len(sub_d):
        return None
    out["sharpness_dim_late"] = float(sub_d.sharpness_dim_late.mean())
    out["lambda_1_late"] = float(sub_d.lambda_1_late.mean())

    # 3. basin pred acc(k=10) — context_tail
    bp_path = base / "reports" / "basin_predictability" / "basin_predictability.csv"
    if bp_path.exists():
        bp = pd.read_csv(bp_path)
        bp_sub = bp[(bp.observable == "context_tail") & (bp.regime == canonical_regime) & (bp.step == 10)]
        if not len(bp_sub):
            bp_sub = bp[(bp.observable == "context_tail") & (bp.step == 10)]
        if len(bp_sub) and not pd.isna(bp_sub.top1.iloc[0]):
            out["basin_pred_acc_k10"] = float(bp_sub.top1.iloc[0])
        else:
            out["basin_pred_acc_k10"] = float("nan")
    else:
        out["basin_pred_acc_k10"] = float("nan")

    # 4. adversarial switch rate (only available for perturbation experiments)
    sw_path = DATA / "aggregated" / "perturbation_cross_regime" / "cross_switching_rates.csv"
    if sw_path.exists():
        sw = pd.read_csv(sw_path)
        m = sw[(sw.exp == exp_id) & (sw.condition == "adversarial")]
        out["adv_switch_rate"] = float(m.switch_rate.iloc[0]) if len(m) else float("nan")
    else:
        out["adv_switch_rate"] = float("nan")

    return out


def build_feature_matrix() -> tuple[pd.DataFrame, np.ndarray, list[str]]:
    """Return (df, X, regime_labels) — df has metadata; X is the
    standardized feature matrix; regime_labels are the ground-truth
    regime tags."""
    rows = []
    labels = []
    for exp_id, regime in EXPERIMENTS:
        feats = load_features(exp_id)
        if feats is None:
            print(f"  SKIP {exp_id}: missing data")
            continue
        feats["regime"] = regime
        rows.append(feats)
        labels.append(regime)

    df = pd.DataFrame(rows)
    feat_cols = ["recurrence_rate", "sharpness_dim_late", "lambda_1_late",
                 "basin_pred_acc_k10", "adv_switch_rate"]
    # Drop rows with any NaN in the feature columns. For experiments
    # without adv_switch_rate (most non-perturbation experiments), fill
    # with the regime's mean from those that have it.
    if "adv_switch_rate" in df.columns:
        for regime in df.regime.unique():
            mask = df.regime == regime
            mean_val = df.loc[mask, "adv_switch_rate"].mean()
            df.loc[mask & df["adv_switch_rate"].isna(), "adv_switch_rate"] = mean_val
    df_clean = df.dropna(subset=feat_cols).reset_index(drop=True)
    labels = df_clean["regime"].tolist()
    X = df_clean[feat_cols].to_numpy()

    # Standardize
    scaler = StandardScaler()
    X_std = scaler.fit_transform(X)
    return df_clean, X_std, labels


def cluster_scores(X_std: np.ndarray, k_range: list[int]) -> pd.DataFrame:
    """Run k-means at each k; return a DataFrame of scores."""
    rows = []
    for k in k_range:
        if k > len(X_std) - 1:
            continue
        km = KMeans(n_clusters=k, n_init=20, random_state=42).fit(X_std)
        labels = km.labels_
        rows.append({
            "k": k,
            "inertia": float(km.inertia_),
            "silhouette": float(silhouette_score(X_std, labels)),
            "calinski_harabasz": float(calinski_harabasz_score(X_std, labels)),
            "davies_bouldin": float(davies_bouldin_score(X_std, labels)),
        })
    return pd.DataFrame(rows)


def confusion_at_k(X_std: np.ndarray, labels: list[str], k: int) -> pd.DataFrame:
    """K-means cluster assignment vs ground-truth regime label."""
    km = KMeans(n_clusters=k, n_init=20, random_state=42).fit(X_std)
    cluster_ids = km.labels_
    # build crosstab
    return pd.crosstab(
        pd.Series(labels, name="regime"),
        pd.Series(cluster_ids, name=f"cluster_k{k}")
    )


def make_plots(df: pd.DataFrame, X_std: np.ndarray, labels: list[str],
               scores: pd.DataFrame) -> None:
    # Scatter plot: PCA-2 of feature space, colored by regime label
    pca = PCA(n_components=2)
    XY = pca.fit_transform(X_std)
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    ax = axes[0]
    for regime in sorted(set(labels)):
        mask = np.array(labels) == regime
        ax.scatter(XY[mask, 0], XY[mask, 1],
                   color=REGIME_COLORS.get(regime, "#888"),
                   label=regime, s=120, alpha=0.85, edgecolors="black", linewidths=1)
    for i, (x, y) in enumerate(XY):
        ax.annotate(df.iloc[i].experiment_id.replace("exp_", "")[:18],
                    (x, y), fontsize=6, alpha=0.7,
                    xytext=(3, 3), textcoords="offset points")
    ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.0f}% var)")
    ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.0f}% var)")
    ax.set_title("Diagnostic feature space (PCA-2)\nground-truth regime labels")
    ax.legend(title="regime")
    ax.grid(alpha=0.3)

    # Score-vs-k plot
    ax = axes[1]
    ax.plot(scores.k, scores.silhouette, "o-", color="#4a90e2", label="silhouette ↑")
    ax2 = ax.twinx()
    ax2.plot(scores.k, scores.calinski_harabasz, "s--", color="#e24a4a", label="Calinski-Harabasz ↑")
    ax.set_xlabel("k (number of clusters)")
    ax.set_ylabel("silhouette score (higher = better)")
    ax2.set_ylabel("Calinski-Harabasz (higher = better)")
    ax.set_title("Cluster validity vs k\n(does k=5 win?)")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left")
    ax2.legend(loc="upper right")

    fig.tight_layout()
    fig.savefig(OUT_DIR / "cluster_scatter.png", dpi=120)
    plt.close(fig)

    # Hierarchical dendrogram
    fig, ax = plt.subplots(figsize=(12, 6))
    Z = linkage(X_std, method="ward")
    dendrogram(Z, labels=[f"{lbl}: {df.iloc[i].experiment_id.replace('exp_', '')[:25]}"
                          for i, lbl in enumerate(labels)],
               leaf_rotation=90, leaf_font_size=8)
    ax.set_title("Ward-linkage hierarchical clustering of experiments\n"
                 "(by canonical diagnostics)")
    ax.set_ylabel("Ward linkage distance")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "cluster_dendrogram.png", dpi=120)
    plt.close(fig)


def main() -> int:
    print("Loading features per experiment...")
    df, X_std, labels = build_feature_matrix()
    print(f"  loaded {len(df)} experiments across {len(set(labels))} regimes")
    print(f"  regimes: {sorted(set(labels))}")
    print(f"  feature dim: {X_std.shape[1]}")

    df.to_csv(OUT_DIR / "feature_matrix.csv", index=False)
    print(f"  wrote {OUT_DIR / 'feature_matrix.csv'}")

    print("\nClustering at k = 2..7...")
    scores = cluster_scores(X_std, list(range(2, 8)))
    scores.to_csv(OUT_DIR / "cluster_scores.csv", index=False)
    print(scores.round(3).to_string(index=False))

    best_k_silh = int(scores.loc[scores.silhouette.idxmax(), "k"])
    best_k_ch = int(scores.loc[scores.calinski_harabasz.idxmax(), "k"])
    best_k_db = int(scores.loc[scores.davies_bouldin.idxmin(), "k"])
    print(f"\nBest k by silhouette: {best_k_silh}")
    print(f"Best k by Calinski-Harabasz: {best_k_ch}")
    print(f"Best k by Davies-Bouldin (min): {best_k_db}")

    print(f"\nConfusion matrix at k=5 (cluster vs ground-truth regime):")
    cm5 = confusion_at_k(X_std, labels, 5)
    print(cm5.to_string())
    cm5.to_csv(OUT_DIR / "confusion_k5.csv")

    print(f"\nConfusion matrix at k=4 (for comparison):")
    cm4 = confusion_at_k(X_std, labels, 4)
    print(cm4.to_string())
    cm4.to_csv(OUT_DIR / "confusion_k4.csv")

    make_plots(df, X_std, labels, scores)
    print(f"\nWrote plots to {OUT_DIR}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
