"""
Build COVERAGE.csv — coverage matrix of analytical artifacts × experiments.

Rows: every `data/exp_*/` directory.
Columns: phase / regime / config metadata + presence (1/0) of each
analytical artifact (per-experiment metric CSVs, reports, perturbation
visualizations, animations).

Output: COVERAGE.csv at the repo root. Cells:
- metadata columns: string or int values
- presence columns: 1 if file exists, 0 otherwise
- count columns (n_*): integer counts

Run: `python -m scripts.build_coverage`
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"


def _phase_of(exp_id: str) -> str:
    if exp_id in ("exp_default", "exp_long", "exp_noclip"):
        return "0_pilot"
    if exp_id.startswith("exp_op_") or exp_id.startswith("exp_dialog_"):
        return "1_taxonomy"
    if exp_id.startswith("exp_pub_"):
        return "2_publication"
    if exp_id.startswith("exp_perturb_") or exp_id == "exp_D2_exploratory_drilldown":
        return "3_perturbation"
    return "?"


def _regime_of(exp_id: str) -> str:
    """Extract regime tag from the experiment id."""
    m = re.search(r"_(O1|O2|O3b|O3|O4|D1|D2|D3)_", exp_id)
    if m:
        return m.group(1)
    if exp_id in ("exp_default", "exp_long", "exp_noclip"):
        return "O1"
    if exp_id.endswith("_O1_pilot") or "_O1_" in exp_id:
        return "O1"
    if exp_id == "exp_D2_exploratory_drilldown":
        return "D2"
    return "?"


def _nudge_of(cfg: dict) -> str:
    if "loop_mode" in cfg:
        return str(cfg["loop_mode"])
    if "nudge" in cfg:
        return str(cfg["nudge"])
    return "?"


def _has(p: Path) -> int:
    return 1 if p.exists() else 0


def _count_glob(d: Path, pattern: str) -> int:
    return len(list(d.glob(pattern))) if d.exists() else 0


def _count_subdirs(d: Path) -> int:
    if not d.exists():
        return 0
    return sum(1 for c in d.iterdir() if c.is_dir())


def _row_for(exp_dir: Path) -> dict:
    eid = exp_dir.name
    cfg_path = exp_dir / "config.yaml"
    cfg: dict = {}
    if cfg_path.exists():
        try:
            with cfg_path.open("r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
        except Exception:
            cfg = {}

    raw = exp_dir / "raw"
    emb = exp_dir / "embeddings"
    metrics = exp_dir / "metrics"
    reports = exp_dir / "reports"
    plots = reports / "plots"
    pred = reports / "basin_predictability"
    pert = reports / "perturbation"

    fams = cfg.get("prompt_families") or []
    n_fams = len(fams)
    ics_per = cfg.get("initial_conditions_per_family")
    if ics_per is None and fams:
        ics_per = max(len(f.get("initial_conditions", [])) for f in fams)
    runs_per = cfg.get("runs_per_condition")
    steps_per_run = cfg.get("steps_per_run")
    n_traj = (
        n_fams * (ics_per or 0) * (runs_per or 0)
        if all(v is not None for v in (n_fams, ics_per, runs_per))
        else None
    )

    row = {
        # ---------- metadata ----------
        "experiment_id": eid,
        "phase": _phase_of(eid),
        "regime": _regime_of(eid),
        "nudge_mode": _nudge_of(cfg),
        "temperature": cfg.get("temperature"),
        "steps_per_run": steps_per_run,
        "runs_per_condition": runs_per,
        "n_families": n_fams or None,
        "ics_per_family": ics_per,
        "n_trajectories": n_traj,
        # ---------- raw / config ----------
        "has_config_yaml": _has(cfg_path),
        "has_steps_jsonl": _has(raw / "steps.jsonl"),
        "has_manifest": _has(raw / "manifest.json"),
        "has_run_log": _has(exp_dir / "run.log"),
        # ---------- embeddings ----------
        "n_observables_embedded": _count_subdirs(emb),
        # ---------- metrics ----------
        "has_recurrence_csv": _has(metrics / "recurrence.csv"),
        "has_dwell_csv": _has(metrics / "dwell.csv"),
        "has_basin_csv": _has(metrics / "basin.csv"),
        "has_basin_entry_csv": _has(metrics / "basin_entry_times.csv"),
        "has_late_recurrence_csv": _has(metrics / "late_recurrence.csv"),
        "has_exit_return_csv": _has(metrics / "exit_return.csv"),
        "has_periodicity_csv": _has(metrics / "periodicity.csv"),
        "has_dispersion_csv": _has(metrics / "dispersion.csv"),
        "has_dynamics_csv": _has(metrics / "dynamics.csv"),
        "has_bootstrap_summary": _has(metrics / "bootstrap_summary.csv"),
        "has_permutation_tests": _has(metrics / "permutation_tests.csv"),
        "has_explained_variance": _has(metrics / "explained_variance.json"),
        "n_pca_models": _count_glob(metrics, "pca_*_model.npz"),
        "n_pca_projections": _count_glob(metrics, "pca_*_*.csv") - _count_glob(metrics, "pca_*_explained_variance.csv"),
        "n_tsne_csvs": _count_glob(metrics, "tsne_*.csv"),
        "n_cluster_csvs": _count_glob(metrics, "clusters_*.csv"),
        # ---------- reports ----------
        "has_report_md": _has(reports / "report.md"),
        "has_report_operators_md": _has(reports / "report_operators.md"),
        "has_basin_predictability_csv": _has(pred / "basin_predictability.csv"),
        "has_basin_predictability_summary": _has(pred / "basin_predictability_summary.json"),
        "n_plot_pngs": _count_glob(plots, "*.png"),
        # ---------- perturbation visualizations ----------
        "has_switching_summary": _has(pert / "switching_summary.csv"),
        "has_relaxation_table": _has(pert / "relaxation_table.csv"),
        "has_relaxation_curves_png": _has(pert / "relaxation_curves.png"),
        "has_switching_rates_png": _has(pert / "switching_rates.png"),
        "has_geodesic_skeleton_png": _has(pert / "geodesic_skeleton_pca.png"),
        "has_geodesic_barriers_csv": _has(pert / "geodesic_barriers_pca.csv"),
        "has_geodesic_barriers_summary": _has(pert / "geodesic_barriers_summary.csv"),
        "has_rg_dendrogram_png": _has(pert / "rg_dendrogram_pca.png"),
        "has_rg_dendrogram_summary": _has(pert / "rg_dendrogram_summary.csv"),
        "has_bulk_landscape_png": _has(pert / "bulk_landscape_pca.png"),
        "has_flow_skeleton_png": _has(pert / "flow_skeleton_pca.png"),
        "has_rg_stack_png": _has(pert / "rg_stack_pca.png"),
        "has_G_streamlines": _has(pert / "G_streamlines_density_by_condition_pca.png"),
        "has_H_speed_streamlines": _has(pert / "H_speed_streamlines_by_condition_pca.png"),
        "has_I_divergence": _has(pert / "I_divergence_by_condition_pca.png"),
        "has_flow_pca_by_condition": _has(pert / "flow_pca_by_condition.png"),
        "has_flow_tsne_by_condition": _has(pert / "flow_tsne_by_condition.png"),
        "has_trajectories_tsne_by_condition": _has(pert / "trajectories_tsne_by_condition.png"),
        "n_animation_mp4": _count_glob(pert, "animation3d_*.mp4"),
        "n_animation_gif": _count_glob(pert, "animation3d_*.gif"),
    }
    return row


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="build_coverage")
    parser.add_argument("--data-dir", default=str(DATA_DIR))
    parser.add_argument("--out", default=str(REPO_ROOT / "COVERAGE.csv"))
    args = parser.parse_args(argv)

    data_dir = Path(args.data_dir)
    exp_dirs = sorted(p for p in data_dir.iterdir() if p.is_dir() and p.name.startswith("exp_"))
    print(f"scanning {len(exp_dirs)} experiment dirs under {data_dir}")

    rows = [_row_for(p) for p in exp_dirs]
    df = pd.DataFrame(rows)

    # Sort: phase ascending, then regime, then experiment_id
    df = df.sort_values(["phase", "regime", "experiment_id"]).reset_index(drop=True)

    out = Path(args.out)
    df.to_csv(out, index=False)
    print(f"wrote {out} ({len(df)} rows × {len(df.columns)} cols)")

    # Brief summary
    print("\nphase distribution:")
    print(df["phase"].value_counts().to_string())
    print("\nregime distribution:")
    print(df["regime"].value_counts().to_string())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
