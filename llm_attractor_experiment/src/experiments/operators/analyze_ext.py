"""
Post-hoc extension of the analyze phase: adds periodicity + dispersion metrics
per observable × space × regime × trajectory, then runs the three-axis
classifier and writes a supplementary report.

Usage:
    python -m src.experiments.operators.analyze_ext --config configs/operators/O2_paraphrase_replace.yaml

Does not modify the main analyze pipeline. Reads cached embeddings, emits new
CSVs alongside the existing metrics, and writes report_operators.md in the
experiment's reports/ folder.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import Config, load_config
from src.experiments.operators.classifier import classify_three_axis
from src.experiments.operators.dispersion import trajectory_dispersion
from src.experiments.operators.periodicity import trajectory_periodicity
from src.utils.io import ensure_dir, load_npy, read_parquet, write_csv
from src.utils.logging import get_logger, setup_logging

log = get_logger(__name__)

GROUP_COLS = ["regime", "prompt_family", "initial_condition_id", "run_id"]


def _try_read_csv(path: Path) -> pd.DataFrame:
    if path.exists():
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def compute_periodicity_dispersion(cfg: Config) -> tuple[pd.DataFrame, pd.DataFrame]:
    periodicity_rows: list[dict] = []
    dispersion_rows: list[dict] = []

    for obs_name in cfg.observables:
        obs_dir = cfg.embeddings_dir / obs_name
        vec_path = obs_dir / "embeddings.npy"
        meta_path = obs_dir / "metadata.parquet"
        if not vec_path.exists() or not meta_path.exists():
            log.warning("missing embeddings for %s", obs_name)
            continue
        vecs = load_npy(vec_path)
        meta = read_parquet(meta_path)

        # Spaces to evaluate: raw only (periodicity/dispersion aren't PCA-specific
        # and raw embedding is the richest signal).
        space = "raw"
        for keys, sub in meta.groupby(GROUP_COLS, dropna=False):
            idx = sub.sort_values("step").index.to_numpy()
            pts = vecs[idx]
            per = trajectory_periodicity(pts, metric="cosine")
            disp = trajectory_dispersion(pts, metric="cosine")

            base = {
                "observable": obs_name,
                "space": space,
                "regime": keys[0],
                "prompt_family": keys[1],
                "initial_condition_id": keys[2],
                "run_id": keys[3],
            }
            periodicity_rows.append(
                {
                    **base,
                    "period_2_score": per.period_2_score,
                    "period_3_score": per.period_3_score,
                    "best_period": per.best_period,
                    "best_period_dist": per.best_period_dist,
                    "n_points": per.n_points,
                }
            )
            dispersion_rows.append(
                {
                    **base,
                    "initial_dispersion": disp.initial_dispersion,
                    "final_dispersion": disp.final_dispersion,
                    "dispersion_growth": disp.dispersion_growth,
                    "global_drift_start": disp.global_drift_start,
                    "global_drift_end": disp.global_drift_end,
                    "drift_monotonicity": disp.drift_monotonicity,
                }
            )

    return pd.DataFrame(periodicity_rows), pd.DataFrame(dispersion_rows)


def write_operator_report(cfg: Config, decision, periodicity_df, dispersion_df) -> Path:
    ensure_dir(cfg.reports_dir)
    lines: list[str] = []
    lines.append(f"# Operator experiment — {cfg.experiment_id}")
    lines.append("")
    lines.append(f"- loop_mode: `{cfg.raw_dict.get('loop_mode', 'append')}`")
    sp = cfg.prompt_families[0].system_prompt if cfg.prompt_families else ""
    lines.append(f"- operator: `{sp}`")
    lines.append("")
    lines.append("## Three-axis verdict")
    lines.append("")
    lines.append(f"- **H1a — convergence:  `{decision.h1a_convergence}`**")
    lines.append(f"- **H1b — recurrence:   `{decision.h1b_recurrence}`**")
    lines.append(f"- **H1c — divergence:   `{decision.h1c_divergence}`**")
    lines.append("")
    for title, sigs, reasons in (
        ("H1a signals", decision.h1a_signals, decision.h1a_reasons),
        ("H1b signals", decision.h1b_signals, decision.h1b_reasons),
        ("H1c signals", decision.h1c_signals, decision.h1c_reasons),
    ):
        lines.append(f"### {title}")
        for k, v in sigs.items():
            lines.append(f"- `{k}`: **{'yes' if v else 'no'}**")
        for r in reasons:
            lines.append(f"- {r}")
        lines.append("")

    lines.append("## Periodicity summary (recursive regime, raw space)")
    lines.append("")
    if periodicity_df is not None and not periodicity_df.empty:
        sub = periodicity_df[
            (periodicity_df["regime"] == "recursive")
            & (periodicity_df["space"] == "raw")
        ]
        if not sub.empty:
            agg = sub.groupby("observable").agg(
                period_2_score_mean=("period_2_score", "mean"),
                period_2_score_std=("period_2_score", "std"),
                best_period_median=("best_period", "median"),
                n=("period_2_score", "count"),
            ).reset_index()
            try:
                lines.append(agg.to_markdown(index=False, floatfmt=".4f"))
            except Exception:
                lines.append("```\n" + agg.to_string(index=False) + "\n```")
    lines.append("")

    lines.append("## Dispersion summary (recursive regime, raw space)")
    lines.append("")
    if dispersion_df is not None and not dispersion_df.empty:
        sub = dispersion_df[
            (dispersion_df["regime"] == "recursive")
            & (dispersion_df["space"] == "raw")
        ]
        if not sub.empty:
            agg = sub.groupby("observable").agg(
                initial_dispersion_mean=("initial_dispersion", "mean"),
                final_dispersion_mean=("final_dispersion", "mean"),
                dispersion_growth_mean=("dispersion_growth", "mean"),
                drift_monotonicity_mean=("drift_monotonicity", "mean"),
                n=("dispersion_growth", "count"),
            ).reset_index()
            try:
                lines.append(agg.to_markdown(index=False, floatfmt=".4f"))
            except Exception:
                lines.append("```\n" + agg.to_string(index=False) + "\n```")
    lines.append("")

    path = cfg.reports_dir / "report_operators.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def run(cfg: Config) -> Path:
    ensure_dir(cfg.metrics_dir)
    periodicity_df, dispersion_df = compute_periodicity_dispersion(cfg)
    if not periodicity_df.empty:
        write_csv(cfg.metrics_dir / "periodicity.csv", periodicity_df)
    if not dispersion_df.empty:
        write_csv(cfg.metrics_dir / "dispersion.csv", dispersion_df)

    recurrence_df = _try_read_csv(cfg.metrics_dir / "recurrence.csv")
    late_recurrence_df = _try_read_csv(cfg.metrics_dir / "late_recurrence.csv")
    dwell_df = _try_read_csv(cfg.metrics_dir / "dwell.csv")
    basin_df = _try_read_csv(cfg.metrics_dir / "basin.csv")

    decision = classify_three_axis(
        recurrence_df=recurrence_df,
        late_recurrence_df=late_recurrence_df,
        dwell_df=dwell_df,
        basin_df=basin_df,
        periodicity_df=periodicity_df,
        dispersion_df=dispersion_df,
        observables=cfg.observables,
    )
    report_path = write_operator_report(cfg, decision, periodicity_df, dispersion_df)
    log.info(
        "operator report %s written: H1a=%s, H1b=%s, H1c=%s",
        report_path,
        decision.h1a_convergence,
        decision.h1b_recurrence,
        decision.h1c_divergence,
    )
    return report_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="operator_analyze_ext")
    parser.add_argument("--config", required=True)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    cfg = load_config(args.config)
    ensure_dir(cfg.experiment_dir)
    setup_logging(args.log_level, cfg.experiment_dir / "run.log")
    run(cfg)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
