"""
Partial-experiment snapshot analyzer.

Safe read of an in-flight experiment's steps.jsonl (parent process only appends,
so reading is concurrent-safe as long as we tolerate a missing last line).
Embeds the recursive-regime rolling_k3 observable, runs Lyapunov + Sharpness-
Dimension analysis per (family, IC), and writes plots to a dedicated
partial-analysis directory so we don't collide with the main analyze phase.

Usage:
    python -m src.experiments.dynamics.partial_snapshot \
        --config configs/operators/O1_pub.yaml \
        [--only-complete-trajectories]

Output: data/<experiment_id>/partial_analysis/
  ├── steps_snapshot.jsonl         (the exact rows used)
  ├── embeddings_rolling_k3.npy    (cached embeddings so reruns are free)
  ├── metadata_rolling_k3.parquet
  ├── dynamics_partial.csv         (per (family, IC) lambda_1/SD rows)
  └── plots/
       ├── regime_map_by_family.png
       └── trajectories_per_family/*.png
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

from src.api.embedder import embed_texts
from src.api.openai_client import make_client
from src.config import Config, load_config
from src.core.observables import build_all_for_run
from src.experiments.dynamics.lyapunov import compute_lyapunov_spectrum
from src.experiments.dynamics.sharpness_dim import sharpness_dimension
from src.utils.io import ensure_dir, load_npy, save_npy, write_csv, write_parquet
from src.utils.logging import get_logger, setup_logging

log = get_logger(__name__)


def snapshot_steps(src: Path, dst: Path) -> int:
    """Copy the currently visible steps.jsonl content, skipping any partial tail line."""
    with src.open("r", encoding="utf-8") as fsrc, dst.open("w", encoding="utf-8") as fdst:
        valid = 0
        for line in fsrc:
            if not line.endswith("\n"):
                break  # partial tail
            line_stripped = line.strip()
            if not line_stripped:
                continue
            try:
                json.loads(line_stripped)
            except json.JSONDecodeError:
                continue
            fdst.write(line)
            valid += 1
    return valid


def _build_rolling_k3_for_recursive(
    records: list[dict], cfg: Config, only_complete: bool
) -> tuple[list[str], pd.DataFrame]:
    """
    Group recursive-regime records by run, build rolling_k3 text per step, and
    return a flat list of strings + a metadata DataFrame.
    """
    by_run: dict[tuple, list[dict]] = defaultdict(list)
    for r in records:
        if r.get("regime") != "recursive":
            continue
        key = (r["prompt_family"], r["initial_condition_id"], r["run_id"])
        by_run[key].append(r)

    texts: list[str] = []
    rows: list[dict] = []
    T_expected = cfg.steps_per_run
    for key, steps in by_run.items():
        steps = sorted(steps, key=lambda x: x["step"])
        if only_complete and len(steps) < T_expected:
            continue
        built = build_all_for_run(
            steps,
            ["rolling_k3"],
            k=cfg.rolling_window_k,
            tail_chars=cfg.context_tail_chars,
            full_chars=cfg.context_full_chars,
        )
        k3 = built["rolling_k3"]
        for rec, t in zip(steps, k3):
            texts.append(t)
            rows.append(
                {
                    "regime": rec["regime"],
                    "prompt_family": rec["prompt_family"],
                    "initial_condition_id": rec["initial_condition_id"],
                    "run_id": rec["run_id"],
                    "step": rec["step"],
                    "text_len": len(t),
                }
            )
    return texts, pd.DataFrame(rows)


def run(cfg: Config, only_complete: bool) -> Path:
    src_path = cfg.raw_dir / "steps.jsonl"
    out_dir = cfg.experiment_dir / "partial_analysis"
    ensure_dir(out_dir)

    snapshot_path = out_dir / "steps_snapshot.jsonl"
    n_lines = snapshot_steps(src_path, snapshot_path)
    log.info("snapshot: %d lines copied from %s", n_lines, src_path)

    records: list[dict] = []
    with snapshot_path.open("r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))

    texts, meta = _build_rolling_k3_for_recursive(records, cfg, only_complete)
    if not texts:
        log.warning("no recursive-regime texts to embed (only_complete=%s)", only_complete)
        return out_dir
    log.info(
        "built %d rolling_k3 texts across %d trajectories",
        len(texts),
        len(meta.groupby(["prompt_family", "initial_condition_id", "run_id"])),
    )

    # Embed (skip if cached)
    emb_path = out_dir / "embeddings_rolling_k3.npy"
    meta_path = out_dir / "metadata_rolling_k3.parquet"
    if emb_path.exists() and meta_path.exists():
        log.info("found cached embeddings at %s; reusing", emb_path)
        vecs = load_npy(emb_path)
        meta = pd.read_parquet(meta_path)
        if len(vecs) != len(meta):
            log.warning("cache size mismatch; re-embedding")
            vecs = None
        else:
            vecs = vecs
    else:
        vecs = None
    if vecs is None or len(vecs) != len(texts):
        log.info("embedding %d texts via %s", len(texts), cfg.embedding_model)
        client = make_client()
        vecs = embed_texts(client, texts, cfg, batch_size=128)
        save_npy(emb_path, vecs)
        write_parquet(meta_path, meta)
        log.info("saved %s and %s", emb_path, meta_path)

    # Dynamics per (family, IC), averaging across runs
    rows: list[dict] = []
    group_cols = ["prompt_family", "initial_condition_id"]
    for (fam, ic), sub in meta.groupby(group_cols, dropna=False):
        runs: list[np.ndarray] = []
        T_ref = None
        ok = True
        for rid, rs in sub.groupby("run_id"):
            rs = rs.sort_values("step")
            r_vecs = vecs[rs.index.to_numpy()]
            if T_ref is None:
                T_ref = len(r_vecs)
            elif len(r_vecs) != T_ref:
                ok = False
                break
            runs.append(r_vecs)
        if not ok or T_ref is None or T_ref < 10 or len(runs) < 2:
            continue
        stack = np.stack(runs)
        t_base_late = max(1, T_ref // 2)
        spec_early = compute_lyapunov_spectrum(stack, t_baseline=1, spectrum_size=10)
        spec_late = compute_lyapunov_spectrum(stack, t_baseline=t_base_late, spectrum_size=10)
        # SD at t=T-1 = participation ratio over singular values of Σ_{T-1};
        # spec_late.singular_vals_last holds covariance eigenvalues, so sqrt
        # to recover singular values (PR is scale-invariant; the √N factor cancels).
        sigma_last = np.sqrt(np.maximum(spec_late.singular_vals_last, 0.0))
        sd_late = sharpness_dimension(sigma_last)
        rows.append(
            {
                "prompt_family": fam,
                "initial_condition_id": ic,
                "n_runs": len(runs),
                "n_steps": T_ref,
                "lambda_1_early": spec_early.lambda_1,
                "lambda_1_late": spec_late.lambda_1,
                "sharpness_dim_late": sd_late.value,
                "spread_t1": float(spec_early.spread_trajectory[1]),
                "spread_mid": float(spec_early.spread_trajectory[t_base_late]),
                "spread_last": float(spec_early.spread_trajectory[-1]),
            }
        )

    df = pd.DataFrame(rows)
    csv_path = out_dir / "dynamics_partial.csv"
    write_csv(csv_path, df)
    log.info("wrote %s (%d family×IC rows)", csv_path, len(df))

    # Plot: per-family (lambda_1_late, SD) distributions
    plot_regime_map_by_family(df, out_dir / "plots", cfg.experiment_id)

    return out_dir


def plot_regime_map_by_family(
    df: pd.DataFrame, out_dir: Path, experiment_id: str
) -> Path:
    ensure_dir(out_dir)
    if df.empty:
        log.warning("empty dynamics_partial; no plot")
        return out_dir

    families = sorted(df["prompt_family"].unique())
    fig, ax = plt.subplots(figsize=(11, 7))
    cmap = plt.get_cmap("tab20", max(1, len(families)))
    for i, fam in enumerate(families):
        sub = df[df["prompt_family"] == fam]
        color = cmap(i % cmap.N)
        ax.scatter(
            sub["lambda_1_late"],
            sub["sharpness_dim_late"],
            s=32,
            alpha=0.7,
            color=color,
            label=f"{fam}  (n={len(sub)})",
            linewidths=0.5,
            edgecolors="k",
        )
    ax.axvline(0, color="k", lw=0.5, alpha=0.5, linestyle="--")
    ax.text(0.001, ax.get_ylim()[0] + 0.05, "edge of stability →", fontsize=8, alpha=0.6)
    ax.set_xlabel(r"$\lambda_1$ (late; t_baseline = T/2)")
    ax.set_ylabel("Sharpness Dimension (late)")
    ax.set_title(
        f"Partial analysis of {experiment_id}: one point per (family, IC) "
        f"recursive trajectory\n"
        f"{len(df)} points from cached embeddings — dark = families with many ICs already done"
    )
    ax.legend(loc="best", fontsize=8, markerscale=1.5)
    ax.grid(alpha=0.2)
    path = out_dir / "regime_map_by_family.png"
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", path)
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="partial_snapshot")
    parser.add_argument("--config", required=True)
    parser.add_argument(
        "--only-complete-trajectories",
        action="store_true",
        help="skip trajectories that haven't reached steps_per_run yet",
    )
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    cfg = load_config(args.config)
    setup_logging(args.log_level, None)
    run(cfg, only_complete=args.only_complete_trajectories)
    return 0


if __name__ == "__main__":
    sys.exit(main())
