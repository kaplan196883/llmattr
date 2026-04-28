from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.basin import (
    BasinResult,
    basin_score_for_condition,
    find_target_cluster,
)
from src.analysis.basin_entry import detect_basin_entry
from src.analysis.bootstrap import bootstrap_mean_ci, permutation_test_mean_diff
from src.analysis.exit_return import exit_return_for_trajectory
from src.analysis.late_recurrence import late_recurrence_for_trajectory
from src.analysis.clustering import cluster_points
from src.analysis.dwell import dwell_stats_for_trajectory
from src.analysis.pca import fit_pca, save_pca_model, save_pca_projection
from src.analysis.recurrence import recurrence_for_trajectory
from src.analysis.tsne import fit_tsne
from src.analysis.robustness import time_shuffle_labels
from src.api.embedder import embed_texts
from src.api.openai_client import make_embedding_client, make_generation_client
from src.config import Config, PromptFamily, limit_initial_conditions, load_config, save_config_snapshot
from src.core.baselines import (
    independent_regeneration_provider,
    no_feedback_provider,
)
from src.core.observables import build_all_for_run
from src.core.trajectory import RunIds, make_jsonl_sink, run_trajectory
from src.reports.plots import (
    plot_basin_entry_histogram,
    plot_basin_scores,
    plot_cluster_occupancy,
    plot_dwell_distribution,
    plot_exit_return_scatter,
    plot_late_recurrence_distribution,
    plot_permutation_effects,
    plot_recurrence_distribution,
    plot_recurrence_vs_late,
    plot_time_colored,
    plot_trajectories_pca2,
    plot_tsne,
    plot_tsne_trajectories,
)
from src.reports.summary import (
    classify_evidence,
    classify_two_axis,
    write_report,
    write_report_v2,
)
from src.utils.io import (
    append_jsonl,
    ensure_dir,
    load_npy,
    read_json,
    read_jsonl,
    read_parquet,
    save_npy,
    write_csv,
    write_json,
    write_parquet,
)
from src.utils.logging import get_logger, setup_logging
from src.utils.seeds import set_global_seed


log = get_logger(__name__)


STEPS_FILE = "steps.jsonl"
MANIFEST_FILE = "manifest.json"


# ---------------------------- RUN (generation) -----------------------------


def cmd_run(cfg: Config) -> None:
    set_global_seed(cfg.seed)
    client = make_generation_client(cfg.generation_provider)

    ensure_dir(cfg.experiment_dir)
    save_config_snapshot(cfg, cfg.experiment_dir / "config.yaml")
    ensure_dir(cfg.raw_dir)

    steps_path = cfg.raw_dir / STEPS_FILE
    manifest_path = cfg.raw_dir / MANIFEST_FILE
    manifest = _load_manifest(manifest_path)
    _prune_uncommitted_steps(steps_path, manifest)
    sink = make_jsonl_sink(steps_path)

    planned = _plan_runs(cfg)
    log.info("planned %d trajectories", len(planned))

    for run_spec in planned:
        run_key = run_spec["run_key"]
        if manifest.get(run_key, {}).get("status") == "completed":
            log.info("skipping completed run %s", run_key)
            continue
        try:
            _execute_run(client, cfg, run_spec, sink)
            manifest[run_key] = {
                "status": "completed",
                "timestamp": time.time(),
                "steps": cfg.steps_per_run,
            }
            write_json(manifest_path, manifest)
        except Exception as exc:
            log.exception("run %s failed: %s", run_key, exc)
            manifest[run_key] = {
                "status": "failed",
                "timestamp": time.time(),
                "error": str(exc),
            }
            write_json(manifest_path, manifest)

    log.info("run phase done. steps at %s", steps_path)


def _plan_runs(cfg: Config) -> list[dict]:
    planned: list[dict] = []
    for family in cfg.prompt_families:
        ics = limit_initial_conditions(family, cfg.initial_conditions_per_family)
        for ic_idx, ic_text in enumerate(ics):
            ic_id = f"ic_{ic_idx:03d}"
            for run_idx in range(cfg.runs_per_condition):
                run_id = f"run_{run_idx:03d}"
                # main recursive regime
                planned.append(
                    {
                        "run_key": f"recursive|{family.name}|{ic_id}|{run_id}",
                        "regime": "recursive",
                        "family": family,
                        "ic_id": ic_id,
                        "ic_text": ic_text,
                        "run_id": run_id,
                    }
                )
                # baseline regimes
                for mode in cfg.baseline_modes:
                    planned.append(
                        {
                            "run_key": f"{mode}|{family.name}|{ic_id}|{run_id}",
                            "regime": mode,
                            "family": family,
                            "ic_id": ic_id,
                            "ic_text": ic_text,
                            "run_id": run_id,
                        }
                    )
    return planned


def _execute_run(client, cfg: Config, spec: dict, sink) -> None:
    family: PromptFamily = spec["family"]
    regime: str = spec["regime"]
    ids = RunIds(
        experiment_id=cfg.experiment_id,
        prompt_family=family.name,
        initial_condition_id=spec["ic_id"],
        run_id=spec["run_id"],
        regime=regime,
    )

    provider = None
    if regime == "no_feedback":
        provider = no_feedback_provider()
    elif regime == "independent_regeneration":
        provider = independent_regeneration_provider(family.system_prompt)
    elif regime == "time_shuffled":
        # time_shuffled is a post-hoc baseline over embeddings; do not regenerate.
        log.debug("skipping generation for post-hoc time_shuffled baseline")
        return
    elif regime != "recursive":
        log.warning("unknown regime '%s' -> treating as recursive", regime)

    run_trajectory(
        client,
        initial_context=spec["ic_text"],
        config=cfg,
        ids=ids,
        system_prompt=family.system_prompt,
        step_sink=sink,
        context_provider=provider,
    )


