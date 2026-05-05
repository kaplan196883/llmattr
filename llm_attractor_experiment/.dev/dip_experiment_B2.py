"""Experiment B2 — frozen-basis variant + family-cluster bootstrap CIs.

Two reviewer-driven additions to Experiment B:

(1) Frozen-basis long-horizon analysis. The canonical destination-coherent
    persistence is defined under PCA-10 + K-means k=12 fit on the ORIGINAL
    30-step experiment alone. The joint-fit Experiment B refits cluster
    geometry across original + extended embeddings, which is a different
    estimand. Here we fit the basis on the ORIGINAL only, project extended
    embeddings into the same PCA-10 space, assign to nearest frozen
    centroid, and recompute S^dst at terminal steps {29, 40, 50, 60, 70,
    79} under the frozen basis. This triangulates whether the dip closes
    when the canonical cluster definition is held fixed.

(2) Family-cluster bootstrap CIs for the dip contrast
        Delta(T) = S^dst_2000(T) - 0.5 * (S^dst_1500(T) + S^dst_3000(T))
    at each terminal step, under both joint-fit and frozen-basis. We
    resample prompt families with replacement (5 -> 5) and rebuild the
    contrast across n_boot bootstrap iterations. This is the family-aware
    interval the rest of the paper uses for ED50.

Outputs:
  data/aggregated/dip_mechanism_B/persistence_by_terminal_step_v2.csv
    rows: terminal_step, dose, basis (joint|frozen), S_dst, n_kicked
  data/aggregated/dip_mechanism_B/dip_contrast_ci.csv
    rows: terminal_step, basis, Delta_point, Delta_lo, Delta_hi
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT_DIR = DATA / "aggregated" / "dip_mechanism_B"

EXP_HIGH = "exp_perturb_O1_ed50_higher_noclip"
EXP_EXT  = "exp_perturb_O1_ed50_higher_noclip_extended"
TARGET_DOSES = (1500, 2000, 3000)
TARGET_REGIMES = {f"adversarial_dose{d}" for d in TARGET_DOSES}
TEST_TERMINAL_STEPS = (29, 40, 50, 60, 70, 79)
PRE_STEP = 14
INJECT_STEP = 15

N_BOOT = 2000
RNG_SEED = 42


def _dose(s):
    m = re.match(r"adversarial_dose(\d+)$", s)
    return int(m.group(1)) if m else None


def _load_high_dose_only(exp: str):
    X = np.load(DATA / exp / "embeddings" / "context_tail" / "embeddings.npy")
    meta = pd.read_parquet(DATA / exp / "embeddings" / "context_tail" / "metadata.parquet")
    keep = meta["regime"].isin(TARGET_REGIMES).to_numpy()
    return X[keep], meta.loc[keep].reset_index(drop=True)


def _label_pivot(meta: pd.DataFrame, label_col: str) -> pd.DataFrame:
    return meta.pivot_table(
        index=["regime", "prompt_family", "initial_condition_id", "run_id"],
        columns="step", values=label_col, aggfunc="first",
    )


def _persistence_per_traj(pivot: pd.DataFrame, terminal_step: int) -> pd.DataFrame:
    rows = []
    for (regime, fam, ic, run), srow in pivot.iterrows():
        pre = srow.get(PRE_STEP)
        post = srow.get(INJECT_STEP)
        end = srow.get(terminal_step)
        if pd.isna(pre) or pd.isna(post) or pd.isna(end):
            continue
        if int(post) == int(pre):
            continue
        rows.append({
            "regime": regime,
            "prompt_family": fam,
            "destcoh": int(end == post),
        })
    return pd.DataFrame(rows)


def _summary_from_perTraj(per_traj: pd.DataFrame) -> dict[int, float]:
    """{dose: S^dst} from a per-trajectory dataframe."""
    summary = per_traj.groupby("regime")["destcoh"].mean().reset_index()
    summary["dose"] = summary["regime"].map(_dose)
    return dict(zip(summary["dose"], summary["destcoh"]))


def _dip(s_by_dose: dict[int, float]) -> float:
    if not all(d in s_by_dose for d in TARGET_DOSES):
        return float("nan")
    return float(s_by_dose[2000] - 0.5 * (s_by_dose[1500] + s_by_dose[3000]))


def _bootstrap_dip_ci(
    per_traj: pd.DataFrame, n_boot: int, rng: np.random.Generator
) -> tuple[float, float, float]:
    """Family-cluster bootstrap of Delta = S(2000) - 0.5(S(1500)+S(3000))."""
    families = sorted(per_traj["prompt_family"].unique())
    n_fams = len(families)
    by_fam = {f: per_traj[per_traj["prompt_family"] == f] for f in families}
    point = _dip(_summary_from_perTraj(per_traj))
    boot_dips = []
    for _ in range(n_boot):
        sampled_fams = rng.choice(families, size=n_fams, replace=True)
        chunks = [by_fam[f] for f in sampled_fams]
        resampled = pd.concat(chunks, ignore_index=True)
        s = _summary_from_perTraj(resampled)
        d = _dip(s)
        if not np.isnan(d):
            boot_dips.append(d)
    if not boot_dips:
        return point, float("nan"), float("nan")
    lo, hi = np.percentile(boot_dips, [2.5, 97.5])
    return point, float(lo), float(hi)


def _attach_dose_per_traj(per_traj: pd.DataFrame) -> pd.DataFrame:
    per_traj = per_traj.copy()
    per_traj["dose"] = per_traj["regime"].map(_dose)
    return per_traj


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(RNG_SEED)

    # Load original high-dose embeddings (the canonical-basis source)
    X_orig, meta_orig = _load_high_dose_only(EXP_HIGH)
    print(f"original high-dose embeddings: {X_orig.shape}")

    # Load extended embeddings (full set; metadata only has high-dose regimes,
    # since Experiment B was scoped to TARGET_DOSES already)
    X_ext = np.load(DATA / EXP_EXT / "embeddings" / "context_tail" / "embeddings.npy")
    meta_ext = pd.read_parquet(DATA / EXP_EXT / "embeddings" / "context_tail" / "metadata.parquet")
    print(f"extended embeddings:  {X_ext.shape}")

    # --------------------------------------------------------------
    # (A) Frozen-basis: fit PCA-10 + K-means k=12 on ORIGINAL only.
    # --------------------------------------------------------------
    pca_frozen = PCA(n_components=10, random_state=42).fit(X_orig)
    Xp_orig = pca_frozen.transform(X_orig)
    km_frozen = KMeans(n_clusters=12, random_state=42, n_init=10).fit(Xp_orig)
    meta_orig["frozen_cluster"] = km_frozen.labels_

    # Project extended embeddings into frozen basis, assign to nearest centroid
    Xp_ext = pca_frozen.transform(X_ext)
    # Distance to each centroid -> argmin
    d2 = ((Xp_ext[:, None, :] - km_frozen.cluster_centers_[None, :, :]) ** 2).sum(axis=2)
    meta_ext["frozen_cluster"] = d2.argmin(axis=1)

    # --------------------------------------------------------------
    # (B) Joint-basis: fit PCA-10 + K-means k=12 on the union (replicates
    # the Experiment B canonical analysis, used as comparator).
    # --------------------------------------------------------------
    X_all = np.vstack([X_orig, X_ext])
    meta_all = pd.concat([meta_orig.assign(_split="orig"),
                           meta_ext.assign(_split="ext")], ignore_index=True)
    pca_joint = PCA(n_components=10, random_state=42).fit(X_all)
    Xp_all = pca_joint.transform(X_all)
    km_joint = KMeans(n_clusters=12, random_state=42, n_init=10).fit(Xp_all)
    meta_all["joint_cluster"] = km_joint.labels_

    # The joint cluster column needs to be propagated back to per-trajectory
    # frames for both basis variants; we'll merge below.
    joint_orig = meta_all[meta_all["_split"] == "orig"][[
        "regime", "prompt_family", "initial_condition_id", "run_id", "step", "joint_cluster"
    ]].reset_index(drop=True)
    joint_ext = meta_all[meta_all["_split"] == "ext"][[
        "regime", "prompt_family", "initial_condition_id", "run_id", "step", "joint_cluster"
    ]].reset_index(drop=True)

    # --------------------------------------------------------------
    # Build pivots per basis. For each (regime, fam, ic, run), we need
    # cluster labels at PRE_STEP, INJECT_STEP, and the various terminal steps.
    # --------------------------------------------------------------
    # FROZEN-BASIS PIVOT
    f_orig = meta_orig[["regime", "prompt_family", "initial_condition_id",
                        "run_id", "step", "frozen_cluster"]].copy()
    f_ext = meta_ext[["regime", "prompt_family", "initial_condition_id",
                      "run_id", "step", "frozen_cluster"]].copy()
    f_all = pd.concat([f_orig, f_ext], ignore_index=True)
    pivot_frozen = _label_pivot(f_all, "frozen_cluster")

    # JOINT-BASIS PIVOT
    j_all = pd.concat([joint_orig, joint_ext], ignore_index=True)
    pivot_joint = _label_pivot(j_all, "joint_cluster")

    # --------------------------------------------------------------
    # (C) Persistence by terminal step under each basis, with bootstrap CIs
    # --------------------------------------------------------------
    rows_summary = []
    rows_ci = []

    for basis_name, pivot in (("frozen", pivot_frozen), ("joint", pivot_joint)):
        print(f"\n=== basis: {basis_name} ===")
        print(f"{'T':>3}  {'S_1500':>8}  {'S_2000':>8}  {'S_3000':>8}  "
              f"{'dip':>8}  {'95% CI':>21}  n_kicked_2000")
        for T in TEST_TERMINAL_STEPS:
            if T not in pivot.columns:
                print(f"  T={T} not available, skipping")
                continue
            per_traj = _attach_dose_per_traj(_persistence_per_traj(pivot, T))
            if per_traj.empty:
                continue
            s_by_dose = _summary_from_perTraj(per_traj)
            n_kicked_2000 = int((per_traj["dose"] == 2000).sum())
            for d, s in s_by_dose.items():
                rows_summary.append({
                    "basis": basis_name,
                    "terminal_step": T,
                    "dose": int(d),
                    "S_dst": float(s),
                    "n_kicked": int((per_traj["dose"] == d).sum()),
                })
            point, lo, hi = _bootstrap_dip_ci(per_traj, N_BOOT, rng)
            rows_ci.append({
                "basis": basis_name,
                "terminal_step": T,
                "delta_point": point,
                "delta_lo_95": lo,
                "delta_hi_95": hi,
            })
            print(f"  {T:>3}  {s_by_dose.get(1500, np.nan):>8.3f}  "
                  f"{s_by_dose.get(2000, np.nan):>8.3f}  "
                  f"{s_by_dose.get(3000, np.nan):>8.3f}  "
                  f"{point:>+8.3f}  [{lo:>+6.3f}, {hi:>+6.3f}]  {n_kicked_2000}")

    pd.DataFrame(rows_summary).to_csv(OUT_DIR / "persistence_by_terminal_step_v2.csv", index=False)
    pd.DataFrame(rows_ci).to_csv(OUT_DIR / "dip_contrast_ci.csv", index=False)
    print(f"\nwrote {OUT_DIR/'persistence_by_terminal_step_v2.csv'}, "
          f"{OUT_DIR/'dip_contrast_ci.csv'}")

    # --------------------------------------------------------------
    # (D) Print the canonical step-29 dip contrast under canonical
    # per-experiment fit, with family-cluster bootstrap.
    # This is the dip contrast the published §5.1.3 number (-0.140) refers to.
    # --------------------------------------------------------------
    print("\n=== canonical per-experiment fit at step 29 (paper's reported numbers) ===")
    pivot_canon = _label_pivot(meta_orig, "frozen_cluster")
    if 29 in pivot_canon.columns:
        per_traj = _attach_dose_per_traj(_persistence_per_traj(pivot_canon, 29))
        s_by_dose = _summary_from_perTraj(per_traj)
        point, lo, hi = _bootstrap_dip_ci(per_traj, N_BOOT, rng)
        print(f"  T=29  S(1500/2000/3000) = {s_by_dose.get(1500, np.nan):.3f} / "
              f"{s_by_dose.get(2000, np.nan):.3f} / "
              f"{s_by_dose.get(3000, np.nan):.3f}")
        print(f"  dip = {point:+.3f}  95% family-cluster CI = "
              f"[{lo:+.3f}, {hi:+.3f}]")


if __name__ == "__main__":
    main()
