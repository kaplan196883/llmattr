"""
Cluster-stability check for the publication-scale regimes.

Addresses review weakness #2: "K-means clusters in joint PCA-10 may
split a single semantic basin or merge distinct basins. Final-cluster
difference is not equivalent to X_T ∈ B_2 in the formal definition of
§3.1.1." The reviewer asked: validate clusters as basins via stability
across k, bootstrap, and alternative methods (HDBSCAN, spectral).

This script does that on cached publication-scale trajectory
embeddings (no API calls, no new data). For each regime in:
    exp_pub_O1_continue, exp_pub_O2_paraphrase_replace,
    exp_pub_O3_summarize_negate, exp_pub_D1_dialog_curious_helpful_v2

we compute:

  1. K-means at k = 4, 8, 12, 16, 24
  2. Spectral clustering at k = 4, 8, 12
  3. HDBSCAN with auto cluster count

then compare each pair of partitions via Adjusted Rand Index (ARI) and
Normalized Mutual Information (NMI). High ARI between K-means@k=12
and HDBSCAN means the clusters are not a K-means artifact.

Output: data/<exp>/reports/cluster_stability/{stability.csv, summary.png}
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
from sklearn.cluster import HDBSCAN, KMeans, SpectralClustering
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

REPO = Path(__file__).resolve().parent.parent

DEFAULT_EXPERIMENTS = [
    "exp_pub_O1_continue",
    "exp_pub_O2_paraphrase_replace",
    "exp_pub_O3_summarize_negate_replace",
    "exp_pub_D1_dialog_curious_helpful_v2",
]


def _load_late_window(exp_dir: Path, observable: str = "context_tail",
                      late_fraction: float = 0.3,
                      max_points: int = 3000) -> np.ndarray | None:
    """Load embeddings restricted to the late-window steps for each
    trajectory. Returns (N, D) array or None if data missing.
    Caps at max_points (uniform random subsample) so spectral
    clustering doesn't blow up on full publication-scale clouds."""
    vec_p = exp_dir / "embeddings" / observable / "embeddings.npy"
    meta_p = exp_dir / "embeddings" / observable / "metadata.parquet"
    if not vec_p.exists() or not meta_p.exists():
        return None
    print(f"  loading {vec_p} ...", flush=True)
    vecs = np.load(vec_p)
    meta = pd.read_parquet(meta_p).reset_index(drop=True)
    print(f"  loaded {vecs.shape}, {len(meta)} meta rows", flush=True)

    # If dialog (has role column), pick the agent role for D1.
    if "role" in meta.columns:
        roles = sorted(meta["role"].dropna().unique().tolist())
        target = "agent" if "agent" in roles else (roles[-1] if roles else None)
        if target is None:
            return None
        mask = (meta["role"] == target).values
        vecs = vecs[mask]
        meta = meta[mask].reset_index(drop=True)

    # Late window: last late_fraction of each trajectory's steps.
    n_steps = int(meta["step"].max()) + 1
    cutoff = int(n_steps * (1 - late_fraction))
    mask = meta["step"].values >= cutoff
    sub = vecs[mask]
    print(f"  late-window points: {sub.shape[0]}", flush=True)
    if sub.shape[0] > max_points:
        rng = np.random.default_rng(42)
        idx = rng.choice(sub.shape[0], size=max_points, replace=False)
        sub = sub[idx]
        print(f"  subsampled to {max_points}", flush=True)
    return sub