def _load_manifest(path: Path) -> dict:
    if path.exists():
        try:
            return read_json(path)
        except Exception:
            pass
    return {}


def _prune_uncommitted_steps(steps_path: Path, manifest: dict) -> None:
    """
    Before a (re)run, drop any records in steps.jsonl whose run_key is not
    marked 'completed' in the manifest. These are stray records from crashed
    or killed previous launches; leaving them in place causes duplicate-write
    issues when the worker re-runs the same trajectory.

    Safe to call when the file doesn't exist (no-op) or the manifest is empty
    (truncates the file entirely — there's nothing to keep).
    """
    if not steps_path.exists():
        return
    completed_keys = {k for k, v in manifest.items() if v.get("status") == "completed"}
    total = 0
    kept = 0
    dropped = 0
    bad = 0
    import json as _json
    tmp_path = steps_path.with_name(steps_path.name + ".prune.tmp")
    with steps_path.open("r", encoding="utf-8") as fin, tmp_path.open(
        "w", encoding="utf-8"
    ) as fout:
        for line in fin:
            stripped = line.rstrip("\n")
            if not stripped.strip():
                continue
            try:
                rec = _json.loads(stripped)
            except Exception:
                bad += 1
                continue
            total += 1
            regime = rec.get("regime")
            family = rec.get("prompt_family")
            ic = rec.get("initial_condition_id")
            run = rec.get("run_id")
            if regime is None or family is None or ic is None or run is None:
                bad += 1
                continue
            run_key = f"{regime}|{family}|{ic}|{run}"
            if run_key in completed_keys:
                fout.write(line if line.endswith("\n") else line + "\n")
                kept += 1
            else:
                dropped += 1
    if dropped > 0 or bad > 0:
        log.warning(
            "pruned steps.jsonl: kept %d, dropped %d stray, dropped %d malformed (total seen=%d)",
            kept, dropped, bad, total,
        )
    # Always replace — even a no-op rewrite verifies the file is intact.
    tmp_path.replace(steps_path)


# ---------------------------- EMBED ----------------------------------------


def cmd_embed(cfg: Config) -> None:
    client = make_embedding_client()
    steps_path = cfg.raw_dir / STEPS_FILE
    if not steps_path.exists():
        raise FileNotFoundError(f"no step log at {steps_path}; run `run` first")

    steps = list(read_jsonl(steps_path))
    log.info("loaded %d step records", len(steps))

    df = pd.DataFrame(steps)
    if df.empty:
        raise RuntimeError("no step records to embed")

    for obs_name in cfg.observables:
        _embed_observable(client, cfg, df, obs_name)

    log.info("embedding phase done")


def _embed_observable(client, cfg: Config, steps_df: pd.DataFrame, obs_name: str) -> None:
    group_cols = ["regime", "prompt_family", "initial_condition_id", "run_id"]
    steps_df = steps_df.sort_values(group_cols + ["step"]).reset_index(drop=True)

    all_texts: list[str] = []
    all_meta_rows: list[dict] = []

    for _, sub in steps_df.groupby(group_cols, dropna=False):
        sub = sub.sort_values("step")
        sub_records = sub.to_dict(orient="records")
        built = build_all_for_run(
            sub_records,
            [obs_name],
            k=cfg.rolling_window_k,
            tail_chars=cfg.context_tail_chars,
            full_chars=cfg.context_full_chars,
        )
        texts = built[obs_name]
        for rec, t in zip(sub_records, texts):
            all_texts.append(t)
            all_meta_rows.append(
                {
                    "regime": rec["regime"],
                    "prompt_family": rec["prompt_family"],
                    "initial_condition_id": rec["initial_condition_id"],
                    "run_id": rec["run_id"],
                    "step": rec["step"],
                    "text_len": len(t),
                }
            )

    log.info("embedding %d texts for observable '%s'", len(all_texts), obs_name)
    vecs = embed_texts(client, all_texts, cfg)
    if vecs.shape[0] == 0:
        log.warning("no vectors produced for observable %s", obs_name)
        return

    obs_dir = cfg.embeddings_dir / obs_name
    ensure_dir(obs_dir)
    save_npy(obs_dir / "embeddings.npy", vecs)
    meta_df = pd.DataFrame(all_meta_rows)
    write_parquet(obs_dir / "metadata.parquet", meta_df)
    log.info("wrote embeddings (%s) to %s", vecs.shape, obs_dir)


# ---------------------------- ANALYZE --------------------------------------


