# EVIDENCE.md — claim-to-evidence map for ARTICLE.md

For every substantive claim in `ARTICLE.md` this file lists the **data
file** the number is read from, the **report / figure** that visualizes
it, the **source code** that produces it (file + function), and the
**CLI command** that regenerates it.

The mapping is organized by article section. Numbered findings (numeric
values, table rows, percentages) cite the exact CSV path and column
where applicable. Methodology claims cite the implementing module.

Conventions:

- `<exp>` is an experiment id under `data/<exp>/`. Each such dir has
  `raw/steps.jsonl`, `raw/manifest.json`, `embeddings/<obs>/{embeddings.npy,
  metadata.parquet}`, `metrics/*.csv`, `reports/{plots,perturbation,
  basin_predictability,report.md,report_operators.md}`, `config.yaml`,
  `run.log`. When this skeleton is referenced as **{stdpaths}** the
  intent is "all of the above".
- "obs" ∈ {`output`, `rolling_k3`, `context_tail`} (operator runs) or
  the dialog observables in §4.3.
- File line numbers are illustrative anchors at the time of writing;
  function names are stable.

---

## §1–3 — Framing and formal definitions

These sections are conceptual; the evidence is that the **formalism is
implemented** rather than measured.

| Article claim | Code |
|---|---|
| §3.1 state-generator-nudge $X_{t+1} = \mathcal{N}_f(X_t, Y_t)$, three architectures (append / replace / dialog) | `src/core/trajectory.py::run_trajectory` (single recurrence loop); branches by `cfg.loop_mode` ∈ {append, replace, dialog}; YAML `loop_mode` ↔ `nudge` aliasing in `src/config.py::load_config` |
| §3.1 context clipping (`clip_rule = "tail_chars"`) | `src/core/context.py::clip_context` (default `tail_chars`) |
| §3.2 observable maps $\mathcal{O}: \mathcal{X}_T \to \mathcal{Y}^*$ — output, rolling, context_tail, context_full | `src/core/observables.py::{observable_output, observable_rolling, observable_context_tail, observable_context_full, build_all_for_run}` |
| §3.2 dialog observables (last_user_turn, last_explorer_turn, etc.) | `src/experiments/dialog/observables.py` |
| §3.3 hypotheses H1a/H1b/H1c, H2, H3, H4 | Each tested in §5; classifier verdicts written by `src/experiments/operators/classifier.py::classify_three_axis` and `src/reports/summary.py::classify_two_axis` |

---

## §4 — Methods

### 4.1 The recurrence (the loop body)

| Claim | Evidence |
|---|---|
| Single recurrence in code | `src/core/trajectory.py::run_trajectory`; emits one `step_record` per step with `output_text`, `context_before`, `context_after`. |
| Generation API surface | `src/api/generator.py::generate_step` (Responses API, `store=False`, optional logprobs). |
| Per-step records persisted | `data/<exp>/raw/steps.jsonl` (one JSON line per step). Manifest at `data/<exp>/raw/manifest.json`. |

### 4.2 Sampling

| Claim | Evidence |
|---|---|
| Operator pub: 15 fams × 30 ICs × 3 runs × 40 steps = **1350 trajectories / regime** | `configs/operators/{O1_pub,O2_pub,O3_pub}.yaml`; planned in `src/main.py::_plan_runs`. Realized in `data/exp_pub_O1_continue/raw/steps.jsonl` etc. |
| Dialog pub: 5 fams × 30 ICs × 3 runs × 40 = **450 / regime** | `configs/dialog/D1_pub_v2.yaml`. Realized in `data/exp_pub_D1_dialog_curious_helpful_v2/`. |
| D2 exploratory: 25 trajectories at 50 steps | `configs/dialog/D2_exploratory_drilldown.yaml`. Data at `data/exp_D2_exploratory_drilldown/`. |
| Phase 1 pilots (5 fams × 5 ICs × 3 runs × 30 = 75) | `data/exp_op_{O1_continue,O2_paraphrase_replace,O3_summarize_negate,O3b_summarize_negate_replace,O4_paraphrase_append}/`, `data/exp_dialog_{D1,D2,D3}_*/`. Configs in `configs/{operators,dialog}/`. |
| T-sweep cells: 5 fams × 15 ICs × 2 runs × 30 = 150 / cell | `configs/operators/O1_Tsweep_T0{3,6,8,12}.yaml`, `configs/dialog/D1_Tsweep_T0{3,6,12}.yaml`; data in `data/exp_pub_{O1,D1}_Tsweep_T*/`. |

### 4.3 Embedding

| Claim | Evidence |
|---|---|
| `text-embedding-3-small`, single context per step | `src/api/embedder.py::embed_texts`; observable text constructed in `src/core/observables.py::build_all_for_run` and embedded in `src/main.py::_embed_observable`. |
| Embedding artifacts (n × 1536, plus parquet metadata) | `data/<exp>/embeddings/<obs>/{embeddings.npy, metadata.parquet}` per observable. |
| §4.3.5 "single context → single embedding" rule (K=3 op pub, K=8 dialog pub; +1 each with context_full) | Operator pub configs declare `observables: [output, rolling_k3, context_tail]`; dialog pub configs declare 8. Visible in each `data/<exp>/config.yaml`. |
| §4.3.4 adjacent-step similarity verification | Visible in `pca_2_*` plots and `tsne_*_by_step.png` plots under `reports/plots/`; no dedicated unit test. |

### 4.4 Representation spaces

| Claim | Evidence |
|---|---|
| Joint PCA-2 / PCA-10 / PCA-50 (no per-trajectory fits) | `src/analysis/pca.py::fit_pca`; called in `src/main.py::cmd_analyze`. Models cached at `data/<exp>/metrics/pca_{2,10,20}_{obs}_model.npz`; projections at `pca_{2,10,20}_{obs}.csv`. Explained variance at `metrics/explained_variance.json`. |
| t-SNE (perplexity 30, pre-PCA-50, cosine) | `src/analysis/tsne.py::fit_tsne`; gated by `cfg.tsne.enabled`. Output at `data/<exp>/metrics/tsne_{obs}.csv`. Pub variant: `src/experiments/dynamics/{partial_tsne.py, pub_tsne_plots_v2.py}`. |

### 4.5 Metric battery

Every metric below is written to a per-experiment CSV by
`src/main.py::cmd_analyze` (or the dynamics-extension scripts).
**Per-experiment presence** of each metric is in the corresponding
`has_*` column of `COVERAGE.csv`; under current state every applicable
cell is `1` (no missing data).