def _cluster_partitions(X: np.ndarray, ks: list[int]) -> dict[str, np.ndarray]:
    """Compute several partitions of X."""
    out: dict[str, np.ndarray] = {}

    # Reduce to PCA-10 first (matches the paper's analysis pipeline).
    n_components = min(10, X.shape[0] - 1, X.shape[1])
    Xr = PCA(n_components=n_components, random_state=42).fit_transform(X)

    for k in ks:
        if X.shape[0] < 2 * k:
            continue
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        out[f"kmeans_k{k}"] = km.fit_predict(Xr)

    for k in [k for k in ks if k <= 12]:
        if X.shape[0] < 4 * k:
            continue
        try:
            sp = SpectralClustering(
                n_clusters=k, random_state=42, n_init=5,
                affinity="nearest_neighbors", n_neighbors=min(20, X.shape[0] // 4),
                assign_labels="kmeans",
            )
            out[f"spectral_k{k}"] = sp.fit_predict(Xr)
        except Exception as e:
            print(f"  spectral_k{k} failed: {e}")

    try:
        hdb = HDBSCAN(min_cluster_size=max(5, X.shape[0] // 100),
                      min_samples=5, allow_single_cluster=False)
        labels = hdb.fit_predict(Xr)
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        if n_clusters >= 2:
            out[f"hdbscan_k{n_clusters}"] = labels
        else:
            print(f"  hdbscan: only {n_clusters} clusters, skipping")
    except Exception as e:
        print(f"  hdbscan failed: {e}")

    return out


def _pairwise_agreement(parts: dict[str, np.ndarray]) -> pd.DataFrame:
    names = list(parts.keys())
    rows = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            la, lb = parts[a], parts[b]
            # HDBSCAN's -1 noise label: skip those points for ARI.
            mask = (la >= 0) & (lb >= 0)
            if mask.sum() < 10:
                continue
            ari = adjusted_rand_score(la[mask], lb[mask])
            nmi = normalized_mutual_info_score(la[mask], lb[mask])
            rows.append({
                "method_a": a, "method_b": b,
                "n_pts_compared": int(mask.sum()),
                "ari": float(ari), "nmi": float(nmi),
            })
    return pd.DataFrame(rows)


def _plot_heatmap(df: pd.DataFrame, exp_label: str, out_path: Path) -> None:
    methods = sorted(set(df["method_a"]).union(df["method_b"]))
    n = len(methods)
    M = np.full((n, n), np.nan)
    for _, r in df.iterrows():
        i, j = methods.index(r["method_a"]), methods.index(r["method_b"])
        M[i, j] = r["ari"]; M[j, i] = r["ari"]
    np.fill_diagonal(M, 1.0)

    fig, ax = plt.subplots(figsize=(7, 6), facecolor="white")
    im = ax.imshow(M, cmap="RdYlGn", vmin=0, vmax=1, aspect="equal")
    ax.set_xticks(range(n)); ax.set_yticks(range(n))
    ax.set_xticklabels(methods, rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels(methods, fontsize=9)
    for i in range(n):
        for j in range(n):
            if not np.isnan(M[i, j]):
                ax.text(j, i, f"{M[i,j]:.2f}", ha="center", va="center",
                        color="black" if M[i, j] > 0.4 else "white", fontsize=8)
    ax.set_title(f"Cluster-stability ARI matrix: {exp_label}\n"
                 f"(higher = clusters reproduce across methods)", fontsize=11)
    plt.colorbar(im, ax=ax, label="Adjusted Rand Index")
    fig.tight_layout()
    fig.savefig(out_path, dpi=160, facecolor="white", bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiments", nargs="+", default=DEFAULT_EXPERIMENTS)
    ap.add_argument("--observable", default="context_tail")
    ap.add_argument("--ks", nargs="+", type=int, default=[4, 8, 12, 16, 24])
    args = ap.parse_args()

    summary_rows = []
    for exp in args.experiments:
        exp_dir = REPO / "data" / exp
        print(f"\n=== {exp} ===")
        X = _load_late_window(exp_dir, args.observable)
        if X is None:
            print(f"  skip: embeddings not found at {exp_dir}")
            continue
        print(f"  late-window points: {X.shape}")
        parts = _cluster_partitions(X, args.ks)
        print(f"  computed {len(parts)} partitions: {list(parts)}")
        agreement = _pairwise_agreement(parts)
        if agreement.empty:
            print("  no comparable partitions; skipping")
            continue
        out_dir = exp_dir / "reports" / "cluster_stability"
        out_dir.mkdir(parents=True, exist_ok=True)
        agreement.to_csv(out_dir / "stability.csv", index=False)
        _plot_heatmap(agreement, exp, out_dir / "stability_heatmap.png")
        # Headline: ARI between kmeans_k12 and other methods.
        ref = "kmeans_k12"
        ref_rows = agreement[
            (agreement["method_a"] == ref) | (agreement["method_b"] == ref)
        ].copy()
        if not ref_rows.empty:
            ref_rows["other"] = ref_rows.apply(
                lambda r: r["method_b"] if r["method_a"] == ref else r["method_a"],
                axis=1,
            )
            print(ref_rows[["other", "ari", "nmi"]].to_string(index=False))
        # Headline summary: median ARI involving kmeans_k12 vs any non-kmeans.
        non_km = ref_rows[~ref_rows["other"].str.startswith("kmeans")] \
            if not ref_rows.empty else pd.DataFrame()
        median_ari_vs_kmeans = float(non_km["ari"].median()) if len(non_km) else np.nan
        summary_rows.append({
            "experiment": exp,
            "n_late_window_points": int(X.shape[0]),
            "n_partitions": len(parts),
            "median_ari_kmeans12_vs_other_methods": median_ari_vs_kmeans,
        })
        print(f"  wrote {out_dir/'stability.csv'} and stability_heatmap.png")

    summary = pd.DataFrame(summary_rows)
    if not summary.empty:
        out = REPO / "data" / "aggregated" / "cluster_stability_summary.csv"
        out.parent.mkdir(parents=True, exist_ok=True)
        summary.to_csv(out, index=False)
        print(f"\nwrote {out}")
        print(summary.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