def cmd_analyze(cfg: Config) -> None:
    ensure_dir(cfg.metrics_dir)
    recurrence_rows: list[dict] = []
    dwell_rows: list[dict] = []
    basin_rows: list[dict] = []
    basin_entry_rows: list[dict] = []
    exit_return_rows: list[dict] = []
    late_recurrence_rows: list[dict] = []
    explained_variance: dict[str, list[float]] = {}
    # (observable, clustering_space, run_key) -> BasinEntryResult, used by late_recurrence
    basin_entry_by_run: dict[tuple, object] = {}

    for obs_name in cfg.observables:
        obs_dir = cfg.embeddings_dir / obs_name
        vec_path = obs_dir / "embeddings.npy"
        meta_path = obs_dir / "metadata.parquet"
        if not vec_path.exists() or not meta_path.exists():
            log.warning("missing embeddings for '%s'; skipping analyze", obs_name)
            continue
        vecs = load_npy(vec_path)
        meta = read_parquet(meta_path)

        # Fit PCA jointly per observable for each requested dim.
        pca_projections: dict[int, np.ndarray] = {}
        evrs: list[float] = []
        for dim in cfg.pca_dims:
            result = fit_pca(vecs, dim)
            pca_projections[result.dim] = result.projection
            save_pca_projection(result, meta, obs_name, cfg.metrics_dir)
            save_pca_model(result, obs_name, cfg.metrics_dir)
            if result.dim >= len(evrs):
                evrs = result.explained_variance_ratio.tolist()
        explained_variance[obs_name] = evrs

        # Build space lookup (raw + each PCA dim, + optional t-SNE).
        spaces: dict[str, np.ndarray] = {"raw": vecs}
        for d, proj in pca_projections.items():
            spaces[f"pca{d}"] = proj

        # t-SNE projection (visualization; optionally also used as a metric space).
        tsne_df = None
        if cfg.tsne.enabled:
            log.info("fitting t-SNE for observable '%s' (n=%d, d=%d)", obs_name, *vecs.shape)
            tsne_res = fit_tsne(
                vecs,
                perplexity=cfg.tsne.perplexity,
                random_state=cfg.seed,
                pre_pca_dim=cfg.tsne.pre_pca_dim,
                metric=cfg.tsne.metric,
            )
            if cfg.tsne.include_in_metrics:
                spaces["tsne2"] = tsne_res.projection
            # write a bare t-SNE CSV now; we'll add cluster columns per clustering space below
            tsne_df = meta.copy().reset_index(drop=True)
            tsne_df["tsne1"] = tsne_res.projection[:, 0]
            tsne_df["tsne2"] = tsne_res.projection[:, 1]

        group_cols = ["regime", "prompt_family", "initial_condition_id", "run_id"]

        # recurrence per run per space
        for space_name, pts in spaces.items():
            # pick epsilon + metric per space
            if space_name == "raw":
                eps_used = cfg.recurrence.epsilon
                metric_used = cfg.recurrence.metric  # cosine
            elif space_name == "tsne2":
                # t-SNE coordinates have arbitrary scale; use a std-relative epsilon.
                scale = float(np.mean(np.std(pts, axis=0)))
                eps_used = cfg.tsne.recurrence_epsilon_std_frac * scale
                metric_used = "euclidean"
            else:
                eps_used = cfg.recurrence.epsilon
                metric_used = "euclidean"

            shuffle_rng = np.random.default_rng(cfg.seed)
            for keys, sub in meta.groupby(group_cols, dropna=False):
                idx = sub.sort_values("step").index.to_numpy()
                sub_pts = pts[idx]
                stats = recurrence_for_trajectory(
                    sub_pts,
                    epsilon=eps_used,
                    tau=cfg.recurrence.tau,
                    metric=metric_used,
                )
                recurrence_rows.append(
                    {
                        "observable": obs_name,
                        "space": space_name,
                        "regime": keys[0],
                        "prompt_family": keys[1],
                        "initial_condition_id": keys[2],
                        "run_id": keys[3],
                        "recurrence_count": stats.recurrence_count,
                        "recurrence_rate": stats.recurrence_rate,
                        "avg_return_lag": stats.avg_return_lag,
                        "nearest_nonlocal_distance": stats.nearest_nonlocal_distance,
                        "n_points": stats.n_points,
                        "epsilon_used": eps_used,
                    }
                )

                # time_shuffled recurrence: shuffle points within the same
                # recursive trajectory, recompute. Tests whether recurrence is
                # a property of dynamics vs of the point cloud alone.
                if "time_shuffled" in cfg.baseline_modes and keys[0] == "recursive":
                    order = np.arange(len(sub_pts))
                    shuffle_rng.shuffle(order)
                    shuffled_pts = sub_pts[order]
                    ts_stats = recurrence_for_trajectory(
                        shuffled_pts,
                        epsilon=eps_used,
                        tau=cfg.recurrence.tau,
                        metric=metric_used,
                    )
                    recurrence_rows.append(
                        {
                            "observable": obs_name,
                            "space": space_name,
                            "regime": "time_shuffled",
                            "prompt_family": keys[1],
                            "initial_condition_id": keys[2],
                            "run_id": keys[3],
                            "recurrence_count": ts_stats.recurrence_count,
                            "recurrence_rate": ts_stats.recurrence_rate,
                            "avg_return_lag": ts_stats.avg_return_lag,
                            "nearest_nonlocal_distance": ts_stats.nearest_nonlocal_distance,
                            "n_points": ts_stats.n_points,
                            "epsilon_used": eps_used,
                        }
                    )

        # Decide clustering space list: always the configured target_space;
        # plus tsne2 if the user asked for it.
        cluster_spaces = [_resolve_target_space(cfg.dwell.space, spaces, obs_name)]
        if cfg.tsne.enabled and cfg.tsne.cluster_in_tsne and "tsne2" in spaces:
            cluster_spaces.append("tsne2")

        tsne_saved = False
        for space_used in cluster_spaces:
            pts_for_clustering = spaces[space_used]
            params = (
                cfg.clustering.dbscan
                if cfg.clustering.method == "dbscan"
                else cfg.clustering.kmeans
            )
            clust = cluster_points(pts_for_clustering, cfg.clustering.method, params)
            meta_with_clusters = meta.copy()
            meta_with_clusters["cluster"] = clust.labels
            meta_with_clusters["space"] = space_used
            write_csv(
                cfg.metrics_dir / f"clusters_{obs_name}_{space_used}.csv",
                meta_with_clusters,
            )

            # If this is the t-SNE clustering pass and we have a tsne_df, save the
            # merged CSV with cluster labels from this space.
            if tsne_df is not None and space_used == "tsne2" and not tsne_saved:
                td = tsne_df.copy()
                td["cluster"] = clust.labels
                td["space"] = space_used
                write_csv(cfg.metrics_dir / f"tsne_{obs_name}.csv", td)
                tsne_saved = True

            cluster_counts = (
                meta_with_clusters.groupby("cluster").size().reset_index(name="count")
            )
            write_csv(
                cfg.metrics_dir / f"cluster_occupancy_{obs_name}_{space_used}.csv",
                cluster_counts,
            )

            # dwell per run
            for keys, sub in meta_with_clusters.groupby(group_cols, dropna=False):
                sub = sub.sort_values("step")
                labels_seq = sub["cluster"].to_numpy()
                for stat in dwell_stats_for_trajectory(labels_seq):
                    dwell_rows.append(
                        {
                            "observable": obs_name,
                            "space": space_used,
                            "regime": keys[0],
                            "prompt_family": keys[1],
                            "initial_condition_id": keys[2],
                            "run_id": keys[3],
                            "cluster": stat.cluster,
                            "mean_dwell": stat.mean_dwell,
                            "median_dwell": stat.median_dwell,
                            "longest_dwell": stat.longest_dwell,
                            "reentry_count": stat.reentry_count,
                            "occupancy": stat.occupancy,
                        }
                    )

            # time-shuffled baseline over embeddings (shuffle cluster labels in time).
            if "time_shuffled" in cfg.baseline_modes:
                rng = np.random.default_rng(cfg.seed)
                for keys, sub in meta_with_clusters.groupby(group_cols, dropna=False):
                    if keys[0] != "recursive":
                        continue
                    sub = sub.sort_values("step")
                    labels_seq = sub["cluster"].to_numpy()
                    shuffled = time_shuffle_labels(labels_seq.copy(), rng)
                    for stat in dwell_stats_for_trajectory(shuffled):
                        dwell_rows.append(
                            {
                                "observable": obs_name,
                                "space": space_used,
                                "regime": "time_shuffled",
                                "prompt_family": keys[1],
                                "initial_condition_id": keys[2],
                                "run_id": keys[3],
                                "cluster": stat.cluster,
                                "mean_dwell": stat.mean_dwell,
                                "median_dwell": stat.median_dwell,
                                "longest_dwell": stat.longest_dwell,
                                "reentry_count": stat.reentry_count,
                                "occupancy": stat.occupancy,
                            }
                        )

            # basin per (prompt_family, initial_condition_id), recursive regime only
            recursive_mask = meta_with_clusters["regime"] == "recursive"
            rec_meta = meta_with_clusters[recursive_mask]
            _append_basin_rows(
                rec_meta, cfg, obs_name, space_used, basin_rows
            )

            # --- basin_entry + exit_return (per-run, gated) ---
            if cfg.basin_entry.enabled or cfg.exit_return.enabled:
                for keys, sub in meta_with_clusters.groupby(group_cols, dropna=False):
                    if keys[0] != "recursive":
                        continue
                    sub = sub.sort_values("step")
                    labels_seq = sub["cluster"].to_numpy()
                    steps_seq = sub["step"].to_numpy()
                    per_run_target = find_target_cluster(
                        labels_seq, steps_seq, cfg.basin_entry.late_fraction
                    )
                    be_res = None
                    if cfg.basin_entry.enabled:
                        be_res = detect_basin_entry(
                            labels_seq,
                            steps_seq,
                            per_run_target,
                            cfg.basin_entry.fraction_after,
                        )
                        basin_entry_rows.append(
                            {
                                "observable": obs_name,
                                "space": space_used,
                                "regime": keys[0],
                                "prompt_family": keys[1],
                                "initial_condition_id": keys[2],
                                "run_id": keys[3],
                                "target_cluster": be_res.target_cluster,
                                "entry_step": be_res.entry_step,
                                "reached": be_res.reached,
                                "late_fraction_in_target": be_res.late_fraction_in_target,
                            }
                        )
                        basin_entry_by_run[(obs_name, space_used, keys)] = be_res

                    if cfg.exit_return.enabled:
                        start = None
                        if cfg.exit_return.use_basin_entry and be_res is not None and be_res.reached:
                            start = be_res.entry_step
                        elif cfg.exit_return.start_fraction > 0:
                            start = int(round(cfg.exit_return.start_fraction * cfg.steps_per_run))
                        er = exit_return_for_trajectory(
                            labels_seq, per_run_target, steps_seq, start
                        )
                        exit_return_rows.append(
                            {
                                "observable": obs_name,
                                "space": space_used,
                                "regime": keys[0],
                                "prompt_family": keys[1],
                                "initial_condition_id": keys[2],
                                "run_id": keys[3],
                                "target_cluster": er.target_cluster,
                                "n_visits": er.n_visits,
                                "n_exits": er.n_exits,
                                "n_returns": er.n_returns,
                                "return_probability": er.return_probability,
                                "mean_time_to_return": er.mean_time_to_return,
                                "median_time_to_return": er.median_time_to_return,
                                "total_time_in_target": er.total_time_in_target,
                                "start_step": start,
                                "n_points_considered": er.n_points_considered,
                            }
                        )

        # --- late_recurrence per recursive run per space (+time_shuffled null) ---
        if cfg.late_recurrence.enabled:
            primary_cluster_space = cluster_spaces[0] if cluster_spaces else None
            for space_name, pts in spaces.items():
                if space_name == "raw":
                    eps_used = cfg.recurrence.epsilon
                    metric_used = cfg.recurrence.metric
                elif space_name == "tsne2":
                    scale = float(np.mean(np.std(pts, axis=0)))
                    eps_used = cfg.tsne.recurrence_epsilon_std_frac * scale
                    metric_used = "euclidean"
                else:
                    eps_used = cfg.recurrence.epsilon
                    metric_used = "euclidean"
                lr_rng = np.random.default_rng(cfg.seed + 17)
                for keys, sub in meta.groupby(group_cols, dropna=False):
                    idx = sub.sort_values("step").index.to_numpy()
                    sub_pts = pts[idx]
                    steps_seq = sub.sort_values("step")["step"].to_numpy()
                    start = None
                    if (
                        keys[0] == "recursive"
                        and cfg.late_recurrence.use_basin_entry
                        and cfg.basin_entry.enabled
                        and primary_cluster_space is not None
                    ):
                        be_local = basin_entry_by_run.get(
                            (obs_name, primary_cluster_space, keys)
                        )
                        if be_local is not None and getattr(be_local, "reached", False):
                            start = be_local.entry_step
                    lr_stats = late_recurrence_for_trajectory(
                        sub_pts,
                        steps=steps_seq,
                        start_step=start,
                        start_fraction=cfg.late_recurrence.start_fraction,
                        epsilon=eps_used,
                        tau=cfg.recurrence.tau,
                        metric=metric_used,
                    )
                    late_recurrence_rows.append(
                        {
                            "observable": obs_name,
                            "space": space_name,
                            "regime": keys[0],
                            "prompt_family": keys[1],
                            "initial_condition_id": keys[2],
                            "run_id": keys[3],
                            "start_step": start,
                            "recurrence_count": lr_stats.recurrence_count,
                            "recurrence_rate": lr_stats.recurrence_rate,
                            "avg_return_lag": lr_stats.avg_return_lag,
                            "nearest_nonlocal_distance": lr_stats.nearest_nonlocal_distance,
                            "n_points": lr_stats.n_points,
                            "epsilon_used": eps_used,
                        }
                    )
                    if (
                        "time_shuffled" in cfg.baseline_modes
                        and keys[0] == "recursive"
                    ):
                        order = np.arange(len(sub_pts))
                        lr_rng.shuffle(order)
                        shuffled_pts = sub_pts[order]
                        # If we anchored to entry_step, apply the same absolute start in the shuffled trajectory.
                        ts_stats = late_recurrence_for_trajectory(
                            shuffled_pts,
                            steps=steps_seq,
                            start_step=start,
                            start_fraction=cfg.late_recurrence.start_fraction,
                            epsilon=eps_used,
                            tau=cfg.recurrence.tau,
                            metric=metric_used,
                        )
                        late_recurrence_rows.append(
                            {
                                "observable": obs_name,
                                "space": space_name,
                                "regime": "time_shuffled",
                                "prompt_family": keys[1],
                                "initial_condition_id": keys[2],
                                "run_id": keys[3],
                                "start_step": start,
                                "recurrence_count": ts_stats.recurrence_count,
                                "recurrence_rate": ts_stats.recurrence_rate,
                                "avg_return_lag": ts_stats.avg_return_lag,
                                "nearest_nonlocal_distance": ts_stats.nearest_nonlocal_distance,
                                "n_points": ts_stats.n_points,
                                "epsilon_used": eps_used,
                            }
                        )

        # If t-SNE CSV wasn't saved with cluster labels above (cluster_in_tsne disabled),
        # still save the bare t-SNE CSV for plotting.
        if tsne_df is not None and not tsne_saved:
            write_csv(cfg.metrics_dir / f"tsne_{obs_name}.csv", tsne_df)

    recurrence_df = pd.DataFrame(recurrence_rows)
    dwell_df = pd.DataFrame(dwell_rows)
    basin_df = pd.DataFrame(basin_rows)

    write_csv(cfg.metrics_dir / "recurrence.csv", recurrence_df)
    write_csv(cfg.metrics_dir / "dwell.csv", dwell_df)
    write_csv(cfg.metrics_dir / "basin.csv", basin_df)

    if basin_entry_rows:
        write_csv(cfg.metrics_dir / "basin_entry_times.csv", pd.DataFrame(basin_entry_rows))
    if exit_return_rows:
        write_csv(cfg.metrics_dir / "exit_return.csv", pd.DataFrame(exit_return_rows))
    if late_recurrence_rows:
        write_csv(cfg.metrics_dir / "late_recurrence.csv", pd.DataFrame(late_recurrence_rows))

    if cfg.bootstrap.enabled:
        _write_bootstrap_summary(
            cfg,
            recurrence_df=recurrence_df,
            dwell_df=dwell_df,
            basin_df=basin_df,
            late_recurrence_df=pd.DataFrame(late_recurrence_rows),
            exit_return_df=pd.DataFrame(exit_return_rows),
        )

    ev_path = cfg.metrics_dir / "explained_variance.json"
    write_json(ev_path, explained_variance)

    # Three-axis classifier + report_operators.md (ARTICLE.md §4.5.9, §11.5).
    # Disable via `analyze_ext_enabled: false` in the YAML for quick re-runs.
    if bool(cfg.raw_dict.get("analyze_ext_enabled", True)):
        try:
            from src.experiments.operators.analyze_ext import run as _analyze_ext_run
            _analyze_ext_run(cfg)
        except Exception as exc:
            log.warning(
                "analyze_ext failed (non-fatal — main analyze succeeded): %s",
                exc,
            )

    log.info("analyze phase done. metrics in %s", cfg.metrics_dir)


