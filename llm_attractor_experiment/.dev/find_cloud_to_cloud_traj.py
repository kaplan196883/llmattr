"""Scan all dose-1500/2000/3000 trajectories and rank them by how well they
start AND finish inside high-density regions of the joint cohort cloud
(i.e., the same density used for the iso-surface visualization). The goal
is to pick a single trajectory whose narrative is "comes from a cloud,
visits the perturbation kick, and lands in a cloud."

Density estimation matches the iso-surface generator
(grid_n=56, sigma=1.6, same as in youtube_long_trajectory_3d.py).
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter
from sklearn.decomposition import PCA

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
EXP_O = "exp_perturb_O1_ed50_higher_noclip"
EXP_E = "exp_perturb_O1_ed50_higher_noclip_extended"
TARGET_DOSES = (1500, 2000, 3000)
TOTAL_STEPS = 80


def main() -> None:
    X_o = np.load(DATA / EXP_O / "embeddings" / "context_tail" / "embeddings.npy")
    M_o = pd.read_parquet(DATA / EXP_O / "embeddings" / "context_tail" / "metadata.parquet").reset_index(drop=True)
    X_e = np.load(DATA / EXP_E / "embeddings" / "context_tail" / "embeddings.npy")
    M_e = pd.read_parquet(DATA / EXP_E / "embeddings" / "context_tail" / "metadata.parquet").reset_index(drop=True)

    candidates: list[tuple] = []  # (dose, fam, ic, run)
    paths: dict[tuple, np.ndarray] = {}
    for dose in TARGET_DOSES:
        regime = f"adversarial_dose{dose}"
        sub_o = M_o[M_o["regime"] == regime]
        sub_e = M_e[M_e["regime"] == regime]
        keys_o = set(sub_o.groupby(["prompt_family", "initial_condition_id", "run_id"]).size().index.tolist())
        keys_e = set(sub_e.groupby(["prompt_family", "initial_condition_id", "run_id"]).size().index.tolist())
        common = sorted(keys_o & keys_e)
        for k in common:
            fam, ic, run = k
            arr = np.zeros((TOTAL_STEPS, X_o.shape[1]), dtype=np.float32)
            ok = True
            for sub, X in [(sub_o, X_o), (sub_e, X_e)]:
                rows = sub[(sub.prompt_family == fam)
                           & (sub.initial_condition_id == ic)
                           & (sub.run_id == run)]
                for idx, r in rows.iterrows():
                    s = int(r["step"])
                    if 0 <= s < TOTAL_STEPS:
                        arr[s] = X[idx]
            # require all 80 steps populated
            if (arr.sum(axis=1) == 0).any():
                continue
            tup = (dose, fam, ic, run)
            candidates.append(tup)
            paths[tup] = arr
    print(f"candidates with full 0-79 paths: {len(candidates)}")

    # Joint PCA-3 across all candidates
    all_pts = np.concatenate(list(paths.values()), axis=0)
    pca = PCA(n_components=3, random_state=42).fit(all_pts)
    proj_paths = {k: pca.transform(v).astype(np.float32) for k, v in paths.items()}

    # Build density histogram on projection
    flat = np.concatenate(list(proj_paths.values()), axis=0)
    pmin = flat.min(axis=0)
    pmax = flat.max(axis=0)
    pad = 0.08 * (pmax - pmin)
    lo, hi = pmin - pad, pmax + pad
    grid_n = 56
    sigma = 1.6
    edges = [np.linspace(lo[d], hi[d], grid_n + 1) for d in range(3)]
    H, _ = np.histogramdd(flat, bins=edges)
    H = gaussian_filter(H, sigma=sigma)
    H_max = float(H.max())
    print(f"density H.max = {H_max:.2f} on grid {grid_n}^3")

    def density_at(p: np.ndarray) -> float:
        ix = [int(np.clip(np.searchsorted(edges[d], p[d]) - 1, 0, grid_n - 1)) for d in range(3)]
        return float(H[ix[0], ix[1], ix[2]])

    box_diag = float(np.linalg.norm(np.asarray(hi) - np.asarray(lo)))
    rows = []
    for k, proj in proj_paths.items():
        d_start = density_at(proj[0])
        d_end = density_at(proj[-1])
        leap = float(np.linalg.norm(proj[15] - proj[14]))
        sep = float(np.linalg.norm(proj[-1] - proj[0]))
        rows.append({
            "dose": k[0], "fam": k[1], "ic": k[2], "run": k[3],
            "density_start": d_start,
            "density_end": d_end,
            "min_endpoint_density": min(d_start, d_end),
            "leap_pca3": leap,
            "endpoint_separation": sep,
            "endpoint_separation_frac": sep / box_diag,
        })
    df = pd.DataFrame(rows)
    df["min_density_norm"] = df["min_endpoint_density"] / H_max

    # New score: SOURCE cloud + LARGE separation (different destination cloud) + visible leap
    leap_max = df["leap_pca3"].max()
    sep_max = df["endpoint_separation"].max()
    df["score_diff_clouds"] = (
        0.55 * df["min_density_norm"]
        + 0.30 * df["endpoint_separation"] / sep_max
        + 0.15 * df["leap_pca3"] / leap_max
    )

    df_sep = df.sort_values("score_diff_clouds", ascending=False)
    print("\nTop 12 by score_diff_clouds (source cloud + separation + visible leap):")
    print(df_sep.head(12)[["dose", "fam", "ic", "run",
                           "density_start", "density_end",
                           "min_density_norm",
                           "endpoint_separation", "endpoint_separation_frac",
                           "leap_pca3", "score_diff_clouds"]].to_string(index=False))

    # Strict filter: both endpoints above density 0.5 of max AND separation > 30% box-diag
    sf = df[(df["min_density_norm"] >= 0.20) &
            (df["endpoint_separation_frac"] >= 0.20)].sort_values(
                "endpoint_separation", ascending=False)
    print(f"\nStrict filter: min_density_norm>=0.20 AND separation_frac>=0.20 "
          f"-> {len(sf)} candidates")
    print(sf.head(12)[["dose", "fam", "ic", "run",
                        "density_start", "density_end",
                        "min_density_norm",
                        "endpoint_separation_frac",
                        "leap_pca3"]].to_string(index=False))


if __name__ == "__main__":
    main()