| Metric | Code | CSV (per experiment) | Plot (per experiment) |
|---|---|---|---|
| §4.5.1 Recurrence (ε=0.15 cosine, τ=3) | `src/analysis/recurrence.py::recurrence_for_trajectory`; `RecurrenceConfig` defaults in `src/config.py` | `metrics/recurrence.csv` | `reports/plots/recurrence_dist_<obs>.png` (legacy); cross-experiment in §5 aggregators |
| §4.5.2 Dwell (k-means k=12 on PCA-10) | `src/analysis/clustering.py::cluster_points` + `src/analysis/dwell.py::dwell_stats_for_trajectory` | `metrics/dwell.csv`, `metrics/clusters_<obs>_pca10.csv`, `metrics/cluster_occupancy_<obs>_pca10.csv` | `reports/plots/dwell_dist_<obs>.png`, `reports/plots/cluster_occupancy_<obs>.png` |
| §4.5.3 Basin score + entry (target = late-window majority cluster, t* = 0.7T) | `src/analysis/basin.py::{find_target_cluster, basin_score_for_condition}` + `src/analysis/basin_entry.py::detect_basin_entry`; orchestrated at `src/main.py::_append_basin_rows` (line 834+) | `metrics/basin.csv`, `metrics/basin_entry_times.csv` | `reports/plots/basin_scores_<obs>.png`, `reports/plots/basin_entry_hist_<obs>.png` |
| §4.5.4 Late recurrence + exit-return | `src/analysis/late_recurrence.py::late_recurrence_for_trajectory`, `src/analysis/exit_return.py::exit_return_for_trajectory` | `metrics/late_recurrence.csv`, `metrics/exit_return.csv` | `reports/plots/late_recurrence_dist_<obs>.png`, `reports/plots/exit_return_scatter_<obs>.png` |
| §4.5.5 Lyapunov spectrum (ensemble-spread covariance, time-divisor form) | `src/experiments/dynamics/lyapunov.py::compute_lyapunov_spectrum` (formula at line 128) | `metrics/dynamics.csv` (cols `lambda_1`, `lambda_spectrum_*`) | `data/pub_dynamics_plots/` (cross-exp); per-exp `reports/plots/dynamics_*` if rendered |
| §4.5.6 Sharpness dimension (Tuci formula, j* + cumsum/|λ_{j*+1}|) + effective rank | `src/experiments/dynamics/sharpness_dim.py::{sharpness_dimension, effective_rank}` | `metrics/dynamics.csv` (cols `sharpness_dim`, `effective_rank`) | (same as Lyapunov) |
| §4.5.7 Periodicity (`period_2_score`, `best_period`) | `src/experiments/operators/periodicity.py` | `metrics/periodicity.csv` | renderer in `src/experiments/dynamics/regime_plots.py` |
| §4.5.8 Dispersion (`dispersion_growth`, `drift_monotonicity`) | `src/experiments/operators/dispersion.py` | `metrics/dispersion.csv` | (overlay in dynamics plots) |
| §4.5.9 Three-axis classifier (H1a/H1b/H1c) | `src/experiments/operators/classifier.py::classify_three_axis`; runner `src/experiments/operators/analyze_ext.py::run` (auto-fired by `cmd_analyze` unless `analyze_ext_enabled: false`) | embedded in `reports/report_operators.md` | `reports/report_operators.md` |
| §4.5.7 (numbering in source) Basin predictability (5-fold CV multinomial logistic, PCA-10, t* = 0.7T late window) | `src/experiments/dynamics/basin_predictability.py` | `reports/basin_predictability/basin_predictability.csv`, `…_summary.json` | `reports/basin_predictability/basin_predictability_<exp>.png` |
| §4.5.8 Perturbation switching rate + Wilson 95% CI | `src/experiments/perturbation/analyze.py`; CI from `src/analysis/bootstrap.py::wilson_ci` | `reports/perturbation/switching_summary.csv` | `reports/perturbation/switching_rates.png`, `relaxation_curves.png`, `relaxation_table.csv` |
| Bootstrap + permutation tests (resamples per `cfg.bootstrap`) | `src/analysis/bootstrap.py::{bootstrap_mean_ci, permutation_test_mean_diff}`; orchestrated at `src/main.py::_write_bootstrap_summary` | `metrics/bootstrap_summary.csv`, `metrics/permutation_tests.csv` | `reports/plots/permutation_effects.png` |

### 4.6 Baselines

| Article claim | Code |
|---|---|
| Three baselines: `no_feedback`, `time_shuffled`, `independent_regeneration` | `src/core/baselines.py::{no_feedback_provider, independent_regeneration_provider}`; `time_shuffled` is post-hoc — applied in `src/main.py::cmd_analyze` (recurrence + dwell shuffles) |
| Dialog uses `time_shuffled` only | Dialog configs declare `baseline_modes: [time_shuffled]`; operator pub configs declare all three. |

### 4.7 Statistical procedures

| Article claim | Code |
|---|---|
| Wilson 95% score CI for proportions | `src/analysis/bootstrap.py::wilson_ci` (`WilsonCI` dataclass, Winitzki erfinv approximation) |
| Bootstrap 95% CI for means | `src/analysis/bootstrap.py::bootstrap_mean_ci` |
| Permutation test (recursive vs time_shuffled) | `src/analysis/bootstrap.py::permutation_test_mean_diff` → `metrics/permutation_tests.csv` |

### 4.8 Static visualization battery (per-experiment)

| Article plot label | Output PNG | Code |
|---|---|---|
| Plot A: joint t-SNE coloring panel | `reports/plots/A_joint_tsne_by_{regime,family,step}_<obs>.png` (legacy), `A_v2_joint_by_{regime,family,step,parity}_<obs>.png` (v2) | legacy: `src/experiments/dynamics/regime_plots.py::plot_joint_tsne` (line 82); v2: `src/experiments/dynamics/pub_tsne_plots_v2.py::{plot_v2_by_family, plot_v2_by_step, plot_v2_by_regime, plot_v2_by_step_parity}` (lines 58, 91, 117, 162). Per-step t-SNE prep in `src/experiments/dynamics/partial_tsne.py`. |
| Plot B: per-family trajectory grid | per-exp `reports/plots/B_v2_per_family_grid_<obs>.png`, `B_v2_per_family_parity_<obs>.png`; cross-exp `data/pub_dynamics_plots/B_trajectory_grid_rolling_k3.png` | cross-exp: `regime_plots.py::plot_trajectory_grid` (line 194); per-exp v2: `pub_tsne_plots_v2.py::{plot_v2_per_family_grid (206), plot_v2_per_family_parity_grid (290)}` |
| Plot C: ensemble-spread timelines | per-exp legacy `reports/plots/C_v2_single_ic_trajectories_<obs>.png`; cross-exp `data/pub_dynamics_plots/C_spread_timeline_<obs>.png` | per-exp legacy: `pub_tsne_plots_v2.py::plot_v2_single_ic_trajectories` (line 376); cross-exp ensemble-spread: `regime_plots.py::plot_spread_timelines` (line 341) |
| Plot E: flow field (PCA + t-SNE) | per-exp `reports/plots/E_flow_field_<obs>.png` (no longer emitted in current pipeline — legacy from earlier reports); cross-exp `data/pub_dynamics_plots/E_flow_<exp>_<obs>.png`, `…/E_tsne_flow_<exp>_<obs>.png`, `…/E_flow_fields_<obs>.png` (grid), `…/E_tsne_flow_fields_<obs>.png` (grid) | `regime_plots.py::{plot_flow_field_single (766), plot_flow_field_grid (822), plot_flow_field_tsne_single (530), plot_flow_field_tsne_grid (587)}` — drawing primitives in `src/experiments/dynamics/field_plots.py::{plot_streamlines_density, plot_speed_colored_streamlines, plot_divergence_field}` (lines 119, 180, 240) |
| Plot F: t-SNE trajectory sample | `reports/plots/F_trajectory_sample_<obs>.png`, `data/pub_dynamics_plots/F_tsne_trajectories_<exp>_<obs>.png` | `regime_plots.py::plot_tsne_trajectories_single` (line 650) |
| Basin / dwell / occupancy / recurrence histograms | `reports/plots/{basin_scores,basin_entry_hist,dwell_dist,cluster_occupancy,exit_return_scatter,late_recurrence_dist,recurrence_dist,recurrence_vs_late,permutation_effects,pca2_*,pca2_timecolor_*,tsne_*}_<obs>.png` | `src/reports/plots.py` (orchestrated by `src/main.py::cmd_report`) |

### 4.9 Flow-field computation (G/H/I triple)

| Plot | Output | Code |
|---|---|---|
| G: streamlines + density (per condition) | `reports/perturbation/G_streamlines_density_by_condition_{pca,tsne}.png` (line 233) | `src/experiments/perturbation/field_plots.py::_plot_panel_streamlines_density` (line 89), driven by public entry `render_fields_for_pilot` (167) → `_render_all_three` (201) |
| H: speed streamlines | `reports/perturbation/H_speed_streamlines_by_condition_{pca,tsne}.png` (line 259) | `src/experiments/perturbation/field_plots.py::_plot_panel_speed_streamlines` (line 113), same orchestrator |
| I: divergence | `reports/perturbation/I_divergence_by_condition_{pca,tsne}.png` (line 299) | `src/experiments/perturbation/field_plots.py::_plot_panel_divergence` (line 137), same orchestrator |

### 4.10 Perturbation visualization toolkit