def _write_bootstrap_summary(
    cfg: Config,
    recurrence_df: pd.DataFrame,
    dwell_df: pd.DataFrame,
    basin_df: pd.DataFrame,
    late_recurrence_df: pd.DataFrame,
    exit_return_df: pd.DataFrame,
) -> None:
    rows: list[dict] = []

    def _add(metric_name: str, df: pd.DataFrame, value_col: str, group_cols: list[str]) -> None:
        if df is None or df.empty or value_col not in df.columns:
            return
        for keys, sub in df.groupby(group_cols, dropna=False):
            vals = sub[value_col].to_numpy(dtype=np.float64)
            ci = bootstrap_mean_ci(
                vals,
                n_resamples=cfg.bootstrap.n_resamples,
                confidence=cfg.bootstrap.confidence,
                seed=cfg.seed,
            )
            row = {"metric": metric_name, "value_col": value_col}
            for c, v in zip(group_cols, keys if isinstance(keys, tuple) else (keys,)):
                row[c] = v
            row.update({"mean": ci.mean, "lo": ci.lo, "hi": ci.hi, "n": ci.n})
            rows.append(row)

    _add("recurrence", recurrence_df, "recurrence_rate", ["observable", "space", "regime"])
    _add("late_recurrence", late_recurrence_df, "recurrence_rate", ["observable", "space", "regime"])
    _add("dwell", dwell_df, "mean_dwell", ["observable", "space", "regime"])
    _add("basin", basin_df, "basin_score", ["observable", "space"])
    _add("exit_return", exit_return_df, "return_probability", ["observable", "space", "regime"])

    # Permutation tests: recursive vs time_shuffled for recurrence + late_recurrence + dwell
    perm_rows: list[dict] = []

    def _perm(metric_name: str, df: pd.DataFrame, value_col: str) -> None:
        if df is None or df.empty or value_col not in df.columns:
            return
        if "regime" not in df.columns:
            return
        for keys, sub in df.groupby(["observable", "space"], dropna=False):
            a = sub[sub["regime"] == "recursive"][value_col].to_numpy(dtype=np.float64)
            b = sub[sub["regime"] == "time_shuffled"][value_col].to_numpy(dtype=np.float64)
            if len(a) == 0 or len(b) == 0:
                continue
            res = permutation_test_mean_diff(a, b, n_resamples=cfg.bootstrap.n_resamples, seed=cfg.seed)
            perm_rows.append(
                {
                    "metric": metric_name,
                    "observable": keys[0],
                    "space": keys[1],
                    **res,
                }
            )

    _perm("recurrence", recurrence_df, "recurrence_rate")
    _perm("late_recurrence", late_recurrence_df, "recurrence_rate")
    _perm("dwell", dwell_df, "mean_dwell")

    if rows:
        write_csv(cfg.metrics_dir / "bootstrap_summary.csv", pd.DataFrame(rows))
    if perm_rows:
        write_csv(cfg.metrics_dir / "permutation_tests.csv", pd.DataFrame(perm_rows))


