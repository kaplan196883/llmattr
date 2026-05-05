"""Experiment A2 — finishing diagnostics.

(1) Hierarchical macro-merge: take K-means k=12 clusters, merge into
    k_macro in {3, 4, 6} via Ward agglomerative clustering of centroids.
    If the dip is microcluster-only (GPT-5.5's mechanism 2), it should
    largely disappear at the macro level.

(2) Transition entropy H(C_T | C_+, kicked) per dose. Mechanism 4
    (perturbation-induced exploration entropy) predicts dose 2000 has
    uniquely high destination scatter; ruled out if H_2000 < neighbor
    average + 0.25 bits.

Both diagnostics target the canonical observable + plus_step combo
(context_tail, plus_step=15) where the dip is sharpest.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT_DIR = DATA / "aggregated" / "dip_mechanism_A"

EXP_HIGH = "exp_perturb_O1_ed50_higher_noclip"
OBSERVABLE = "context_tail"
K_BASE = 12
K_MACRO_GRID = [3, 4, 6, 8]
INJECT_STEP = 15
PRE_STEP = 14
FINAL_STEP = 29


def _wilson(p: float, n: int) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    z = 1.959963984540054
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def _dose(s: str) -> int | None:
    m = re.match(r"adversarial_dose(\d+)$", s)
    return int(m.group(1)) if m else None


def _shannon_entropy_bits(counts: np.ndarray) -> float:
    p = counts / counts.sum() if counts.sum() else counts
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load + cluster the high-dose experiment exactly as the paper does
    X = np.load(DATA / EXP_HIGH / "embeddings" / OBSERVABLE / "embeddings.npy")
    meta = pd.read_parquet(DATA / EXP_HIGH / "embeddings" / OBSERVABLE / "metadata.parquet")
    pca = PCA(n_components=10, random_state=42)
    Xp = pca.fit_transform(X)
    km = KMeans(n_clusters=K_BASE, random_state=42, n_init=10)
    base_labels = km.fit_predict(Xp)
    base_centroids = km.cluster_centers_

    df = meta.copy()
    df["cluster_k12"] = base_labels

    # ============================================================
    # (1) Hierarchical macro-merge
    # ============================================================
    print("=" * 70)
    print("(1) Hierarchical macro-merge of K-means k=12 clusters")
    print("=" * 70)
    print(f"observable={OBSERVABLE}  experiment={EXP_HIGH}  base k=12")
    print()

    macro_results = []
    for k_macro in K_MACRO_GRID:
        agg = AgglomerativeClustering(n_clusters=k_macro, linkage="ward")
        macro_map = agg.fit_predict(base_centroids)  # length 12: each base cluster -> macro id
        df[f"cluster_macro{k_macro}"] = df["cluster_k12"].map(dict(enumerate(macro_map)))

        pivot = df.pivot_table(
            index=["regime", "prompt_family", "initial_condition_id", "run_id"],
            columns="step", values=f"cluster_macro{k_macro}", aggfunc="first",
        )
        rows = []
        for (regime, fam, ic, run), srow in pivot.iterrows():
            if regime == "control":
                continue
            pre = srow.get(PRE_STEP)
            post = srow.get(INJECT_STEP)
            end = srow.get(FINAL_STEP)
            if pd.isna(pre) or pd.isna(post) or pd.isna(end):
                continue
            rows.append({
                "regime": regime,
                "kicked": int(post != pre),
                "destcoh": int(end == post and post != pre),
                "srcesc": int(end != pre and post != pre),
                "post_cluster": int(post),
                "end_cluster": int(end),
            })
        df_p = pd.DataFrame(rows)
        summary = df_p.groupby("regime").agg(
            n=("regime", "count"),
            kicked=("kicked", "sum"),
            destcoh=("destcoh", "sum"),
            srcesc=("srcesc", "sum"),
        ).reset_index()
        summary["dose"] = summary["regime"].map(_dose)
        summary = summary.dropna(subset=["dose"]).sort_values("dose").copy()
        summary["pct_destcoh"] = summary["destcoh"] / summary["n"]
        summary["pct_kicked"] = summary["kicked"] / summary["n"]
        summary["pct_srcesc"] = summary["srcesc"] / summary["n"]
        ci = summary.apply(
            lambda r: _wilson(r["pct_destcoh"], r["n"]), axis=1, result_type="expand"
        )
        summary["lo"] = ci[0]
        summary["hi"] = ci[1]

        # Print per-dose table
        print(f"--- macro k={k_macro} ---")
        for _, r in summary.iterrows():
            print(f"  dose {int(r['dose']):>5d}  S^dst={r['pct_destcoh']:.3f} "
                  f"[{r['lo']:.2f},{r['hi']:.2f}]  kicked={r['pct_kicked']:.3f}  "
                  f"srcesc={r['pct_srcesc']:.3f}")
        # Dip magnitude
        g = summary.set_index("dose")["pct_destcoh"]
        if all(d in g.index for d in (1500, 2000, 3000)):
            dip = float(g[2000] - 0.5 * (g[1500] + g[3000]))
            print(f"  dip = S(2000) - mean(S(1500),S(3000)) = {dip:+.3f}")
            macro_results.append({
                "k_macro": k_macro,
                "S_1500": g[1500], "S_2000": g[2000], "S_3000": g[3000],
                "dip": dip,
            })
        print()

    # ============================================================
    # (2) Transition entropy H(C_T | C_+) by dose
    # ============================================================
    print("=" * 70)
    print("(2) Transition entropy H(C_T | C_+, kicked) by dose under k=12")
    print("=" * 70)
    print()

    pivot = df.pivot_table(
        index=["regime", "prompt_family", "initial_condition_id", "run_id"],
        columns="step", values="cluster_k12", aggfunc="first",
    )
    rows = []
    for (regime, fam, ic, run), srow in pivot.iterrows():
        if regime == "control":
            continue
        pre = srow.get(PRE_STEP)
        post = srow.get(INJECT_STEP)
        end = srow.get(FINAL_STEP)
        if pd.isna(pre) or pd.isna(post) or pd.isna(end):
            continue
        if int(post) == int(pre):  # not kicked
            continue
        rows.append({
            "regime": regime,
            "post_cluster": int(post),
            "end_cluster": int(end),
        })
    dfk = pd.DataFrame(rows)
    dfk["dose"] = dfk["regime"].map(_dose)
    dfk = dfk.dropna(subset=["dose"])
    dfk["dose"] = dfk["dose"].astype(int)

    ent_rows = []
    for dose in sorted(dfk["dose"].unique()):
        sub = dfk[dfk["dose"] == dose]
        joint = sub.groupby(["post_cluster", "end_cluster"]).size().unstack(fill_value=0)
        if joint.empty:
            continue
        row_totals = joint.sum(axis=1).to_numpy(dtype=float)
        weights = row_totals / row_totals.sum() if row_totals.sum() else row_totals
        cond_entropies = []
        for i, total in enumerate(row_totals):
            if total == 0:
                cond_entropies.append(0.0)
            else:
                cond_entropies.append(_shannon_entropy_bits(joint.iloc[i].to_numpy()))
        H = float(np.dot(weights, cond_entropies))
        n_unique_C_T_given_kick = int((joint > 0).any(axis=0).sum())
        max_share = float(joint.sum(axis=0).max() / joint.sum().sum())
        ent_rows.append({
            "dose": dose,
            "n_kicked": int(sub.shape[0]),
            "H_T_given_plus_bits": H,
            "n_unique_terminal_clusters": n_unique_C_T_given_kick,
            "max_terminal_share": max_share,
        })
    ent_df = pd.DataFrame(ent_rows)
    print(ent_df.to_string(index=False))

    # Predicted-by-mechanism-4 contrast: H(2000) vs neighbor avg
    if all(d in ent_df["dose"].values for d in (1500, 2000, 3000)):
        h = ent_df.set_index("dose")["H_T_given_plus_bits"]
        delta_h = float(h[2000] - 0.5 * (h[1500] + h[3000]))
        print(f"\nDelta_H = H(2000) - mean(H(1500), H(3000)) = {delta_h:+.3f} bits")
        if delta_h >= 0.25:
            print("  -> mechanism 4 (exploration entropy) SUPPORTED")
        else:
            print("  -> mechanism 4 RULED OUT (Delta_H < 0.25 bits)")

    # ============================================================
    # Save and print final verdict
    # ============================================================
    pd.DataFrame(macro_results).to_csv(OUT_DIR / "macro_merge.csv", index=False)
    ent_df.to_csv(OUT_DIR / "transition_entropy.csv", index=False)
    print(f"\nwrote {OUT_DIR/'macro_merge.csv'}, {OUT_DIR/'transition_entropy.csv'}")

    print("\n" + "=" * 70)
    print("VERDICTS")
    print("=" * 70)
    if macro_results:
        max_macro_dip = max(abs(r["dip"]) for r in macro_results)
        if max_macro_dip < 0.05:
            print(f"  Mechanism 2 (microcluster fragmentation): SUPPORTED. "
                  f"Macro-merge dips all |Delta| < 0.05 (max {max_macro_dip:.3f}).")
        else:
            print(f"  Mechanism 2 (microcluster fragmentation): NOT FULLY SUPPORTED. "
                  f"Max macro-merge dip {max_macro_dip:.3f} >= 0.05.")


if __name__ == "__main__":
    main()