| Article element | Output | Code |
|---|---|---|
| §4.10 Effective potential V(x) = −log ρ(x) (KDE) | `reports/perturbation/bulk_landscape_pca.png` | `src/experiments/perturbation/bulk_plots.py` |
| §4.10 Geodesic skeleton (Dijkstra over V grid + basin centers from local minima) | `reports/perturbation/geodesic_skeleton_pca.png` | `src/experiments/perturbation/geodesic_skeleton.py` |
| §4.10 Volumetric bulk (marching-cubes iso-density at fractions 0.04, 0.10, 0.20, 0.35, 0.55) + N-trajectory walk through cloud + red kick beams at perturbation step | Per-perturbation-pilot (4 conds × 4 pilots, N=50): `data/exp_perturb_{O1,O2,O3,D1}_pilot/reports/perturbation/animation3d_{control,neutral,lorem,adversarial}_n50_seed0.mp4`. Pub experiments (no perturbation, N=50): `data/exp_pub_{O1_continue,O2_paraphrase_replace,O3_summarize_negate_replace,D1_dialog_curious_helpful_v2}/reports/perturbation/animation3d_recursive_n50_seed0.mp4`. D2 (N=25): `data/exp_perturb_D2_exploratory/reports/perturbation/animation3d_{control,adversarial}_n25_seed0.mp4`. ~22 mp4 files, ~320 MB total. | `src/experiments/perturbation/trajectory_animation_3d.py` — shell fractions at line ~50 (`levels_frac=(0.04, 0.10, 0.20, 0.35, 0.55)`); parallel path emits `.mp4` via `imageio + libx264` (lines 279–286), sequential / single-trajectory path emits `.gif` via PillowWriter (line 561). Driven by `--condition` and `--parallel N` flags. |
| §4.10 Parallel rendering across 40 cores | `--parallel 40` flag handled in `trajectory_animation_3d.py::main` |
| §5.10 Hierarchical RG dendrogram (K=48 KMeans + Ward linkage on PCA-30) | `reports/perturbation/rg_dendrogram_pca.png`; cluster CSV at `reports/perturbation/joint_pca10_clusters.csv` | `src/experiments/perturbation/rg_dendrogram.py` (`N_LEAVES = 48` at line 50) |
| Flow skeleton (PCA only) | `reports/perturbation/flow_skeleton_pca.png` | `src/experiments/perturbation/flow_skeleton.py` |
| RG stack (per-scale clouds) | `reports/perturbation/rg_stack_pca.png` | `src/experiments/perturbation/bulk_plots.py` |

### 4.11 End-to-end pipeline diagram

| Article claim | Evidence |
|---|---|
| Persistence boundaries (raw → embeddings → metrics → reports) | Directory layout in every `data/<exp>/`; producers in `src/main.py::cmd_{run,embed,analyze,report}` |
| §4.11.6 K=48 dendrogram annotation | `src/experiments/perturbation/rg_dendrogram.py:50` (`N_LEAVES = 48`) |
| Shape annotations through the pipeline (T=40, n=1536, PCA-10, k=12, …) | Exact shape verified at runtime by `src/main.py::cmd_embed` log lines and recorded in `run.log`. |

### 4.12 Hardware and software

| Claim | Evidence |
|---|---|
| Python deps | `requirements.txt` |
| 94 pytest tests | `tests/` (run with `PYTHONPATH=. python -m pytest tests/ -q`) |

---

## §5 — Results

For each phase, the **canonical data dirs** below contain the
`{stdpaths}` skeleton (raw / embeddings / metrics / reports). When a
specific number from the article is cited, the column and CSV are
named. **Per-experiment artifact presence is in `COVERAGE.csv`** —
each phase below has 100% of its applicable artifacts populated.

### 5.0 Master comparison table (regimes at a glance)

Every cell of the §5.0 table is computed from one of:

| Column | Source CSV (per `<exp>`) | Aggregated source |
|---|---|---|
| basin pred. acc(k=5→final) | `reports/basin_predictability/basin_predictability.csv` | `data/aggregated/basin_predictability_cross/cross_basin_predictability.csv` |
| recurrence | `metrics/recurrence.csv` (col `recurrence_rate`, `space=pca10`) | `data/dynamics_cross_experiment.csv` |
| sharpness dim | `metrics/dynamics.csv` (col `sharpness_dim`) | `data/dynamics_cross_experiment.csv` |
| adversarial switch | `reports/perturbation/switching_summary.csv` | `data/aggregated/perturbation_cross_regime/` |
| dose 50% | dose CSVs in `data/exp_perturb_*_dose*/reports/perturbation/switching_summary.csv` | `data/aggregated/perturbation_dose_response/` |
| T-stability | T-sweep dirs `data/exp_pub_{O1,D1}_Tsweep_T*/reports/basin_predictability/` | `data/aggregated/t_sensitivity_cross_regime/`, `…/t_sweep_basin_predictability/` |

### 5.1 Phase 0 — pilot validation

| Article cite | Data | Report | Code |
|---|---|---|---|
| `exp_default` first run, T=0.8, append+continue, 75 trajectories | `data/exp_default/{stdpaths}` | `data/exp_default/reports/{report.md, report_operators.md, plots/, basin_predictability/}` | Pipeline as in §4 |
| `exp_long` 60-step horizon | `data/exp_long/{stdpaths}` | `data/exp_long/reports/` | same |
| `exp_noclip` no-context-clipping ablation | `data/exp_noclip/{stdpaths}` | `data/exp_noclip/reports/` | same; config sets `clip_rule: none` (see config.yaml) |
| Discovery narrative | — | `docs/reports/REPORT1.md`, `REPORT2.md` | — |

### 5.2 Phase 1 — four-regime taxonomy at small N

The 8-row table at §5.2 maps row-by-row to:

| Article row (regime) | Data dir | Report | Generation config |
|---|---|---|---|
| O1 contractive | `data/exp_op_O1_continue/` | `reports/{report_operators.md, plots/}` | `configs/operators/O1_continue.yaml` |
| O2 oscillatory replace | `data/exp_op_O2_paraphrase_replace/` | `reports/…` | `configs/operators/O2_paraphrase_replace.yaml` |
| O3 absorbing append (weak) | `data/exp_op_O3_summarize_negate/` | `reports/…` | `configs/operators/O3_summarize_negate.yaml` |
| O3b absorbing replace (sharp) | `data/exp_op_O3b_summarize_negate_replace/` | `reports/…` | `configs/operators/O3b_summarize_negate_replace.yaml` |
| O4 paraphrase append | `data/exp_op_O4_paraphrase_append/` | `reports/…` | `configs/operators/O4_paraphrase_append.yaml` |
| D1 multi-basin curious+helpful | `data/exp_dialog_D1_curious_helpful/` | `reports/…` | `configs/dialog/D1_curious_helpful.yaml` |
| D2 replace-mode dialog | `data/exp_dialog_D2_replace_curious_helpful/` | `reports/…` | `configs/dialog/D2_replace_curious_helpful.yaml` |
| D3 advocate+skeptic | `data/exp_dialog_D3_debate_advocate_skeptic/` | `reports/…` | `configs/dialog/D3_debate_advocate_skeptic.yaml` |
| Stage report | — | `docs/reports/REPORT3.md`, `REPORT4.md` | — |

Per-row "basin score / recurrence / sharpness dim" verdicts come from
each row's `metrics/{basin,recurrence,dynamics}.csv` and the
three-axis verdict in `reports/report_operators.md`.

### 5.3 Phase 2 — publication-scale verification

The four-row §5.3 table is the canonical pub claim. Each row maps
strictly:

| Article row | Data | Report figure |
|---|---|---|
| `exp_pub_O1_continue` (1350 traj) | `data/exp_pub_O1_continue/{stdpaths}` | `reports/basin_predictability/basin_predictability_exp_pub_O1_continue.png`, `reports/plots/*` |
| `exp_pub_O2_paraphrase_replace` | `data/exp_pub_O2_paraphrase_replace/` | same skeleton |
| `exp_pub_O3_summarize_negate_replace` | `data/exp_pub_O3_summarize_negate_replace/` | same skeleton |
| `exp_pub_D1_dialog_curious_helpful_v2` (450 traj) | `data/exp_pub_D1_dialog_curious_helpful_v2/` | same skeleton |