def _resolve_target_space(requested: str, spaces: dict[str, np.ndarray], obs_name: str) -> str:
    if requested in spaces:
        return requested
    log.warning(
        "target space '%s' not available for observable %s; falling back to raw",
        requested,
        obs_name,
    )
    return "raw"


def _append_basin_rows(
    rec_meta: pd.DataFrame,
    cfg: Config,
    obs_name: str,
    space_used: str,
    basin_rows: list[dict],
) -> None:
    for (fam, ic), sub in rec_meta.groupby(
        ["prompt_family", "initial_condition_id"], dropna=False
    ):
        sub = sub.sort_values(["run_id", "step"])
        labels_by_run: list[np.ndarray] = []
        steps_by_run: list[np.ndarray] = []
        for _, runsub in sub.groupby("run_id", dropna=False):
            rs = runsub.sort_values("step")
            labels_by_run.append(rs["cluster"].to_numpy())
            steps_by_run.append(rs["step"].to_numpy())
        if not labels_by_run:
            continue
        all_labels = np.concatenate(labels_by_run)
        all_steps = np.concatenate(steps_by_run)
        target_cluster = find_target_cluster(
            all_labels, all_steps, cfg.basin.target_region_late_fraction
        )
        T = cfg.steps_per_run
        target_step = int(round(cfg.basin.target_step_fraction * T))
        if target_cluster == -1:
            basin_rows.append(
                {
                    "observable": obs_name,
                    "space": space_used,
                    "prompt_family": fam,
                    "initial_condition_id": ic,
                    "target_cluster": -1,
                    "target_step": target_step,
                    "n_runs": len(labels_by_run),
                    "n_converged": 0,
                    "basin_score": 0.0,
                }
            )
            continue
        n_converged, n_runs = basin_score_for_condition(
            labels_by_run, steps_by_run, target_cluster, target_step
        )
        score = n_converged / n_runs if n_runs else 0.0
        basin_rows.append(
            {
                "observable": obs_name,
                "space": space_used,
                "prompt_family": fam,
                "initial_condition_id": ic,
                "target_cluster": int(target_cluster),
                "target_step": target_step,
                "n_runs": n_runs,
                "n_converged": n_converged,
                "basin_score": score,
            }
        )


