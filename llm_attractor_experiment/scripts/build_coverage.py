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

# Cross-model suffixes (strip before set-membership / regex matching so
# `exp_pub_O1_continue_gpt4nano` resolves the same eligibility as
# `exp_pub_O1_continue` for animation / perturbation-pilot checks).
MODEL_SUFFIXES = ("_gpt4nano", "_minimax", "_m2_7", "_text01", "_haiku", "_claude")


def _base_id(exp_id: str) -> str:
    """Strip a known cross-model suffix to get the base experiment id."""
    for suf in MODEL_SUFFIXES:
        if exp_id.endswith(suf):
            return exp_id[: -len(suf)]
    return exp_id


def _phase_of(exp_id: str) -> str:
    base = _base_id(exp_id)
    if base in ("exp_default", "exp_long", "exp_noclip"):
        return "0_pilot"
    if base.startswith("exp_op_") or base.startswith("exp_dialog_"):
        return "1_taxonomy"
    if base.startswith("exp_pub_"):
        return "2_publication"
    if base.startswith("exp_perturb_") or base == "exp_D2_exploratory_drilldown":
        return "3_perturbation"
    return "?"


def _regime_of(exp_id: str) -> str:
    """Extract regime tag from the experiment id."""
    base = _base_id(exp_id)
    m = re.search(r"_(O1|O2|O3b|O3|O4|D1|D2|D3)_", base)
    if m:
        return m.group(1)
    # Match `_(O1|...)` at the very end of the base id (no trailing _).
    m = re.search(r"_(O1|O2|O3b|O3|O4|D1|D2|D3)$", base)
    if m:
        return m.group(1)
    if base in ("exp_default", "exp_long", "exp_noclip"):
        return "O1"
    if base == "exp_D2_exploratory_drilldown":
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


def _has_or_na(p: Path, applicable: bool) -> object:
    """Return 1 / 0 / '' (n/a) — '' means structurally not applicable to this experiment."""
    if not applicable:
        return ""
    return 1 if p.exists() else 0


def _count_or_na(d: Path, pattern: str, applicable: bool) -> object:
    if not applicable:
        return ""
    return _count_glob(d, pattern)


def _count_glob(d: Path, pattern: str) -> int:
    return len(list(d.glob(pattern))) if d.exists() else 0


def _count_subdirs(d: Path) -> int:
    if not d.exists():
        return 0
    return sum(1 for c in d.iterdir() if c.is_dir())


def _is_perturbation(eid: str) -> bool:
    return _base_id(eid).startswith("exp_perturb_")


def _is_full_perturb_pilot(eid: str) -> bool:
    """The 5 pilots that get the full geometric visualization suite (bulk +
    geodesic + RG + G/H/I + animations): O1/O2/O3/D1 main pilots + D2."""
    return _base_id(eid) in {
        "exp_perturb_O1_pilot",
        "exp_perturb_O2_pilot",
        "exp_perturb_O3_pilot",
        "exp_perturb_D1_pilot",
        "exp_perturb_D2_exploratory",
    }


def _is_main_4_pilot(eid: str) -> bool:
    """The 4 main pilots that get rg_stack_png (D2 doesn't run that script)."""
    return _base_id(eid) in {
        "exp_perturb_O1_pilot",
        "exp_perturb_O2_pilot",
        "exp_perturb_O3_pilot",
        "exp_perturb_D1_pilot",
    }


