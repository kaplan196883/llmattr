"""
Aggregate per-pilot V* (geodesic) and Ward-merge-distance (RG dendrogram)
into wide tables matching ARTICLE.md §5.10.

Reads (per regime in {O1, O2, O3, D1}):
  data/exp_perturb_<R>_pilot/reports/perturbation/geodesic_barriers_summary.csv
  data/exp_perturb_<R>_pilot/reports/perturbation/rg_dendrogram_summary.csv

Writes:
  data/aggregated/perturbation_geometric_barriers/
    - v_star_table.csv       — regime × condition → V_star_mean
                                (matches §5.10 V* table, ARTICLE.md:1655–1658)
    - rg_merge_table.csv     — regime × condition → max_merge_distance
                                (matches §5.10 RG dendrogram table, ARTICLE.md:1684–1689)
    - geometric_barriers_long.csv  — long-form combined table
                                      (regime, condition, metric, value)

Run: `python -m scripts.aggregate_perturbation_geometric_barriers`
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from scripts.lib_load import read_experiment_csv
from src.utils.io import ensure_dir

REGIMES = [
    ("O1", "exp_perturb_O1_pilot"),
    ("O2", "exp_perturb_O2_pilot"),
    ("O3", "exp_perturb_O3_pilot"),
    ("D1", "exp_perturb_D1_pilot"),
    # D2 perturb only ran 2 of the 4 conditions (control + adversarial);
    # neutral / lorem cells in the wide tables will be NaN for D2.
    ("D2", "exp_perturb_D2_exploratory"),
]
CONDITIONS = ["control", "neutral", "lorem", "adversarial"]


def _wide(rows: list[dict], value_col: str) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return (
        df.pivot(index="regime", columns="condition", values=value_col)
        .reindex(index=[r for r, _ in REGIMES], columns=CONDITIONS)
        .reset_index()
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="aggregate_perturbation_geometric_barriers")
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args(argv)

    data_dir = Path(args.data_dir)
    out_dir = data_dir / "aggregated" / "perturbation_geometric_barriers"
    ensure_dir(out_dir)

    v_rows: list[dict] = []
    rg_rows: list[dict] = []
    long_rows: list[dict] = []

    for regime, exp_id in REGIMES:
        v_df = read_experiment_csv(
            data_dir, exp_id, ("reports", "perturbation", "geodesic_barriers_summary.csv")
        )
        rg_df = read_experiment_csv(
            data_dir, exp_id, ("reports", "perturbation", "rg_dendrogram_summary.csv")
        )
        if v_df is not None:
            for _, r in v_df.iterrows():
                v_rows.append({
                    "regime": regime,
                    "condition": r["condition"],
                    "V_star_mean": float(r["V_star_mean"]),
                    "V_star_min": float(r["V_star_min"]),
                    "V_star_max": float(r["V_star_max"]),
                    "n_basins": int(r["n_basins"]),
                    "n_geodesics": int(r["n_geodesics"]),
                    "source_exp": exp_id,
                })
                long_rows.append({
                    "regime": regime, "condition": r["condition"],
                    "metric": "V_star_mean", "value": float(r["V_star_mean"]),
                })
        if rg_df is not None:
            for _, r in rg_df.iterrows():
                rg_rows.append({
                    "regime": regime,
                    "condition": r["condition"],
                    "max_merge_distance": float(r["max_merge_distance"]),
                    "mean_merge_distance": float(r["mean_merge_distance"]),
                    "median_merge_distance": float(r["median_merge_distance"]),
                    "n_leaves": int(r["n_leaves"]),
                    "total_points": int(r["total_points"]),
                    "source_exp": exp_id,
                })
                long_rows.append({
                    "regime": regime, "condition": r["condition"],
                    "metric": "max_merge_distance", "value": float(r["max_merge_distance"]),
                })

    v_table = _wide(v_rows, "V_star_mean")
    rg_table = _wide(rg_rows, "max_merge_distance")
    long_df = pd.DataFrame(long_rows)

    v_table.to_csv(out_dir / "v_star_table.csv", index=False)
    rg_table.to_csv(out_dir / "rg_merge_table.csv", index=False)
    long_df.to_csv(out_dir / "geometric_barriers_long.csv", index=False)

    pd.DataFrame(v_rows).to_csv(out_dir / "v_star_full.csv", index=False)
    pd.DataFrame(rg_rows).to_csv(out_dir / "rg_merge_full.csv", index=False)

    print(f"wrote {out_dir / 'v_star_table.csv'}")
    print(v_table.to_string(index=False))
    print(f"wrote {out_dir / 'rg_merge_table.csv'}")
    print(rg_table.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