# ---------------------------- REPORT ---------------------------------------


def cmd_report(cfg: Config) -> None:
    plots_dir = cfg.reports_dir / "plots"
    ensure_dir(plots_dir)

    recurrence_df = _try_read_csv(cfg.metrics_dir / "recurrence.csv")
    dwell_df = _try_read_csv(cfg.metrics_dir / "dwell.csv")
    basin_df = _try_read_csv(cfg.metrics_dir / "basin.csv")
    late_recurrence_df = _try_read_csv(cfg.metrics_dir / "late_recurrence.csv")
    exit_return_df = _try_read_csv(cfg.metrics_dir / "exit_return.csv")
    basin_entry_df = _try_read_csv(cfg.metrics_dir / "basin_entry_times.csv")
    permutation_df = _try_read_csv(cfg.metrics_dir / "permutation_tests.csv")
    try:
        explained_variance = read_json(cfg.metrics_dir / "explained_variance.json")
    except Exception:
        explained_variance = {}

    # plots
    for obs_name in cfg.observables:
        pca_csv = cfg.metrics_dir / f"pca_2_{obs_name}.csv"
        if pca_csv.exists():
            pca_df = pd.read_csv(pca_csv)
            plot_trajectories_pca2(pca_df, obs_name, plots_dir, color_by="run_id")
            plot_trajectories_pca2(pca_df, obs_name, plots_dir, color_by="prompt_family")
            plot_time_colored(pca_df, obs_name, plots_dir)
        tsne_csv = cfg.metrics_dir / f"tsne_{obs_name}.csv"
        if tsne_csv.exists():
            tdf = pd.read_csv(tsne_csv)
            for color_by in ("prompt_family", "regime", "cluster", "step", "run_id"):
                if color_by in tdf.columns:
                    plot_tsne(tdf, obs_name, plots_dir, color_by=color_by)
            plot_tsne_trajectories(tdf, obs_name, plots_dir, color_by="prompt_family")
            plot_tsne_trajectories(tdf, obs_name, plots_dir, color_by="regime")
        occ_csv = cfg.metrics_dir / f"cluster_occupancy_{obs_name}_{cfg.dwell.space}.csv"
        if occ_csv.exists():
            plot_cluster_occupancy(pd.read_csv(occ_csv), obs_name, plots_dir)
        if not recurrence_df.empty:
            sub = recurrence_df[recurrence_df["observable"] == obs_name]
            if not sub.empty:
                plot_recurrence_distribution(sub, obs_name, plots_dir)
        if not dwell_df.empty:
            sub = dwell_df[dwell_df["observable"] == obs_name]
            if not sub.empty:
                plot_dwell_distribution(sub, obs_name, plots_dir)
        if not basin_df.empty:
            sub = basin_df[basin_df["observable"] == obs_name]
            if not sub.empty:
                plot_basin_scores(sub, obs_name, plots_dir)

        # v2 metric plots
        if not late_recurrence_df.empty:
            sub = late_recurrence_df[late_recurrence_df["observable"] == obs_name]
            plot_late_recurrence_distribution(sub, obs_name, plots_dir, space=cfg.dwell.space)
            plot_recurrence_vs_late(
                recurrence_df[recurrence_df["observable"] == obs_name] if not recurrence_df.empty else recurrence_df,
                sub,
                obs_name,
                plots_dir,
                space=cfg.dwell.space,
            )
        if not basin_entry_df.empty:
            sub = basin_entry_df[basin_entry_df["observable"] == obs_name]
            plot_basin_entry_histogram(sub, obs_name, plots_dir, space=cfg.dwell.space)
        if not exit_return_df.empty:
            sub = exit_return_df[exit_return_df["observable"] == obs_name]
            plot_exit_return_scatter(sub, obs_name, plots_dir, space=cfg.dwell.space)

    # permutation-effects plot (one global plot, all metrics)
    if not permutation_df.empty:
        plot_permutation_effects(permutation_df, plots_dir)

    # step / trajectory counts
    steps_path = cfg.raw_dir / STEPS_FILE
    n_steps = sum(1 for _ in read_jsonl(steps_path)) if steps_path.exists() else 0
    steps_iter = read_jsonl(steps_path) if steps_path.exists() else iter(())
    traj_keys = set()
    for rec in steps_iter:
        traj_keys.add(
            (rec["regime"], rec["prompt_family"], rec["initial_condition_id"], rec["run_id"])
        )
    n_trajectories = len(traj_keys)

    decision_legacy = classify_evidence(
        recurrence_df, dwell_df, basin_df, cfg.observables, cfg.pca_dims
    )

    report_path = cfg.reports_dir / "report.md"
    has_v2_data = any(not df.empty for df in (late_recurrence_df, exit_return_df, basin_entry_df))
    if has_v2_data:
        decision_two = classify_two_axis(
            recurrence_df=recurrence_df,
            late_recurrence_df=late_recurrence_df,
            dwell_df=dwell_df,
            basin_df=basin_df,
            exit_return_df=exit_return_df,
            observables=cfg.observables,
        )
        write_report_v2(
            cfg=cfg,
            n_trajectories=n_trajectories,
            n_steps=n_steps,
            recurrence_df=recurrence_df,
            late_recurrence_df=late_recurrence_df,
            dwell_df=dwell_df,
            basin_df=basin_df,
            exit_return_df=exit_return_df,
            basin_entry_df=basin_entry_df,
            explained_variance=explained_variance,
            decision=decision_two,
            decision_legacy=decision_legacy,
            report_path=report_path,
        )
        log.info(
            "report v2 written to %s (H1a=%s, H1b=%s; legacy=%s)",
            report_path,
            decision_two.h1a_convergence,
            decision_two.h1b_recurrence,
            decision_legacy.label,
        )
    else:
        write_report(
            cfg=cfg,
            n_trajectories=n_trajectories,
            n_steps=n_steps,
            recurrence_df=recurrence_df,
            dwell_df=dwell_df,
            basin_df=basin_df,
            explained_variance=explained_variance,
            decision=decision_legacy,
            report_path=report_path,
        )
        log.info(
            "report written to %s (legacy classification=%s)",
            report_path,
            decision_legacy.label,
        )


