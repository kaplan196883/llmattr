"""
Run Lyapunov + Sharpness Dimension analysis across cached experiments.

Usage
-----
    # single experiment:
    python -m src.experiments.dynamics.analyze --config configs/long.yaml

    # sweep across all cached experiments:
    python -m src.experiments.dynamics.analyze --all

Outputs CSV per experiment at:
    data/<experiment_id>/metrics/dynamics.csv

And a cross-experiment summary when --all is used:
    data/dynamics_cross_experiment.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import Config, load_config
from src.experiments.dynamics.lyapunov import (
    LyapunovSpectrum,
    compute_lyapunov_spectrum,
    ftle_from_spread,
)
from src.experiments.dynamics.sharpness_dim import (
    SharpnessDimension,
    effective_rank,
    sharpness_dimension,
)
from src.utils.io import ensure_dir, load_npy, read_parquet, write_csv
from src.utils.logging import get_logger, setup_logging

log = get_logger(__name__)


def _iter_ic_ensembles(
    vecs: np.ndarray, meta: pd.DataFrame
) -> dict[tuple, np.ndarray]:
    """
    Group embeddings by (regime, prompt_family, initial_condition_id).
    For each group, stack runs as (N, T, d) where N = number of runs and
    T = steps_per_run. Returns a dict keyed by (regime, family, ic).
    Only groups with N >= 2 runs and consistent T are kept.
    """
    key_cols = ["regime", "prompt_family", "initial_condition_id"]
    out: dict[tuple, np.ndarray] = {}
    grouped = meta.groupby(key_cols, dropna=False)
    for keys, sub in grouped:
        if len(sub["run_id"].unique()) < 2:
            continue
        runs: list[np.ndarray] = []
        T_ref: int | None = None
        ok = True
        for _rid, run_sub in sub.groupby("run_id", dropna=False):
            run_sub = run_sub.sort_values("step")
            idx = run_sub.index.to_numpy()
            run_vecs = vecs[idx]  # (T_i, d)
            if T_ref is None:
                T_ref = len(run_vecs)
            elif len(run_vecs) != T_ref:
                ok = False
                break
            runs.append(run_vecs)
        if not ok or T_ref is None or T_ref < 3:
            continue
        stacked = np.stack(runs, axis=0)  # (N, T, d)
        out[keys] = stacked
    return out


def analyze_experiment(cfg: Config, write_per_experiment_csv: bool = True) -> pd.DataFrame:
    """
    For each observable × (regime, family, IC) group, compute FTLE and SD from
    the inter-run ensemble spread. Returns a DataFrame with one row per group.
    """
    rows: list[dict] = []
    for obs_name in cfg.observables:
        obs_dir = cfg.embeddings_dir / obs_name
        vec_path = obs_dir / "embeddings.npy"
        meta_path = obs_dir / "metadata.parquet"
        if not vec_path.exists() or not meta_path.exists():
            log.warning("missing embeddings for observable %r; skipping", obs_name)
            continue
        vecs = load_npy(vec_path)
        meta = read_parquet(meta_path)

        ensembles = _iter_ic_ensembles(vecs, meta)
        for (regime, family, ic), runs_by_step in ensembles.items():
            T_ref = runs_by_step.shape[1]
            t_base_late = max(1, T_ref // 2)
            spec = compute_lyapunov_spectrum(runs_by_step, t_baseline=1, spectrum_size=10)
            spec_late = compute_lyapunov_spectrum(
                runs_by_step, t_baseline=t_base_late, spectrum_size=10
            )
            sd = sharpness_dimension(spec.lambda_spectrum)
            sd_late = sharpness_dimension(spec_late.lambda_spectrum)
            rows.append(
                {
                    "experiment_id": cfg.experiment_id,
                    "observable": obs_name,
                    "regime": regime,
                    "prompt_family": family,
                    "initial_condition_id": ic,
                    "n_runs": spec.n_runs,
                    "n_steps": spec.n_steps,
                    # early (transient) spectrum: biased positive by the seed
                    "lambda_1": spec.lambda_1,
                    "lambda_2": float(spec.lambda_spectrum[1]) if len(spec.lambda_spectrum) > 1 else 0.0,
                    "lambda_3": float(spec.lambda_spectrum[2]) if len(spec.lambda_spectrum) > 2 else 0.0,
                    "ftle_scalar": ftle_from_spread(spec.spread_trajectory, t_baseline=1),
                    "sharpness_dim": sd.value,
                    "j_star": sd.j_star,
                    "cumulative_lambda": sd.cumulative_sum,
                    "effective_rank_01": effective_rank(spec.lambda_spectrum, threshold=0.01),
                    # late (settled) spectrum — scientifically meaningful
                    "t_baseline_late": t_base_late,
                    "lambda_1_late": spec_late.lambda_1,
                    "lambda_2_late": float(spec_late.lambda_spectrum[1]) if len(spec_late.lambda_spectrum) > 1 else 0.0,
                    "sharpness_dim_late": sd_late.value,
                    "ftle_late": ftle_from_spread(spec_late.spread_trajectory, t_baseline=t_base_late),
                    # spread snapshots for diagnostics
                    "spread_t1": float(spec.spread_trajectory[1]) if len(spec.spread_trajectory) > 1 else 0.0,
                    "spread_mid": float(spec.spread_trajectory[t_base_late]),
                    "spread_last": float(spec.spread_trajectory[-1]) if len(spec.spread_trajectory) > 0 else 0.0,
                }
            )

    df = pd.DataFrame(rows)
    if write_per_experiment_csv and not df.empty:
        out_path = cfg.metrics_dir / "dynamics.csv"
        ensure_dir(out_path.parent)
        write_csv(out_path, df)
        log.info("wrote %d rows to %s", len(df), out_path)
    return df


def _find_all_configs(data_dir: Path) -> list[Path]:
    """Find all config.yaml snapshots under data/<exp_id>/config.yaml."""
    out: list[Path] = []
    for exp_dir in data_dir.iterdir():
        if exp_dir.is_dir():
            cfg = exp_dir / "config.yaml"
            if cfg.exists():
                out.append(cfg)
    return sorted(out)


def run_sweep(data_dir: Path, cross_csv_path: Path) -> pd.DataFrame:
    all_dfs: list[pd.DataFrame] = []
    for cfg_path in _find_all_configs(data_dir):
        try:
            cfg = load_config(cfg_path)
        except Exception as exc:
            log.warning("skipping %s (config load error: %s)", cfg_path, exc)
            continue
        log.info("analyzing %s", cfg.experiment_id)
        try:
            df = analyze_experiment(cfg, write_per_experiment_csv=True)
            if not df.empty:
                all_dfs.append(df)
        except Exception as exc:
            log.exception("failed for %s: %s", cfg.experiment_id, exc)
    if not all_dfs:
        log.warning("no experiments produced results")
        return pd.DataFrame()
    combined = pd.concat(all_dfs, ignore_index=True)
    ensure_dir(cross_csv_path.parent)
    write_csv(cross_csv_path, combined)
    log.info("wrote cross-experiment summary: %s (%d rows)", cross_csv_path, len(combined))
    return combined


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dynamics_analyze")
    parser.add_argument("--config", help="path to a single config.yaml")
    parser.add_argument(
        "--all", action="store_true", help="sweep across every data/<exp>/config.yaml"
    )
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    setup_logging(args.log_level, None)

    if args.all:
        out_path = Path(args.data_dir) / "dynamics_cross_experiment.csv"
        run_sweep(Path(args.data_dir), out_path)
        return 0
    if not args.config:
        parser.error("provide --config <path> or --all")
    cfg = load_config(args.config)
    analyze_experiment(cfg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