The "Numbers measured from
`data/aggregated/basin_predictability_cross/cross_basin_predictability.csv`,
recursive regime only, canonical observable per regime" line at
ARTICLE.md:1448–1449 is **literally the file that produced the table** — that
CSV is generated by `scripts/aggregate_basin_predictability.py`.

Stage report: `docs/reports/REPORT5.md`.

### 5.4 Phase 2b — temperature sensitivity

The two T-sweep tables (O1 and D1, T ∈ {0.3, 0.6, 0.8, 1.2}) are
assembled from per-cell experiments:

| Cell | Data dir | Config |
|---|---|---|
| O1 T=0.3 | `data/exp_pub_O1_Tsweep_T03/` | `configs/operators/O1_Tsweep_T03.yaml` |
| O1 T=0.6 | `data/exp_pub_O1_Tsweep_T06/` | `…T06.yaml` |
| O1 T=0.8 | `data/exp_pub_O1_Tsweep_T08/` (or `exp_pub_O1_continue` reused as 0.8 cell) | `…T08.yaml` |
| O1 T=1.2 | `data/exp_pub_O1_Tsweep_T12/` | `…T12.yaml` |
| D1 T=0.3 | `data/exp_pub_D1_Tsweep_T03/` | `configs/dialog/D1_Tsweep_T03.yaml` |
| D1 T=0.6 | `data/exp_pub_D1_Tsweep_T06/` | `…T06.yaml` |
| D1 T=0.8 | `data/exp_pub_D1_dialog_curious_helpful_v2/` (reused as 0.8 cell) | `D1_pub_v2.yaml` |
| D1 T=1.2 | `data/exp_pub_D1_Tsweep_T12/` | `…T12.yaml` |

Aggregated: `data/aggregated/t_sweep_basin_predictability/` and
`data/aggregated/t_sensitivity_cross_regime/`. Built by
`scripts/aggregate_t_sweep.py` and `scripts/aggregate_o1_d1_t_sensitivity.py`.

### 5.5 Phase 3a — perturbation pilots

The 5-row §5.5 switching table maps to:

| Article regime | Data dir | Report | Config |
|---|---|---|---|
| O1 perturb pilot | `data/exp_perturb_O1_pilot/` | `reports/perturbation/{switching_rates.png, switching_summary.csv, relaxation_curves.png, relaxation_table.csv}` | `configs/perturbation/O1_pilot.yaml` |
| O2 perturb pilot | `data/exp_perturb_O2_pilot/` | same | `configs/perturbation/O2_pilot.yaml` |
| O3 perturb pilot | `data/exp_perturb_O3_pilot/` | same | `configs/perturbation/O3_pilot.yaml` |
| D1 perturb pilot | `data/exp_perturb_D1_pilot/` | same | `configs/perturbation/D1_pilot.yaml` |
| D2 perturb (control + adversarial only) | `data/exp_perturb_D2_exploratory/` | `reports/perturbation/` | `configs/perturbation/D2_exploratory_perturb.yaml` |

Numbers (switch %, Wilson CI) live in `switching_summary.csv` per
experiment. Cross-regime aggregation:
`data/aggregated/perturbation_cross_regime/` (4×5 grouped bar) by
`scripts/aggregate_perturbation_cross_regime.py`.

Wilson CI computation: `src/analysis/bootstrap.py::wilson_ci`.

Perturbation conditions (control / neutral / lorem / adversarial)
are defined in `src/experiments/perturbation/corpora.py`:

- `control` — no injection
- `neutral` — `corpora.NEUTRAL_WIKI` (8 hand-written paragraphs); pilot
  sends the full paragraph (`approx_tokens=None`)
- `lorem` — `corpora.random_words` over `corpora._WORD_POOL` (90-word
  hand-curated pool), default `n_words=70`
- `adversarial` — `corpora.sample_adversarial_text` pulls late-step
  output from a *different* (family, IC) trajectory

Perturbation runner: `src/experiments/perturbation/main.py` (config,
`_resolve_perturbation_text`); harnesses
`src/experiments/perturbation/{runner.py, runner_op.py}`. Switching
analysis: `src/experiments/perturbation/analyze.py`.

Stage report: `docs/reports/REPORT6.md`.

### 5.6 Phase 3b — dose-response

Per-cell experiments:

| Cell | Data dir | Config |
|---|---|---|
| D1 / neutral / dose ∈ {20, 80, 200, 400} | `data/exp_perturb_D1_dose/` | `configs/perturbation/D1_dose.yaml` |
| D1 / neutral / dose ∈ {5, 10, 15} | `data/exp_perturb_D1_dose_fine/` | `configs/perturbation/D1_dose_fine.yaml` |
| O1 / neutral / dose ∈ {20, 80, 200, 400} | `data/exp_perturb_O1_dose/` | `configs/perturbation/O1_dose.yaml` |
| O1 / adversarial / dose ∈ {20, 80, 200, 400} | `data/exp_perturb_O1_dose_adversarial/` | `configs/perturbation/O1_dose_adversarial.yaml` |

Aggregated: `data/aggregated/perturbation_dose_response/` (log-scale
dose × switch with Wilson CI bars). Built by
`scripts/aggregate_dose_response.py`. The "150 tokens of in-distribution
text" 50% switching dose is read off the curve in this aggregated
output.

### 5.7 Phase 3c — injection-time sweep

Per-cell experiments:

| Cell | Data dir | Config |
|---|---|---|
| D1 / neutral @80 / inject step 5 | `data/exp_perturb_D1_inject_t5/` | `configs/perturbation/D1_inject_t5.yaml` |
| D1 / neutral @80 / inject step 25 | `data/exp_perturb_D1_inject_t25/` | `configs/perturbation/D1_inject_t25.yaml` |
| O1 / adversarial @200 / inject step 5 | `data/exp_perturb_O1_inject_t5/` | `configs/perturbation/O1_inject_t5.yaml` |
| O1 / adversarial @200 / inject step 25 | `data/exp_perturb_O1_inject_t25/` | `configs/perturbation/O1_inject_t25.yaml` |
| (step 15 cell = pilot's default inject step) | reuse pilot dirs | pilot configs |

Aggregated: `data/aggregated/perturbation_basin_hardening/` by
`scripts/aggregate_basin_hardening.py`.

### 5.8 Phase 3d — drill-down dialog (D2)

| Element | Data | Code |
|---|---|---|
| 25 trajectories at 50 steps; 5 topic families × 5 seeds | `data/exp_D2_exploratory_drilldown/` | `configs/dialog/D2_exploratory_drilldown.yaml` |
| Adversarial perturbation at step 25, 25 steps relaxation, 64% switch | `data/exp_perturb_D2_exploratory/reports/perturbation/switching_summary.csv` | `configs/perturbation/D2_exploratory_perturb.yaml` |
| Matched D1-vs-D2 comparison | Aggregated within `data/aggregated/perturbation_basin_hardening/` (D1 inject_t25 cell) | `scripts/aggregate_basin_hardening.py` |

### 5.9 Cross-experiment aggregation (six aggregator scripts)

The article enumerates the six scripts; each is one-to-one with an
output directory:

| Script | Output |
|---|---|
| `scripts/aggregate_basin_predictability.py` | `data/aggregated/basin_predictability_cross/` |
| `scripts/aggregate_t_sweep.py` | `data/aggregated/t_sweep_basin_predictability/` |
| `scripts/aggregate_o1_d1_t_sensitivity.py` | `data/aggregated/t_sensitivity_cross_regime/` |
| `scripts/aggregate_perturbation_cross_regime.py` | `data/aggregated/perturbation_cross_regime/` |
| `scripts/aggregate_dose_response.py` | `data/aggregated/perturbation_dose_response/` |
| `scripts/aggregate_basin_hardening.py` | `data/aggregated/perturbation_basin_hardening/` |
| `scripts/aggregate_perturbation_geometric_barriers.py` | `data/aggregated/perturbation_geometric_barriers/` (`v_star_table.csv`, `rg_merge_table.csv`, `geometric_barriers_long.csv`) — sourced from the per-pilot `geodesic_barriers_summary.csv` and `rg_dendrogram_summary.csv` written by §5.10 scripts |

Deterministic — re-running produces byte-identical output.

The cross-experiment dynamics CSV (`data/dynamics_cross_experiment.csv`)
combines per-experiment `metrics/dynamics.csv` rows for the §5.0 master
table; assembled by `src/experiments/dynamics/analyze.py` /
`scripts/render_per_exp_plots.py`.

### 5.10 Geometric barriers V(x) = −log ρ(x)

#### Geodesic skeleton table (V*) — values at ARTICLE.md:1655–1658

Per-condition V* values are read from the per-perturbation-pilot
output:

| Source | File |
|---|---|
| O1 V* | `data/exp_perturb_O1_pilot/reports/perturbation/geodesic_skeleton_pca.png` (V* annotated on geodesics; numeric values tracked in `joint_pca10_clusters.csv` companion) |
| O2 V* | `data/exp_perturb_O2_pilot/reports/perturbation/geodesic_skeleton_pca.png` |
| O3 V* | `data/exp_perturb_O3_pilot/reports/perturbation/geodesic_skeleton_pca.png` |
| D1 V* | `data/exp_perturb_D1_pilot/reports/perturbation/geodesic_skeleton_pca.png` |

Code: `src/experiments/perturbation/geodesic_skeleton.py`
(`V(x) = −log ρ(x)` from KDE; basin centers at local minima of V;
Dijkstra over the V grid).

#### RG dendrogram table — values at ARTICLE.md:1684–1689 (k=48)

| Article row | File |
|---|---|
| O1 / O2 / O3 | `data/exp_perturb_{O1,O2,O3}_pilot/reports/perturbation/rg_dendrogram_pca.png` |
| D1 | `data/exp_perturb_D1_pilot/reports/perturbation/rg_dendrogram_pca.png` |

Code: `src/experiments/perturbation/rg_dendrogram.py` (`N_LEAVES = 48`,
`PRE_PCA = 30`, Ward linkage on K-means centroids).

---

## §6–8 — Discussion / limitations / future work

These sections interpret §5; cross-references resolve back to the
same data dirs already listed.

| Article element | Pointer |
|---|---|
| §6.1 architecture × content interaction | Read off the §5.0 master table (data sources above) |
| §6.4 holographic-bulk picture (V landscape, geodesics, marching-cubes shells) | All artifacts in `data/exp_perturb_*_pilot/reports/perturbation/` |
| §7.x limitations | No new evidence; cross-references to method sections |
| §8 future work | Open items — no implementation yet |

---

## §9 — Methods appendix

### 9.1 Exact metric definitions (executable form)

The article reproduces the canonical NumPy implementations of
recurrence, dwell, basin, late_recurrence, exit_return, Lyapunov, and
sharpness dimension. Each is the **same code** as the production
modules (or a thin wrapper):

| Article snippet | Implementation |
|---|---|
| recurrence | `src/analysis/recurrence.py::recurrence_for_trajectory` |
| dwell | `src/analysis/dwell.py::dwell_stats_for_trajectory` |
| basin | `src/analysis/basin.py::{find_target_cluster, basin_score_for_condition}` |
| basin_entry | `src/analysis/basin_entry.py::detect_basin_entry` |
| late_recurrence | `src/analysis/late_recurrence.py::late_recurrence_for_trajectory` |
| exit_return | `src/analysis/exit_return.py::exit_return_for_trajectory` |
| Lyapunov | `src/experiments/dynamics/lyapunov.py::compute_lyapunov_spectrum` |
| sharpness_dim | `src/experiments/dynamics/sharpness_dim.py::sharpness_dimension` |

### 9.2 Perturbation injection mechanics

| Article claim | Code |
|---|---|
| Injection at step k via context modification | `src/experiments/perturbation/main.py::_resolve_perturbation_text` (lines ~92–130) |
| Condition library (control / neutral / lorem / adversarial) | `src/experiments/perturbation/corpora.py` |

### 9.3 K-means choice and stability

| Claim | Code |
|---|---|
| K=12 default | `configs/operators/*_pub.yaml` (and dialog pub) `clustering.kmeans.n_clusters: 12` |
| K=48 for RG dendrogram | `src/experiments/perturbation/rg_dendrogram.py:50` |
| Stability over seeds | `src/analysis/clustering.py::cluster_points` (n_init=8) |

### 9.4 PCA stability

`src/analysis/pca.py::fit_pca` saves the model
(`pca_{dim}_{obs}_model.npz`) so projection is reproducible from cached
embeddings.

### 9.5 Animation rendering pipeline

`src/experiments/perturbation/trajectory_animation_3d.py` — marching
cubes via `skimage.measure.marching_cubes`; iso fractions
`(0.04, 0.10, 0.20, 0.35, 0.55)` at line ~50; `--parallel 40` ffmpeg
through `imageio-ffmpeg`.

---

## §10 — Reproducibility

### 10.4 Pipeline commands — exact CLI

Every command in §10.4 is implemented:

| Command | Entry point |
|---|---|
| `python -m src.experiments.dialog.main run` | `src/experiments/dialog/main.py::main` |
| `python -m src.experiments.operators.main run` | `src/experiments/operators/main.py::main` |
| `python -m src.experiments.perturbation.main run` | `src/experiments/perturbation/main.py::main` |
| `python -m src.experiments.dynamics.basin_predictability` | `src/experiments/dynamics/basin_predictability.py::main` |
| `python -m src.experiments.dynamics.regime_plots` | `src/experiments/dynamics/regime_plots.py::main` |
| `python -m src.experiments.perturbation.flow_skeleton` | `src/experiments/perturbation/flow_skeleton.py::main` |
| `python -m src.experiments.perturbation.geodesic_skeleton` | `src/experiments/perturbation/geodesic_skeleton.py::main` |
| `python -m src.experiments.perturbation.bulk_plots` | `src/experiments/perturbation/bulk_plots.py::main` |
| `python -m src.experiments.perturbation.rg_dendrogram` | `src/experiments/perturbation/rg_dendrogram.py::main` |
| `python -m src.experiments.perturbation.trajectory_animation_3d` | `src/experiments/perturbation/trajectory_animation_3d.py::main` |
| `python -m scripts.aggregate_*` | `scripts/aggregate_*.py` (six scripts) |

### 10.5 Per-experiment catalog

Two complementary catalogs:

- **`docs/DATA_INDEX.md`** — narrative catalog of the 37 experiments
  organized by phase, with descriptions of each experiment's purpose,
  scope, and supersession relationships.
- **`COVERAGE.csv`** — machine-readable matrix (37 rows × 60 cols)
  showing which analytical artifacts every experiment carries, plus
  metadata (phase, regime, nudge_mode, temperature, n_trajectories)
  and three summary columns (`n_applicable_artifacts`,
  `n_present_artifacts`, `coverage_pct`). All 37 experiments are at
  100% of their applicable artifacts. See "Coverage matrix" section
  below for cell semantics + applicability rules. Regenerate with
  `python -m scripts.build_coverage`.

Each row in either resolves to a `data/<exp>/` dir documented above.

### 10.6 Stage reports

`docs/reports/REPORT1.md` … `REPORT6.md` — the discovery narrative
that produced the article's regime taxonomy. Each report cites the
specific experiments it analyzed; cross-reference back to §5 phases.

### 10.7 Test coverage

```bash
PYTHONPATH=. python -m pytest tests/ -q
# 94 passed in ~12s
```

Key test files: `tests/test_dynamics.py` (Lyapunov + sharpness),
`tests/test_recurrence.py`, `tests/test_basin*.py`, `tests/test_perturbation*.py`.

---

## §11 — Coverage of original specification

§11 already maps requirements (req1.txt, req2.txt, reg4.txt) to
implementation files; it is itself an evidence map at the
specification level. No additional pointers needed here — the article
section contains the table.

---

## Aggregated cross-experiment outputs (canonical)

| Output | Path | Producer |
|---|---|---|
| Cross-regime dynamics (Lyapunov, SD, recurrence, …) | `data/dynamics_cross_experiment.csv` | `src/experiments/dynamics/analyze.py` |
| Pub dynamics plots (B / C / E / F per experiment) | `data/pub_dynamics_plots/` | `scripts/render_per_exp_plots.py`, `src/experiments/dynamics/{regime_plots.py, partial_tsne.py, pub_tsne_plots_v2.py}` |
| Basin predictability cross | `data/aggregated/basin_predictability_cross/cross_basin_predictability.csv` + plots | `scripts/aggregate_basin_predictability.py` |
| T-sweep basin predictability | `data/aggregated/t_sweep_basin_predictability/` | `scripts/aggregate_t_sweep.py` |
| O1-vs-D1 T-sensitivity | `data/aggregated/t_sensitivity_cross_regime/` | `scripts/aggregate_o1_d1_t_sensitivity.py` |
| Perturbation cross-regime (4×5 bar) | `data/aggregated/perturbation_cross_regime/` | `scripts/aggregate_perturbation_cross_regime.py` |
| Dose-response (D1+O1) | `data/aggregated/perturbation_dose_response/` | `scripts/aggregate_dose_response.py` |
| Basin-hardening (inject-time × switch) | `data/aggregated/perturbation_basin_hardening/` | `scripts/aggregate_basin_hardening.py` |

---

## Coverage matrix

`COVERAGE.csv` at the repo root is a 37 row × 60 col matrix of every
experiment's analytical-artifact presence. Rows are experiments, columns
are artifacts (config / raw / metrics / reports / perturbation
visualizations / animations) plus metadata (phase, regime, nudge,
temperature, n_trajectories) and three summary columns
(`n_applicable_artifacts`, `n_present_artifacts`, `coverage_pct`).

**Cell semantics**:
- `1` — artifact is present
- `0` — artifact is **missing** (real gap)
- `""` (empty cell) — **structurally not applicable** to this
  experiment (e.g. perturbation experiments have no `regime=recursive`
  trajectories, so basin_entry / exit_return / permutation_tests are
  N/A there)
- positive integer in `n_*` columns — count

**Applicability rules** (in `scripts/build_coverage.py`):

| column | applicable when |
|---|---|
| `has_basin_entry_csv`, `has_exit_return_csv` | non-perturbation AND `cfg.<feature>.enabled = True` |
| `has_late_recurrence_csv` | `cfg.late_recurrence.enabled = True` |
| `has_dynamics_csv` (Lyapunov + sharpness) | `runs_per_condition >= 2` (D2 N=1 is N/A) |
| `has_bootstrap_summary` | `cfg.bootstrap.enabled = True` |
| `has_permutation_tests` | `time_shuffled` in `baseline_modes` AND non-perturbation |
| `has_basin_predictability_*` | non-perturbation (perturbation regimes are conditions, not the recursive vs no_feedback the predictor expects) |
| `has_switching_summary`, `relaxation_*`, `G/H/I`, `flow_*_by_condition` | perturbation experiment (`exp_perturb_*`) |
| `has_geodesic_barriers_*`, `has_rg_dendrogram_summary` | one of the 5 perturbation pilots (4 main + D2) |
| `has_rg_stack_png` | one of the 4 main perturbation pilots |
| `n_animation_mp4`, `n_animation_gif` | one of the 5 perturbation pilots OR one of the 4 pub diagnostic experiments |

After applying applicability, **all 37 experiments report 100%
coverage** of their applicable artifacts (mean = 100.0%, median =
100.0%). This means the matrix has no fillable gaps left — every cell
is either filled (1 / positive count) or marked N/A by structural
design. Regenerate with `python -m scripts.build_coverage`.

### Coverage profile by phase × artifact category

The shape of the matrix tells the story of the project — different
experiment phases run different analyses by design. Reading
"x/y" as "x experiments have this artifact among y to which it's
applicable":

| artifact category | Phase 0 (3) | Phase 1 (8) | Phase 2 (12) | Phase 3 (14) |
|---|---|---|---|---|
| **raw + config** (config.yaml, steps.jsonl, manifest, run.log) | 3/3 | 8/8 | 12/12 | 14/14 |
| **per-trajectory metric battery** (recurrence, dwell, basin, periodicity, dispersion, dynamics, explained_variance) | 3/3 | 8/8 | 12/12 | 14/14 |
| **v2 metrics** (basin_entry, exit_return, late_recurrence) | 1/1 (only `exp_long`/`exp_noclip`; `exp_default` config has the flags off → N/A there) | 8/8 | 12/12 | 1/1 (only the D2 exploratory parent — `exp_perturb_*` runs are N/A because there's no recursive regime to anchor entry/return) |
| **statistical** (bootstrap_summary, permutation_tests) | 1–2 / 1–2 (`exp_default` had bootstrap off; permutation needs `time_shuffled`, which T-sweeps don't include) | 8/8 | 5/12 permutation (7 T-sweeps don't run `time_shuffled` baseline) | 14/14 bootstrap; 1/1 permutation (only the D2 exploratory parent has recursive runs) |
| **PCA / t-SNE / clusters** (n_pca_models, n_pca_projections, n_tsne_csvs, n_cluster_csvs) | 3/3 | 8/8 | 12/12 | 14/14 |
| **reports** (report.md, report_operators.md, basin_predictability) | 3/3 | 8/8 | 12/12 | 1/1 basin_predictability (perturbation experiments are N/A); 14/14 reports |
| **single-condition geometric viz** (geodesic_skeleton, rg_dendrogram, bulk_landscape, flow_skeleton) | 3/3 | 8/8 | 12/12 | 14/14 |
| **multi-condition perturbation viz** (switching_summary, relaxation_*, G/H/I, flow_*_by_condition) | N/A | N/A | N/A | 13/13 (all perturbation experiments) |
| **headline-pilot extras** (geodesic_barriers CSV, rg_dendrogram_summary, rg_stack_png) | N/A | N/A | N/A | 4–5 / 4–5 (the 4 main pilots + D2; rg_stack only main 4) |
| **animations** (n_animation_mp4) | N/A | N/A | 4/4 (one per pub diagnostic, single `recursive` regime) | 5/5 (4 main pilots × 4 conditions = 16 + D2 × 2 = 18, plus the recursive ones already counted in pub) |

**Reading the table**: the per-experiment metric battery (recurrence,
dwell, basin, dynamics, periodicity, dispersion, …) is **fully
populated across all 37 experiments**. Statistical baselines and
predictability are populated wherever they're meaningful. Geometric
viz (single-condition) is populated everywhere. Multi-condition viz
is populated only on the 13 perturbation experiments. Animations
exist for the 9 experiments that warrant them (5 perturb pilots × N
condition + 4 pub × 1 recursive condition = 22 mp4 files).

### Cell location index (where in the matrix things live)

- **Want the per-trajectory metrics for a specific experiment?**
  `data/<exp>/metrics/{recurrence,dwell,basin,basin_entry_times,
  late_recurrence,exit_return,periodicity,dispersion,dynamics,
  bootstrap_summary,permutation_tests}.csv` — match what COVERAGE.csv
  shows for that row.
- **Want the perturbation switching numbers?**
  `data/exp_perturb_*/reports/perturbation/switching_summary.csv`.
  All 13 perturbation experiments have it (D2 exploratory drilldown
  is the parent run, not a perturbation run).
- **Want the cross-pilot V\* table from §5.10?**
  `data/aggregated/perturbation_geometric_barriers/v_star_table.csv`
  (5 rows × 4 conditions). The wide RG merge-distance table is
  alongside as `rg_merge_table.csv`.
- **Want the cross-experiment dynamical-systems metrics?**
  `data/dynamics_cross_experiment.csv` (19,074 rows: every
  observable × space × experiment).
- **Want the basin-predictability cross-regime comparison?**
  `data/aggregated/basin_predictability_cross/cross_basin_predictability.csv`.
- **Want a 3D animation of the cloud + perturbation kicks?** 22 mp4
  files under `data/exp_{perturb_*,pub_*}/reports/perturbation/animation3d_*.mp4`.

### What was filled to reach 100%

In the order it was done during the gap-fill pass:

1. Ran `dynamics.analyze --all` → 19 missing `dynamics.csv` files
   (skipped only D2 N=1 runs which can't compute ensemble-spread
   Lyapunov).
2. Ran `analyze_ext` on 24 experiments to populate `periodicity.csv`,
   `dispersion.csv`, and `report_operators.md`.
3. Ran the standard `cmd_analyze` on the 13 perturbation experiments
   to populate the full per-trajectory metric battery (recurrence,
   dwell, basin, late_recurrence, exit_return, t-SNE projections,
   PCA models, cluster occupancy, …).
4. Ran `cmd_report` on 14 experiments to populate `report.md` +
   `reports/plots/`.
5. Ran `geodesic_skeleton`, `rg_dendrogram`, `bulk_plots`,
   `flow_skeleton` (with `--conditions recursive`) on 19
   non-perturbation experiments to populate the 4 single-condition
   geometric visualizations.
6. Re-ran `cmd_analyze` + `cmd_report` on `exp_default` to populate
   v2-era metrics that the original 2025 run didn't compute.
7. Ran `geodesic_skeleton + rg_dendrogram` on `exp_perturb_D2_exploratory`
   so D2 has the same companion CSVs as the 4 main pilots.
8. Patched `basin_predictability.py` with **adaptive `n_splits`** —
   StratifiedKFold previously crashed on phase-1 pilots whose
   smallest cluster had < 5 members; now uses
   `min(5, smallest_class_size)` and returns NaN when 2-fold is
   impossible.
9. Extended `aggregate_perturbation_geometric_barriers.py` to include
   D2 as a fifth row (with NaN for neutral/lorem since D2 ran only
   control + adversarial).
10. Added applicability rules in `build_coverage.py` so cells that
    are structurally not-applicable show as empty (rather than 0)
    and don't count against coverage_pct.

## How a reviewer should walk this

1. **Pick a claim** in ARTICLE.md.
2. **Find its section** in this file (sections mirror the article).
3. The row gives: which `data/<exp>/` dir, which CSV column, which PNG,
   which `src/...` module / function.
4. **Confirm presence**: open `COVERAGE.csv`, find the row for that
   `<exp>`, check the `has_*` or `n_*` column for the artifact. `1` /
   positive count = present; empty = N/A by design (read the
   "Coverage matrix" section above for applicability rules).
5. **Reproduce**: load the cited CSV with pandas, or invoke the cited
   CLI with the cited config — the output is byte-deterministic for
   the analysis stage.

If a claim cannot be located here, the corresponding fix is one of:
(a) the claim is interpretive (§6 / §7) — read the cited §5 row;
(b) the article is ahead of the code — file an audit issue (the most
recent batch was B-1..B-10 — see commit history); (c) the code emits
the artifact under a different path than this map — update this file.

If `COVERAGE.csv` shows `0` for a cited artifact (a real missing
file), that's a regenerable gap — re-run the corresponding analysis
stage (see "What was filled to reach 100%" in the Coverage matrix
section above for the standard recipes).

---

## Verification status (self-audit of this document)

This document was verified end-to-end against the filesystem and
source tree at the time of writing. Coverage of the verification:

### ✓ Verified present (filesystem)

- **All 36 experiment dirs** under `data/exp_*/` cited by name —
  every `data/<exp>/` referenced exists on disk.
- **All 33 config YAMLs** cited under `configs/{operators,dialog,perturbation}/`
  exist.
- **All 6 aggregator scripts** + `render_per_exp_plots.py` +
  `build_publication_configs.py` exist under `scripts/`.
- **All 7 aggregated output dirs** under `data/aggregated/` exist;
  `data/aggregated/basin_predictability_cross/cross_basin_predictability.csv`
  (the canonical pub source for §5.3) is present.
- **Per-experiment metrics CSV skeleton** (12 files: dynamics, recurrence,
  dwell, basin, basin_entry_times, late_recurrence, exit_return,
  periodicity, dispersion, permutation_tests, bootstrap_summary,
  explained_variance.json) — verified for `exp_pub_O1_continue` as a
  representative pub experiment.
- **Per-experiment perturbation report skeleton** (switching_summary.csv,
  switching_rates.png, relaxation_curves.png, relaxation_table.csv,
  geodesic_skeleton_pca.png, rg_dendrogram_pca.png, bulk_landscape_pca.png,
  flow_skeleton_pca.png, joint_pca10_clusters.csv) — verified for
  `exp_perturb_O1_pilot` as representative.
- **All 6 stage reports** (`docs/reports/REPORT{1..6}.md`) and
  `docs/DATA_INDEX.md` exist.
- `data/dynamics_cross_experiment.csv` and `data/pub_dynamics_plots/`
  exist.

### ✓ Verified present (source code)

All of the following functions exist with the cited signatures (line
numbers verified at time of writing):

- Core loop / context / observables: `core/trajectory.py::run_trajectory`
  (61), `core/context.py::clip_context` (18), `core/observables.py::{observable_output (10), observable_rolling (14), observable_context_tail (19), observable_context_full (23), build_all_for_run (37)}`
- API: `api/generator.py::generate_step` (44),
  `api/embedder.py::embed_texts` (47)
- Baselines: `core/baselines.py::{no_feedback_provider (39),
  independent_regeneration_provider (49)}`
- Analysis primitives: `analysis/recurrence.py::recurrence_for_trajectory`
  (19), `analysis/clustering.py::cluster_points` (18),
  `analysis/dwell.py::dwell_stats_for_trajectory` (35),
  `analysis/basin.py::{find_target_cluster (19), basin_score_for_condition (47)}`,
  `analysis/basin_entry.py::detect_basin_entry` (16),
  `analysis/late_recurrence.py::late_recurrence_for_trajectory` (8),
  `analysis/exit_return.py::exit_return_for_trajectory` (21),
  `analysis/pca.py::{fit_pca (22), save_pca_projection (43), save_pca_model (69)}`,
  `analysis/tsne.py::fit_tsne` (18),
  `analysis/bootstrap.py::{wilson_ci (20), bootstrap_mean_ci (78), permutation_test_mean_diff (115)}`
- Dynamics extension: `experiments/dynamics/lyapunov.py::compute_lyapunov_spectrum`
  (80), `experiments/dynamics/sharpness_dim.py::{sharpness_dimension (57), effective_rank (125)}`
- Classifiers: `experiments/operators/classifier.py::classify_three_axis`
  (50), `reports/summary.py::classify_two_axis` (137)
- Perturbation: `experiments/perturbation/main.py::_resolve_perturbation_text`
  (92)

### ✓ Inaccuracies found and fixed inline (during this verification)

The following EVIDENCE.md citations were imprecise at the time of
first authorship and have been corrected in this same revision:

- **F-1**: §4.8 Plot B — was cited as
  `regime_plots.py::plot_per_family_grid` (no such function). Actual:
  cross-exp `regime_plots.py::plot_trajectory_grid` (line 194), per-exp
  v2 `pub_tsne_plots_v2.py::{plot_v2_per_family_grid (206), plot_v2_per_family_parity_grid (290)}`.
- **F-2**: §4.8 Plot C — per-exp legacy single-IC variant was
  attributed to `regime_plots.py`; it actually lives at
  `pub_tsne_plots_v2.py::plot_v2_single_ic_trajectories` (line 376).
  The cross-exp ensemble-spread variant `plot_spread_timelines` (line 341)
  was correct.
- **F-3**: §4.8 Plot E — was cited as `field_plots.py + flow_plots.py`.
  Actual rendering is in `regime_plots.py::{plot_flow_field_single (766),
  plot_flow_field_grid (822), plot_flow_field_tsne_single (530),
  plot_flow_field_tsne_grid (587)}`. `field_plots.py` provides drawing
  primitives (`plot_streamlines_density (119), plot_speed_colored_streamlines (180),
  plot_divergence_field (240)`).
- **F-4**: §4.8 Plot A — was cited as `reports/plots.py::plot_tsne`.
  That helper exists for legacy per-exp plots (`tsne_<obs>_by_*.png`),
  but the lettered Plot A files (`A_joint_*`, `A_v2_*`) come from
  `regime_plots.py::plot_joint_tsne` (line 82) and
  `pub_tsne_plots_v2.py::plot_v2_by_*` (lines 58/91/117/162).
- **F-5**: §4.9 G/H/I plots — cited public function names
  (`plot_streamlines_density`, `plot_speed_streamlines`,
  `plot_divergence_heatmap`) in
  `src/experiments/perturbation/field_plots.py`. Those names belong
  to the **dynamics** version (`plot_speed_colored_streamlines`,
  `plot_divergence_field`); the perturbation version uses **private
  functions** `_plot_panel_streamlines_density (89)`,
  `_plot_panel_speed_streamlines (113)`, `_plot_panel_divergence (137)`,
  driven by the public entry `render_fields_for_pilot (167)`.
- **F-6**: §4.3.4 adjacent-step similarity — speculatively pointed at
  `tests/test_embeddings_adjacency.py`, which does not exist. Replaced
  with the actual evidence (PCA-2 and t-SNE step-colored plots).
- **F-7 (RESOLVED — article updated)**: §5.10 V* table at
  ARTICLE.md:1655–1658 originally disagreed with the recomputed values
  from the current `geodesic_skeleton.py`. The article has now been
  updated to the measured values (4.4/2.3/2.6/2.2 for O1, etc.) and
  the surrounding interpretive paragraph rewritten to explain the
  high O2/O3-lorem V* as "lorem creates a *new* far basin; geodesics
  traverse low-density plateau → high V*; perturbed runs land *into*
  the new basin, hence 100% switching without climbing the barrier."
  The original mismatch table is preserved here for traceability:

  | regime | column | article | measured (`V_star_mean`) |
  |---|---|---:|---:|
  | O1 | control | 2.5 | **4.43** |
  | O1 | neutral | 2.6 | 2.33 |
  | O1 | lorem | 2.5 | 2.64 |
  | O1 | adversarial | 2.2 | 2.21 ✓ |
  | O2 | control | 2.7 | 2.83 ✓ |
  | O2 | neutral | 2.5 | 3.55 |
  | O2 | lorem | **0.55** | **5.57** |
  | O2 | adversarial | 1.3 | 1.55 |
  | O3 | control | 2.3 | 1.06 |
  | O3 | neutral | 2.5 | 5.22 |
  | O3 | lorem | **0.52** | **6.97** |
  | O3 | adversarial | 1.4 | 2.21 |
  | D1 | control | 1.2 | 1.32 ✓ |
  | D1 | neutral | 1.0 | 1.08 ✓ |
  | D1 | lorem | 0.8 | 0.84 ✓ |
  | D1 | adversarial | 0.4 | 0.40 ✓ |

  The most consequential mismatch is the **lorem** column for
  replace-mode regimes: article reports 0.55 / 0.52 ("barriers
  collapsed") but the measurement shows 5.57 / 6.97 (geodesics cross
  high-V plateaus, with several hitting the V_max=8.0 floor where
  ρ≈ε). The high V* is **internally consistent with the §5.10 RG
  narrative** ("lorem expands the cloud to merge distance 3.64/3.25 …
  produces a *new* basin that sits [far from control]") — a new far
  basin means geodesics traverse low-density space, which gives high
  V*, not low. So the article's RG and V* tables tell **opposite
  stories**, and the new measurement supports the RG story.

  D1 matches well because its basins are spatially compact (stylistic,
  not content-bound) and inter-basin geodesics never traverse
  zero-density regions; replace-mode regimes have wider lorem-induced
  spread and do.

  **Recommended fix**: update §5.10 V* table to the measured numbers
  (above) and amend the surrounding interpretive paragraph at
  ARTICLE.md:1665–1673 to say "V* > 5 under O2/O3 lorem" (high
  geometric barrier consistent with a *new distant basin*) instead
  of the current "V* < 0.5 — barriers are small". The interpretive
  conclusion (replace-mode lorem creates a new basin attractor that
  perturbed runs commit to) does not change; only the directional
  language about V* needs flipping.

### Remaining caveats / known gaps

- **CG-1 (resolved + article updated)**: V* values for §5.10
  (ARTICLE.md:1655–1658) are now dumped to
  `reports/perturbation/geodesic_barriers_pca.csv` (per-geodesic) and
  `geodesic_barriers_summary.csv` (per-condition mean/min/max/n) by
  `src/experiments/perturbation/geodesic_skeleton.py`. After rerunning
  on all four perturbation pilots, the D1 row matched the article
  numerically but O1/O2/O3 disagreed (see F-7 history below). The
  ARTICLE.md §5.10 V* table and surrounding interpretive paragraph
  have been updated to the measured values; the regime-level
  conclusion (replace-mode lorem causes 100% switching by basin
  *creation* rather than barrier *crossing*) is unchanged.
- **CG-2 (resolved)**: §5.10 RG dendrogram values are now dumped to
  `reports/perturbation/rg_dendrogram_summary.csv` by
  `src/experiments/perturbation/rg_dendrogram.py`. After rerunning on
  all four perturbation pilots, **the values match the article
  exactly** (O1 control 2.38, O2 lorem 3.64, O3 lorem 3.25, D1 all
  ~1.79). The article's RG table is reproducible from this CSV.
- **CG-3 (resolved)**: 654 MB of leftover diagnostic files
  (`steps.jsonl.bak`, `steps.jsonl.doubled`) under
  `data/exp_pub_D1_dialog_curious_helpful_v2/raw/` have been deleted.
  The canonical `steps.jsonl` (163 MB) and `manifest.json` remain.
- **CG-4** unchanged — D1 T=0.8 / O1 T=0.8 cell reuse is documented
  in §5.4 / `docs/DATA_INDEX.md`.
- **CG-5** unchanged — per-experiment dynamics plots are conditional
  on the dynamics extension having run.
- **CG-6** unchanged — line numbers are anchors, not invariants.
- **CG-7 (resolved)**: `ARTICLE_SCI.md` (461 lines, an alternative
  formal-paper rendering) was deleted at the user's request as
  superseded by ARTICLE.md.
- **CG-3**: `data/exp_pub_D1_dialog_curious_helpful_v2/raw/` contains
  `steps.jsonl.bak` and `steps.jsonl.doubled` artifacts (visible in
  `git status`). These are leftover diagnostics from a duplicate-import
  recovery and are not load-bearing for any cited claim. Safe to ignore;
  recommend a future cleanup pass.
- **CG-4**: §5.4 D1 T=0.8 cell — there is no
  `exp_pub_D1_Tsweep_T08/`; the §5.4 row is sourced from
  `exp_pub_D1_dialog_curious_helpful_v2/` (which is the canonical pub
  D1 run at T=0.8). EVIDENCE.md notes this reuse explicitly. Likewise
  O1 T=0.8 may reuse `exp_pub_O1_continue/` as the 0.8 cell, with
  `exp_pub_O1_Tsweep_T08/` being a smaller-scope reproduction.
- **CG-5**: Paths cited as "if rendered" (e.g. per-experiment dynamics
  plots in `reports/plots/dynamics_*`) are conditional on the
  `dynamics` extension having been run on that experiment. For pub
  experiments these typically live in `data/pub_dynamics_plots/` rather
  than per-experiment dirs.
- **CG-6**: Line numbers shown for source functions are **anchors at
  the time of writing** (commit `ac0a3f7` + B-1..B-10 doc edits). They
  may drift if the source is edited; the function names are stable.

### How to re-run this verification

```bash
# 1) Filesystem checks (data dirs / configs / scripts)
bash -c 'ls data/exp_*/ configs/*/*.yaml scripts/aggregate_*.py 2>&1 | tail'

# 2) Function existence
PYTHONPATH=. grep -rn "^def " src/ | grep -E '(run_trajectory|recurrence_for_trajectory|...)'

# 3) Plot filename emission
grep -rn "out_dir / f\"[A-Z]_" src/experiments/dynamics/ src/experiments/perturbation/

# 4) End-to-end: rerun a representative pipeline and diff the metrics dir
python -m src.experiments.operators.main analyze --config configs/operators/O1_pub.yaml
python -m src.experiments.dynamics.basin_predictability --config configs/operators/O1_pub.yaml
diff <(ls data/exp_pub_O1_continue/metrics/) /tmp/expected_metrics_listing.txt
```