def _try_read_csv(path: Path) -> pd.DataFrame:
    if path.exists():
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


# ---------------------------- CLI ------------------------------------------


def cmd_compare(configs: list[str], output_path: Path | None = None) -> Path:
    """
    Cross-condition summary. Reads metrics CSVs from each config's experiment_dir
    and produces condition_comparison.csv at `output_path` (default: ./data/condition_comparison.csv).
    """
    rows: list[dict] = []
    out_dir = None
    for cfg_path in configs:
        cfg = load_config(cfg_path)
        if out_dir is None:
            out_dir = Path(cfg.output_dir)
        rec = _try_read_csv(cfg.metrics_dir / "recurrence.csv")
        late = _try_read_csv(cfg.metrics_dir / "late_recurrence.csv")
        dwell = _try_read_csv(cfg.metrics_dir / "dwell.csv")
        basin = _try_read_csv(cfg.metrics_dir / "basin.csv")
        er = _try_read_csv(cfg.metrics_dir / "exit_return.csv")
        be = _try_read_csv(cfg.metrics_dir / "basin_entry_times.csv")

        summary: dict = {
            "experiment_id": cfg.experiment_id,
            "temperature": cfg.temperature,
            "max_output_tokens": cfg.max_output_tokens,
            "max_context_chars": cfg.max_context_chars,
            "steps_per_run": cfg.steps_per_run,
            "runs_per_condition": cfg.runs_per_condition,
            "initial_conditions_per_family": cfg.initial_conditions_per_family,
        }

        def _mean(df: pd.DataFrame, col: str, **filt) -> float | None:
            if df is None or df.empty or col not in df.columns:
                return None
            sub = df
            for k, v in filt.items():
                if k in sub.columns:
                    sub = sub[sub[k] == v]
            if sub.empty:
                return None
            return float(sub[col].mean())

        summary["recursive_recurrence_pca10_mean"] = _mean(
            rec, "recurrence_rate", regime="recursive", space="pca10"
        )
        summary["time_shuffled_recurrence_pca10_mean"] = _mean(
            rec, "recurrence_rate", regime="time_shuffled", space="pca10"
        )
        summary["recursive_late_recurrence_pca10_mean"] = _mean(
            late, "recurrence_rate", regime="recursive", space="pca10"
        )
        summary["time_shuffled_late_recurrence_pca10_mean"] = _mean(
            late, "recurrence_rate", regime="time_shuffled", space="pca10"
        )
        summary["recursive_dwell_pca10_mean"] = _mean(
            dwell, "mean_dwell", regime="recursive", space="pca10"
        )
        summary["time_shuffled_dwell_pca10_mean"] = _mean(
            dwell, "mean_dwell", regime="time_shuffled", space="pca10"
        )
        summary["basin_mean"] = _mean(basin, "basin_score")
        summary["return_probability_mean"] = _mean(
            er, "return_probability", regime="recursive"
        )
        summary["basin_entry_median"] = (
            float(be[be["reached"] == True]["entry_step"].median())  # noqa: E712
            if be is not None and not be.empty and "reached" in be.columns and (be["reached"] == True).any()  # noqa: E712
            else None
        )

        # Re-run the two-axis classifier from the cached CSVs so verdicts are
        # reported consistently across conditions.
        decision = classify_two_axis(
            recurrence_df=rec,
            late_recurrence_df=late,
            dwell_df=dwell,
            basin_df=basin,
            exit_return_df=er,
            observables=cfg.observables,
        )
        summary["H1a_convergence"] = decision.h1a_convergence
        summary["H1b_recurrence"] = decision.h1b_recurrence
        rows.append(summary)

    df = pd.DataFrame(rows)
    if output_path is None:
        output_path = (out_dir or Path("data")) / "condition_comparison.csv"
    write_csv(output_path, df)
    log.info("wrote cross-condition summary: %s (%d rows)", output_path, len(df))
    return output_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="llm_attractor_experiment")
    parser.add_argument(
        "command",
        choices=[
            "run",
            "embed",
            "analyze",
            "report",
            "all",
            "resume",
            "baseline",
            "compare",
        ],
    )
    parser.add_argument("--config", required=False)
    parser.add_argument("--configs", nargs="+", help="one or more configs (for `compare`)")
    parser.add_argument("--out", default=None, help="output CSV path (for `compare`)")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)

    if args.command == "compare":
        configs = args.configs or ([args.config] if args.config else [])
        if not configs:
            parser.error("compare requires --configs or --config")
        setup_logging(args.log_level, None)
        out_path = Path(args.out) if args.out else None
        cmd_compare(configs, out_path)
        return 0

    if not args.config:
        parser.error(f"--config is required for `{args.command}`")

    cfg = load_config(args.config)
    log_file = cfg.experiment_dir / "run.log"
    ensure_dir(log_file.parent)
    setup_logging(args.log_level, log_file)

    if args.command == "run":
        cmd_run(cfg)
    elif args.command == "resume":
        # resume is identical to run: _load_manifest skips completed runs.
        cmd_run(cfg)
    elif args.command == "embed":
        cmd_embed(cfg)
    elif args.command == "analyze":
        cmd_analyze(cfg)
    elif args.command == "report":
        cmd_report(cfg)
    elif args.command == "all":
        cmd_run(cfg)
        cmd_embed(cfg)
        cmd_analyze(cfg)
        cmd_report(cfg)
    elif args.command == "baseline":
        # baseline is part of `run`; this is a no-op alias for clarity.
        cmd_run(cfg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