def _gets_animation(eid: str) -> bool:
    """Animations are rendered for the 5 perturb pilots (4 conds each) and
    the 4 pub experiments (1 'recursive' anim each)."""
    return _is_full_perturb_pilot(eid) or _base_id(eid) in {
        "exp_pub_O1_continue",
        "exp_pub_O2_paraphrase_replace",
        "exp_pub_O3_summarize_negate_replace",
        "exp_pub_D1_dialog_curious_helpful_v2",
    }


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

    is_pert = _is_perturbation(eid)
    is_full_pert = _is_full_perturb_pilot(eid)
    is_main4 = _is_main_4_pilot(eid)
    has_anim = _gets_animation(eid)
    # basin_entry / exit_return are computed only for `regime=recursive`
    # trajectories. Perturbation experiments have no recursive regime
    # (regime encodes the condition), so these cells are structurally
    # not applicable.
    runs_recursive = not is_pert
    # Permutation tests need recursive vs time_shuffled comparison; only
    # applicable when time_shuffled is among the baselines AND the
    # experiment has a recursive regime (perturbation experiments don't).
    baseline_modes = cfg.get("baseline_modes") or []
    has_time_shuffled = "time_shuffled" in baseline_modes and runs_recursive
    # bootstrap_summary needs `cfg.bootstrap.enabled = True`
    bootstrap_enabled = bool((cfg.get("bootstrap") or {}).get("enabled", False))
    # v2 metrics gated by their own enable flags
    basin_entry_enabled = bool((cfg.get("basin_entry") or {}).get("enabled", False))
    exit_return_enabled = bool((cfg.get("exit_return") or {}).get("enabled", False))
    late_recurrence_enabled = bool((cfg.get("late_recurrence") or {}).get("enabled", False))
    # Lyapunov / sharpness need >= 2 runs per IC for ensemble-spread covariance
    runs_per = cfg.get("runs_per_condition") or 0
    can_compute_dynamics = runs_per >= 2
    # Basin predictability targets `recursive` vs `no_feedback` regimes;
    # not meaningful for multi-condition perturbation data.
    can_basin_predict = not is_pert

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
        "has_basin_entry_csv": _has_or_na(metrics / "basin_entry_times.csv", runs_recursive and basin_entry_enabled),
        "has_late_recurrence_csv": _has_or_na(metrics / "late_recurrence.csv", late_recurrence_enabled),
        "has_exit_return_csv": _has_or_na(metrics / "exit_return.csv", runs_recursive and exit_return_enabled),
        "has_periodicity_csv": _has(metrics / "periodicity.csv"),
        "has_dispersion_csv": _has(metrics / "dispersion.csv"),
        "has_dynamics_csv": _has_or_na(metrics / "dynamics.csv", can_compute_dynamics),
        "has_bootstrap_summary": _has_or_na(metrics / "bootstrap_summary.csv", bootstrap_enabled),
        "has_permutation_tests": _has_or_na(metrics / "permutation_tests.csv", has_time_shuffled),
        "has_explained_variance": _has(metrics / "explained_variance.json"),
        "n_pca_models": _count_glob(metrics, "pca_*_model.npz"),
        "n_pca_projections": _count_glob(metrics, "pca_*_*.csv") - _count_glob(metrics, "pca_*_explained_variance.csv"),
        "n_tsne_csvs": _count_glob(metrics, "tsne_*.csv"),
        "n_cluster_csvs": _count_glob(metrics, "clusters_*.csv"),
        # ---------- reports ----------
        "has_report_md": _has(reports / "report.md"),
        "has_report_operators_md": _has(reports / "report_operators.md"),
        "has_basin_predictability_csv": _has_or_na(pred / "basin_predictability.csv", can_basin_predict),
        "has_basin_predictability_summary": _has_or_na(pred / "basin_predictability_summary.json", can_basin_predict),
        "n_plot_pngs": _count_glob(plots, "*.png"),
        # ---------- perturbation visualizations ----------
        # Switching/relaxation/G/H/I/flow_*_by_condition: applicable only to
        # multi-condition perturbation experiments.
        "has_switching_summary": _has_or_na(pert / "switching_summary.csv", is_pert),
        "has_relaxation_table": _has_or_na(pert / "relaxation_table.csv", is_pert),
        "has_relaxation_curves_png": _has_or_na(pert / "relaxation_curves.png", is_pert),
        "has_switching_rates_png": _has_or_na(pert / "switching_rates.png", is_pert),
        # geodesic_skeleton/RG/bulk/flow_skeleton: pub experiments also have
        # these (single-condition versions); we keep these applicable everywhere.
        "has_geodesic_skeleton_png": _has(pert / "geodesic_skeleton_pca.png"),
        "has_geodesic_barriers_csv": _has_or_na(pert / "geodesic_barriers_pca.csv", is_full_pert),
        "has_geodesic_barriers_summary": _has_or_na(pert / "geodesic_barriers_summary.csv", is_full_pert),
        "has_rg_dendrogram_png": _has(pert / "rg_dendrogram_pca.png"),
        "has_rg_dendrogram_summary": _has_or_na(pert / "rg_dendrogram_summary.csv", is_full_pert),
        "has_bulk_landscape_png": _has(pert / "bulk_landscape_pca.png"),
        "has_flow_skeleton_png": _has(pert / "flow_skeleton_pca.png"),
        "has_rg_stack_png": _has_or_na(pert / "rg_stack_pca.png", is_main4),
        # G/H/I are inherently multi-condition: only perturbation experiments
        "has_G_streamlines": _has_or_na(pert / "G_streamlines_density_by_condition_pca.png", is_pert),
        "has_H_speed_streamlines": _has_or_na(pert / "H_speed_streamlines_by_condition_pca.png", is_pert),
        "has_I_divergence": _has_or_na(pert / "I_divergence_by_condition_pca.png", is_pert),
        "has_flow_pca_by_condition": _has_or_na(pert / "flow_pca_by_condition.png", is_pert),
        "has_flow_tsne_by_condition": _has_or_na(pert / "flow_tsne_by_condition.png", is_pert),
        "has_trajectories_tsne_by_condition": _has_or_na(pert / "trajectories_tsne_by_condition.png", is_pert),
        # Animations: 5 perturb pilots + 4 pub experiments
        "n_animation_mp4": _count_or_na(pert, "animation3d_*.mp4", has_anim),
        "n_animation_gif": _count_or_na(pert, "animation3d_*.gif", has_anim),
    }

    # Compute per-row coverage: filled / applicable across the boolean cells.
    coverage_cols = [k for k, v in row.items()
                     if (k.startswith("has_") or k == "n_animation_mp4")]
    n_applicable = sum(1 for k in coverage_cols if row[k] != "")
    n_filled = sum(1 for k in coverage_cols
                   if row[k] != "" and (row[k] == 1 or (isinstance(row[k], int) and row[k] > 0)))
    row["n_applicable_artifacts"] = n_applicable
    row["n_present_artifacts"] = n_filled
    row["coverage_pct"] = round(100 * n_filled / n_applicable, 1) if n_applicable else 0.0
    return row


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="build_coverage")
    parser.add_argument("--data-dir", default=str(DATA_DIR))
    parser.add_argument("--out", default=str(REPO_ROOT / "COVERAGE.csv"))
    parser.add_argument(
        "--filter", default=None,
        help="glob pattern restricting which exp_* dirs are scanned "
             "(e.g. 'exp_*_gpt4nano' for the nano cross-model sweep, "
             "or 'exp_*[!_gpt4nano]*' to exclude it)",
    )
    parser.add_argument(
        "--exclude-suffixes", default=None,
        help="comma-separated suffixes to exclude (e.g. '_gpt4nano,_minimax')",
    )
    args = parser.parse_args(argv)

    data_dir = Path(args.data_dir)
    if args.filter:
        exp_dirs = sorted(p for p in data_dir.glob(args.filter) if p.is_dir() and p.name.startswith("exp_"))
    else:
        exp_dirs = sorted(p for p in data_dir.iterdir() if p.is_dir() and p.name.startswith("exp_"))
    if args.exclude_suffixes:
        bad = tuple(s.strip() for s in args.exclude_suffixes.split(",") if s.strip())
        exp_dirs = [p for p in exp_dirs if not p.name.endswith(bad)]
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
