# REQ1 → source-code mapping

This document pairs every section of `d:\ROOT\llmattr\req1.txt` with the file(s)
and function(s) that implement it, so you can verify coverage at a glance.

Paths are relative to `d:\ROOT\llmattr\llm_attractor_experiment\`.

---

## Top-level goal (req1 §Goal)

| req1 point | implementation | notes |
|---|---|---|
| "run many append-only trajectories with an OpenAI model" | `src/main.py` → `cmd_run`; `src/core/trajectory.py` → `run_trajectory` | |
| "build embeddings for outputs and state proxies" | `src/main.py` → `cmd_embed`, `_embed_observable`; `src/api/embedder.py` → `embed_texts` | |
| "project them with PCA" | `src/analysis/pca.py` → `fit_pca`; invoked in `cmd_analyze` | |
| "compute recurrence, dwell, and basin metrics" | `src/analysis/recurrence.py`, `dwell.py`, `basin.py`; orchestrated in `src/main.py` → `cmd_analyze` | |
| "compare against baselines" | `src/core/baselines.py`; post-hoc `time_shuffled` block in `cmd_analyze` | |
| "generate plots and a final report" | `src/reports/plots.py` (21+ plot functions); `src/reports/summary.py` → `write_report` / `write_report_v2`; invoked in `cmd_report` | |

---

## Core experimental definition (req1 §Core)

| req1 point | implementation |
|---|---|
| `Y_t ~ P_theta(. \| X_t, N)` — generation call | `src/api/generator.py` → `generate_step` (uses `client.responses.create` with `store=False`) |
| `X_{t+1} = clip(X_t \|\| Y_t)` | `src/core/context.py` → `append_only_update` |
| `clip` deterministic bounded-context rule | `src/core/context.py` → `clip_context(text, max_chars, rule)` |
| append-only (no rewriting/summarization/deletion except overflow) | trajectory loop in `src/core/trajectory.py` never calls anything except `append_only_update` with `rule="tail_chars"` |

---

## Observables to embed (req1 §Observables)

| req1 observable | implementation |
|---|---|
| φ₁ = E(Y_t) "Output-only" | `src/core/observables.py` → `observable_output` |
| φ₂ = E(Y_{t-k+1} ‖ … ‖ Y_t) "Rolling-window" | `src/core/observables.py` → `observable_rolling(steps, t, k, sep)` |
| φ₃ = E(tail_M(X_t)) "Context-tail" | `src/core/observables.py` → `observable_context_tail(step, max_chars)` |
| rolling `k=3` as primary | all shipped configs set `rolling_window_k: 3`; default in `src/config.py` |
| ("bonus": whole-context observable, fixed-size tail) | `observable_context_full` — added in response to user request during exp_noclip |

`build_all_for_run(steps, observable_types, k, tail_chars, full_chars)` produces
strings for all configured observables at once; supports the generic
`rolling_k{N}` pattern (regex `^rolling(?:_k(\d+))?$`).

---

## Deliverables (req1 §Deliverables)

| req1 deliverable | implementation |
|---|---|
| 1. Runnable Python project | `requirements.txt`; entry at `python -m src.main …` |
| 2. Config-driven experiment runner | `src/config.py` + `configs/*.yaml` |
| 3. Raw data logs for all runs | `data/<exp_id>/raw/steps.jsonl` (JSONL) + `manifest.json` |
| 4. Embedding datasets | `data/<exp_id>/embeddings/<observable>/{embeddings.npy, metadata.parquet}` |
| 5. PCA projections | `data/<exp_id>/metrics/pca_{2,10,20}_<obs>.csv` + `.npz` models |
| 6. Quantitative metrics | `data/<exp_id>/metrics/{recurrence,dwell,basin,…}.csv` |
| 7. Plots | `data/<exp_id>/reports/plots/*.png` (42 PNGs per experiment in the standard pipeline) |
| 8. Final markdown report | `data/<exp_id>/reports/report.md` (written by `write_report_v2` when v2 metrics exist, else `write_report`) |

---

## Project structure (req1 §Project structure)

| req1 path | actual path | status |
|---|---|---|
| `README.md` | `README.md` | ✓ |
| `requirements.txt` | `requirements.txt` | ✓ |
| `.env.example` | `.env.example` | ✓ |
| `configs/default.yaml` | `configs/default.yaml` | ✓ |
| `configs/deterministic.yaml` | `configs/deterministic.yaml` | ✓ |
| `configs/stochastic.yaml` | `configs/stochastic.yaml` | ✓ |
| `configs/basin.yaml` | `configs/basin.yaml` | ✓ |
| `src/main.py` | `src/main.py` | ✓ |
| `src/config.py` | `src/config.py` | ✓ |
| `src/api/openai_client.py` | `src/api/openai_client.py` | ✓ |
| `src/api/generator.py` | `src/api/generator.py` | ✓ |
| `src/api/embedder.py` | `src/api/embedder.py` | ✓ |
| (req2 addition) batch jobs | `src/api/batch_jobs.py` | ✓ |
| (req2 addition) evals | `src/api/evals_runner.py` | ✓ |
| `src/core/context.py` | `src/core/context.py` | ✓ |
| `src/core/trajectory.py` | `src/core/trajectory.py` | ✓ |
| `src/core/observables.py` | `src/core/observables.py` | ✓ |
| `src/core/baselines.py` | `src/core/baselines.py` | ✓ |
| `src/analysis/pca.py` | `src/analysis/pca.py` | ✓ |
| `src/analysis/clustering.py` | `src/analysis/clustering.py` | ✓ |
| `src/analysis/recurrence.py` | `src/analysis/recurrence.py` | ✓ |
| `src/analysis/dwell.py` | `src/analysis/dwell.py` | ✓ |
| `src/analysis/basin.py` | `src/analysis/basin.py` | ✓ |
| `src/analysis/robustness.py` | `src/analysis/robustness.py` | ✓ |
| `src/reports/plots.py` | `src/reports/plots.py` | ✓ |
| `src/reports/summary.py` | `src/reports/summary.py` | ✓ |
| `src/utils/io.py` | `src/utils/io.py` | ✓ |
| `src/utils/text.py` | `src/utils/text.py` | ✓ |
| `src/utils/logging.py` | `src/utils/logging.py` | ✓ |
| `src/utils/seeds.py` | `src/utils/seeds.py` | ✓ |
| `data/raw/` | `data/<exp_id>/raw/` | ✓ (per-experiment subdir) |
| `data/processed/` | not created — use `data/<exp_id>/metrics/` instead | deviation |
| `data/embeddings/` | `data/<exp_id>/embeddings/` | ✓ |
| `data/metrics/` | `data/<exp_id>/metrics/` | ✓ |
| `data/reports/` | `data/<exp_id>/reports/` | ✓ |
| `notebooks/exploratory_analysis.ipynb` | **not created** | deviation — covered by `src/utils/dump_messages.py` + ad-hoc inspection |

Additional files beyond req1:

- `src/utils/dump_messages.py` — debug helper for inspecting message flow
- `src/experiments/operators/*` — isolated module for the operator-regime follow-up (`exp_operators` in REPORT2)
- Tests under `tests/`

---

## Phase 1 — Config and infrastructure (req1 §Phase 1)

| req1 config field | actual Config field | location |
|---|---|---|
| OpenAI model for generation | `generation_model` | `src/config.py` `Config` |
| OpenAI model for embeddings | `embedding_model` | same |
| number of prompt families | implicit in `prompt_families` list | same |
| number of initial conditions per family | `initial_conditions_per_family` | same |
| number of runs per condition | `runs_per_condition` | same |
| trajectory length T | `steps_per_run` | same |
| generation length N | `max_output_tokens` | same |
| temperature | `temperature` | same |
| top_p | `top_p` | same |
| max_output_tokens | `max_output_tokens` | same |
| clip rule | `clip_rule` | same |
| max context size | `max_context_chars` | same |
| observable types to compute | `observables: [output, rolling_k3, context_tail]` | same |
| rolling window size k | `rolling_window_k` | same |
| PCA dimensions | `pca_dims: [2, 10]` (20 in v2 configs) | same |
| clustering method | `clustering.method` (dbscan\|kmeans) + params | `ClusteringConfig` |
| output paths | `output_dir` + `cfg.experiment_dir` property | same |
| baseline toggles | `baseline_modes: [...]` | same |

### Acceptance criteria

| req1 | implementation |
|---|---|
| experiment runs entirely from a config file | `python -m src.main all --config configs/default.yaml` |
| config saved into output folder for reproducibility | `save_config_snapshot(cfg, cfg.experiment_dir / "config.yaml")` called at start of `cmd_run` |

---

## Phase 2 — Context and trajectory engine (req1 §Phase 2)

| req1 requirement | implementation |
|---|---|
| `ContextState` object with serialized text / step / length / clip method | `src/core/context.py` → `ContextState` dataclass (`text`, `step`, `length_chars`, `clip_rule`), plus `ContextState.initial` factory |
| `clip_context(text, max_len, rule)` | `src/core/context.py` → `clip_context(text, max_chars, rule)` |
| rule `tail_chars` | implemented |
| rule `tail_tokens` if tokenizer available | **not implemented** — intentional (avoids tokenizer dep); noted in `src/utils/text.py` `approx_token_count` fallback |
| optional `strict_stop` | implemented — raises `ContextOverflow` |
| default = deterministic tail clipping | default `rule="tail_chars"` throughout |
| `run_trajectory(initial_context, config)` | `src/core/trajectory.py` → `run_trajectory(client, initial_context, config, ids, system_prompt=None, step_sink=None, context_provider=None)` |
| per-step loop: generate → append → clip → save | the body of `run_trajectory` |

### Step record schema (req1 Phase 2)

| req1 field | actual field in step record | location |
|---|---|---|
| `experiment_id` | `experiment_id` | `_step_record` in `src/core/trajectory.py` |
| `prompt_family` | `prompt_family` | same |
| `initial_condition_id` | `initial_condition_id` | same |
| `run_id` | `run_id` | same |
| `step` | `step` | same |
| `context_before` | `context_before` | same |
| `output_text` | `output_text` | same |
| `context_after` | `context_after` | same |
| `context_length_chars` | `context_length_chars` | same |
| `generation_params` | `temperature`, `top_p`, `max_output_tokens`, `model` (separate fields, not a nested object) | same |
| response metadata | `response_id`, `latency_sec`, `retries` | same |

Extras added: `regime`, `context_before_hash`, `output_hash`, `timestamp`.

### Acceptance criteria

| req1 | implementation |
|---|---|
| one trajectory run creates full JSONL log | `make_jsonl_sink` appends each record; `data/<exp_id>/raw/steps.jsonl` |
| rerunning with same config produces same directory structure | `cfg.experiment_dir` is deterministic from `experiment_id` |

---

## Phase 3 — OpenAI API integration (req1 §Phase 3)

### `generator.py`

| req1 responsibility | implementation |
|---|---|
| function `generate_text(context_text, config) -> GenerationResult` | **named `generate_step`** in `src/api/generator.py` (same signature semantics: `generate_step(client, context_text, config, system_prompt=None, max_retries=5, base_delay=2.0)`) |
| send request to Responses API | `client.responses.create(**request)` |
| return text | `resp.output_text` via `_extract_output_text` helper |
| optionally request logprobs | `include=["message.output_text.logprobs"]` when `config.include_logprobs` |
| capture response IDs and metadata | `response_id`, `latency_sec`, `retries` stored in `GenerationResult` |
| robust retry handling | `for attempt in range(max_retries + 1)` with `_is_retryable` filter |
| rate-limit aware backoff | exponential: `base_delay * (2**attempt) + random.uniform(0, 0.5)` |
| save raw response payload if configured | full response stored in `GenerationResult.raw` via `_response_to_dict` (but not persisted to disk by default — noted in step record `response_id` only) |

### `embedder.py`

| req1 responsibility | implementation |
|---|---|
| function `embed_texts(texts, config)` | `src/api/embedder.py` → `embed_texts(client, texts, config, batch_size=128, max_retries=5, base_delay=2.0, normalize=True)` |
| batch embedding requests | `_chunks(seq, n)` generator + per-batch `_embed_batch` |
| normalize responses into arrays | `np.array([d.embedding for d in resp.data], dtype=np.float32)` |
| optionally L2-normalize | `normalize=True` default: `mat / (||mat|| + 1e-12)` |
| save embeddings to disk | save handled one level up in `_embed_observable` (`save_npy` + `write_parquet`) — keeps embedder pure |

### Acceptance criteria

| req1 | implementation |
|---|---|
| generation and embedding can be tested independently | separate modules, separate tests; integration test `tests/test_integration.py` monkeypatches both |
| failures are logged cleanly | `log.error`/`log.warning` around retries |
| partial progress is not lost | checkpointing per trajectory: `manifest.json` updated after each completed run |

---

## Phase 4 — Observable construction (req1 §Phase 4)

| req1 builder | implementation |
|---|---|
| `build_output_observable(trajectory_steps) -> list[str]` | `observable_output(step)` + batch wrapper via `build_all_for_run(steps, ["output"], ...)` |
| `build_rolling_observable(trajectory_steps, k=3, sep="\n<SEP>\n")` | `observable_rolling(steps, t, k, sep)` — separator constant `ROLLING_SEP = "\n<SEP>\n"` |
| `build_context_tail_observable(trajectory_steps, max_chars=M)` | `observable_context_tail(step, max_chars)` |

### Constraints (req1 Phase 4)

| req1 | implementation |
|---|---|
| observable serialization deterministic | no randomness; pure string operations |
| exact formatting fixed across all runs | `ROLLING_SEP` is a module constant; separator never varies |
| long observables clipped consistently | `context_tail` always slices `[-max_chars:]`; `context_full` same pattern |

### Acceptance criteria

| req1 | implementation |
|---|---|
| same trajectory → same observable strings | `test_observables.py::test_rolling_is_deterministic` |
| each observable type has unit tests | `tests/test_observables.py`, `test_observables_rolling_k.py`, `test_context_full.py` |

---

## Phase 5 — Embedding dataset creation (req1 §Phase 5)

| req1 output | implementation |
|---|---|
| vector matrix | `data/<exp_id>/embeddings/<obs>/embeddings.npy` (shape `(N, 1536)` for text-embedding-3-small) — written by `save_npy` |
| metadata table linking rows to trajectory steps | `metadata.parquet` with columns: `regime`, `prompt_family`, `initial_condition_id`, `run_id`, `step`, `text_len` — written by `write_parquet` |

### Row schema

| req1 field | location in metadata.parquet |
|---|---|
| `observable_type` | implied by directory name (`embeddings/<obs>/`) — not duplicated per row |
| `experiment_id` | implied by directory name (`data/<exp_id>/…`) |
| `run_id` | in metadata.parquet |
| `step` | in metadata.parquet |
| `prompt_family` | in metadata.parquet |
| `initial_condition_id` | in metadata.parquet |
| original text | **not stored** — retrievable from `raw/steps.jsonl` by (run_id, step) |
| embedding path or inline vector reference | row index in `embeddings.npy` matches row index in metadata.parquet |

### Acceptance criteria

| req1 | implementation |
|---|---|
| embeddings reloadable without recomputation | `load_npy(cfg.embeddings_dir/obs_name/"embeddings.npy")` + `read_parquet(…/metadata.parquet)` in `cmd_analyze` |
| metadata allows trace-back to raw step | join on `(regime, prompt_family, initial_condition_id, run_id, step)` |

---

## Phase 6 — PCA (req1 §Phase 6)

| req1 requirement | implementation |
|---|---|
| PCA-2 projection | `pca_dims` config includes 2; `fit_pca(embeddings, dim=2)` |
| PCA-10 projection | same, dim=10 |
| PCA-20 projection | same, dim=20 (enabled in all v2 configs) |
| explained variance ratios | `PCAResult.explained_variance_ratio`; saved to `pca_<dim>_<obs>_explained_variance.csv` and to `explained_variance.json` |
| fit PCA on all points jointly per observable | `fit_pca(vecs, dim)` called once per (observable, dim); never per trajectory |
| do not fit per trajectory | enforced by structure — there's no per-trajectory PCA fit anywhere in the code |
| save PCA model | `save_pca_model(result, …)` → `pca_<dim>_<obs>_model.npz` |

### Plots (req1)

| req1 plot | implementation |
|---|---|
| all trajectories in PCA-2 | `plot_trajectories_pca2` in `src/reports/plots.py` |
| colored by run | `plot_trajectories_pca2(…, color_by="run_id")` |
| colored by prompt family | `plot_trajectories_pca2(…, color_by="prompt_family")` |
| time-colored trajectories | `plot_time_colored(…)` |
| separate plots for baselines | baseline points in same PCA plots colored by `regime`; separable via filtering |

### Acceptance criteria

| req1 | implementation |
|---|---|
| every observable has saved PCA projections and plots | `cmd_analyze` iterates `cfg.observables`; `cmd_report` iterates same |
| explained variance report generated | `explained_variance.json` + per-observable `_explained_variance.csv` |

---

## Phase 7 — Recurrence metric (req1 §Phase 7)

| req1 requirement | implementation |
|---|---|
| recurrence if `|z_t - z_s| < ε, |t-s| > τ` | `src/analysis/recurrence.py` → `recurrence_for_trajectory(points, epsilon, tau, metric)` |
| recurrence count | `RecurrenceStats.recurrence_count` |
| recurrence rate | `RecurrenceStats.recurrence_rate` |
| average return time | `RecurrenceStats.avg_return_lag` |
| nearest nonlocal neighbor distance | `RecurrenceStats.nearest_nonlocal_distance` |
| recurrence plot matrix (optional) | `recurrence_matrix(points, epsilon, tau, metric)` |
| metric = cosine or euclidean | `metric` parameter; cosine used in raw space, euclidean in PCA spaces |
| ε threshold | config `recurrence.epsilon` |
| τ minimum lag | config `recurrence.tau` |

### Acceptance criteria

| req1 | implementation |
|---|---|
| works in raw and PCA-k spaces | `cmd_analyze` loops over `spaces = {"raw": vecs, "pca2": …, "pca10": …, "pca20": …}` |
| results aggregated per run and globally | `recurrence.csv` has one row per (observable, space, regime, run); `summary.py::_summary_by_regime` groups globally |

---

## Phase 8 — Dwell metric (req1 §Phase 8)

| req1 requirement | implementation |
|---|---|
| KMeans support | `src/analysis/clustering.py` → `cluster_points(points, method="kmeans", params={"n_clusters": k})` |
| DBSCAN support | `cluster_points(points, method="dbscan", params={"eps": …, "min_samples": …})` |
| (default DBSCAN per spec) | default in `ClusteringConfig.method = "dbscan"` |
| contiguous dwell lengths | `dwell_runs(labels)` returns list of `(cluster, start, length)` |
| mean / median / longest dwell | `DwellStats.mean_dwell`, `median_dwell`, `longest_dwell` |
| re-entry count | `DwellStats.reentry_count` |
| per-cluster per-run stats | `dwell_stats_for_trajectory(labels)` returns one `DwellStats` per non-noise cluster |
| cluster occupancy report | `data/<exp_id>/metrics/cluster_occupancy_<obs>_<space>.csv` |

### Acceptance criteria

| req1 | implementation |
|---|---|
| dwell stats computed per run and per cluster | row format in `dwell.csv`: `(observable, space, regime, prompt_family, initial_condition_id, run_id, cluster, mean_dwell, median_dwell, longest_dwell, reentry_count, occupancy)` |
| cluster occupancy report generated | `cluster_occupancy_<obs>_<space>.csv` |

---

## Phase 9 — Basin convergence metric (req1 §Phase 9)

| req1 requirement | implementation |
|---|---|
| find target region as most-visited late-time cluster | `src/analysis/basin.py` → `find_target_cluster(labels, steps, late_fraction)` |
| compute fraction of perturbed runs entering target by T* | `basin_score_for_condition(labels_by_run, steps_by_run, target_cluster, target_step)` |
| per-family / per-IC convergence | `cmd_analyze` groups by `(prompt_family, initial_condition_id)` and calls `basin_score_for_condition` per group |

### Perturbation methods (req1)

| req1 perturbation | implementation |
|---|---|
| suffix perturbation | `BasinConfig.perturbation_suffix` string + listed in `perturbations` — **planned but not actively used**; the `perturbations` field is plumbed through but the pipeline currently uses natural sampling variance across `runs_per_condition` as the perturbation mechanism |
| paraphrase perturbation | present as a named entry in `perturbations` list, requires explicit paraphrased prompts in config — unused so far |
| neutral sentence insertion | `BasinConfig.neutral_sentence` string — plumbed, not actively invoked |
| random seed change only | implicit: every run_id samples the LLM independently at temperature > 0 |

Note: basin convergence is currently computed across the natural `runs_per_condition` runs, which all share the same initial condition but differ by sampling variance. Explicit perturbation injection was descoped as a future extension.

### Acceptance criteria

| req1 | implementation |
|---|---|
| basin computed for each initial condition | `basin.csv` has rows keyed by `(observable, space, prompt_family, initial_condition_id)` |
| summary table with convergence fractions | same CSV; rendered as markdown table in report |

---

## Phase 10 — Baselines (req1 §Phase 10)

| req1 baseline | implementation |
|---|---|
| no_feedback (send original X₀ every step) | `src/core/baselines.py` → `no_feedback_provider()`; used via `context_provider` arg of `run_trajectory` |
| time_shuffled (shuffle time order after embeddings) | **post-hoc** in `cmd_analyze`: for each recursive trajectory, `time_shuffle_labels(labels_seq)` from `src/analysis/robustness.py` + identically for recurrence (shuffle point order then recompute) |
| independent_regeneration (fresh outputs from fixed family prompt) | `src/core/baselines.py` → `independent_regeneration_provider(family_prompt)` |

### Acceptance criteria

| req1 | implementation |
|---|---|
| metrics computed for main regime and all baselines | `cmd_analyze` runs the recurrence + dwell computations with the regime column tagged accordingly |
| comparison plots produced automatically | `plot_recurrence_distribution`, `plot_dwell_distribution` group by `regime` |

---

## Phase 11 — Robustness tests (req1 §Phase 11)

| req1 requirement | implementation |
|---|---|
| across observable type | metrics have `observable` column → group by observable |
| raw vs PCA-10 vs PCA-20 | metrics have `space` column → raw/pca2/pca10/pca20 rows all present |
| deterministic vs stochastic decoding | supported via `configs/deterministic.yaml` + `configs/stochastic.yaml` |
| prompt families | metrics have `prompt_family` column |
| multiple seeds/runs | metrics have `run_id` column |
| robustness report: mean, std, effect size, sign preservation | `src/analysis/robustness.py` → `summarize_metric`, `effect_vs_baseline` |

### Acceptance criteria

| req1 | implementation |
|---|---|
| report states robust vs representation-specific | classifier signal `robust_non_pca2_space` + `robust_across_two_observables` in `src/reports/summary.py::classify_evidence` / `classify_two_axis` |

---

## Phase 12 — Report generation (req1 §Phase 12)

| req1 section | implementation |
|---|---|
| 1. Experiment definition | `write_report_v2` header |
| 2. Config summary | `write_report_v2` "## Config summary" section |
| 3. Number of trajectories and steps | `write_report_v2` "## Data volume" — computed from `raw/steps.jsonl` line count |
| 4. Observable definitions | implicit in config summary listing `observables` |
| 5. PCA results | "## PCA explained variance" section |
| 6. Recurrence results | "## Global recurrence" (+ "## Late-time recurrence" in v2) |
| 7. Dwell results | "## Dwell (H1a primary)" |
| 8. Basin results | "## Basin (H1a primary)" |
| 9. Baseline comparison | all metric tables include `regime` column (recursive / no_feedback / time_shuffled rows) |
| 10. Robustness summary | implicit in classifier signals `dwell_positive_in_two_observables`, `dwell_positive_in_non_flat_space` |
| 11. Conclusion on Hypothesis 1 | "## Two-axis verdict" section with classifier output |

### Final conclusion format (req1)

| req1 label | classifier output |
|---|---|
| `not supported` | `"not_supported"` |
| `weak support` | `"weak_support"` |
| `moderate support` | `"moderate_support"` |
| `strong support` | `"strong_support"` |

### Classification logic (req1 "Suggested classification logic")

| req1 signal | classifier check | file |
|---|---|---|
| recurrence above baseline | `pos_effect(recurrence_df, "recurrence_rate")` | `src/reports/summary.py::classify_evidence` (legacy) and `classify_two_axis` |
| dwell above baseline | `pos_effect(dwell_df, "mean_dwell")` | same |
| basin convergence present | `basin_df["basin_score"].mean() > 0.5` (legacy) / `> 0.7` (two-axis) | same |
| effect robust across ≥2 observables and ≥2 spaces | `robust_across_two_observables`, `robust_non_pca2_space` signals | same |

**Deviation from req1:** in response to the REPORT1 finding that `no_feedback` is a degenerate comparator, the classifier was updated to prefer `time_shuffled` as the null when present. The four-label output mapping still matches req1's spec verbatim.

---

## Required implementation details (req1 §Required implementation details)

### Data format

| req1 | implementation |
|---|---|
| JSONL for raw trajectory logs | `append_jsonl` / `read_jsonl` in `src/utils/io.py` |
| CSV/Parquet for metric tables | `write_csv` / `write_parquet` in `src/utils/io.py`; embeddings metadata is parquet, metrics are CSV |
| Raw generation record with `experiment_id`, `run_id`, `step`, `context_before`, `output_text`, `context_after`, `observable_type` | see §Phase 2 step record mapping above (note: `observable_type` lives in the embeddings metadata, not the raw step record) |

### Reproducibility

| req1 must-save | implementation |
|---|---|
| config copy | `save_config_snapshot` writes `data/<exp_id>/config.yaml` |
| model names | inside the config snapshot (`generation_model`, `embedding_model`) and per-step record (`model`) |
| timestamps | `timestamp` field added to every step record |
| seeds if used | `cfg.seed` in snapshot; `set_global_seed(cfg.seed)` at start of `cmd_run` |
| exact observable serialization settings | `rolling_window_k`, `context_tail_chars` in snapshot; separator `ROLLING_SEP` is a module constant |

### Error handling

| req1 | implementation |
|---|---|
| API retries | `_is_retryable` + exponential backoff in `src/api/generator.py` and `src/api/embedder.py` |
| partial resume | `manifest.json` tracks per-run completion; `cmd_run` skips completed entries; `resume` is a CLI alias for `run` |
| skipped failed runs with logging | `cmd_run` wraps each trajectory in try/except, marks `"failed"` on exception, continues |
| checkpointing after each trajectory | `write_json(manifest_path, manifest)` after each successful or failed run |

### Performance

| req1 | implementation |
|---|---|
| batch embeddings | `embed_texts(..., batch_size=128)` chunks input; 128 strings per API call |
| trajectories parallelized cautiously | `parallel_trajectories` config field exists but is **not currently wired** — parallelism is achieved by launching multiple background CLI processes (see operator experiment in REPORT2) |

---

## Minimal first experiment (req1 §Minimal first experiment)

| req1 spec | actual `exp_default` |
|---|---|
| 3 prompt families | ✓ (reflective, story, conceptual) |
| 10 initial conditions each | scaled to **5 per family** in default config to fit minimal milestone cost budget |
| 5 runs each | scaled to **3 per IC** |
| 30 steps | scaled to **15 steps** |
| 3 observables | ✓ |
| PCA-2 and PCA-20 | `pca_dims: [2, 10]` (20 enabled in v2 configs) |
| recurrence + dwell + basin | ✓ |
| 2 baselines | `no_feedback` only in default; `time_shuffled` added post-REPORT1 |

Scale-down was intentional to stay under ~$0.10 and ~1h for the first validation run. The full-scale version is `exp_long` (40 steps × 3 ICs × 3 runs).

---

## Prompt families (req1 §Prompt families)

| req1 example | in configs |
|---|---|
| open-ended reflective prompts | `reflective` family in every config |
| story continuation prompts | `story` family |
| conceptual/philosophical prompts | `conceptual` family |
| instruction-following prompts | **not included** — deemed out of scope for an attractor experiment |

### Constraints

| req1 | implementation |
|---|---|
| prompt families saved in config or data files | `prompt_families: [...]` in every YAML |
| no prompt text hardcoded deep in code | verified — `rg` of `src/` finds no literal prompt strings except test fixtures |

---

## Suggested CLI commands (req1 §Suggested CLI commands)

| req1 command | implementation |
|---|---|
| `python -m src.main run --config …` | `src/main.py::main` → `cmd_run` |
| `python -m src.main embed --config …` | `cmd_embed` |
| `python -m src.main analyze --config …` | `cmd_analyze` |
| `python -m src.main report --config …` | `cmd_report` |
| `python -m src.main all --config …` | sequentially calls run → embed → analyze → report |
| `python -m src.main resume --config …` | alias for `run` (manifest-driven skip) |
| `python -m src.main baseline --config …` | alias for `run` — baselines generate as part of `run` phase |
| (extra) `python -m src.main compare --configs a.yaml b.yaml …` | `cmd_compare` — cross-condition summary |

---

## Tests (req1 §Tests)

| req1 test category | files |
|---|---|
| clipping behavior | `tests/test_context.py` |
| rolling-window observable | `tests/test_observables.py`, `tests/test_observables_rolling_k.py` |
| context-tail extraction | `tests/test_observables.py` |
| recurrence detection | `tests/test_recurrence.py` |
| dwell calculation | `tests/test_dwell.py` |
| basin score computation | `tests/test_basin.py` |
| one complete tiny trajectory run (integration) | `tests/test_integration.py` — monkeypatches `generate_step` and `embed_texts`, runs full `all` pipeline |
| one embedding batch (integration) | covered inside `test_integration.py` |
| one PCA analysis (integration) | same |
| one end-to-end report on toy data (integration) | same (writes `report.md` and asserts content) |

Extras added over time:
- `test_context_full.py` — fixed-tail observable
- `test_basin_entry.py`, `test_late_recurrence.py`, `test_exit_return.py`, `test_bootstrap.py` — v2 metrics
- `test_operators_context.py`, `test_operators_periodicity.py`, `test_operators_dispersion.py` — operator module

Total: **57 tests pass** as of the last run.

---

## What the coding agent should avoid (req1 §What to avoid)

| req1 prohibition | compliance |
|---|---|
| do not rely on hidden chat state as experimental state | `store=False` on every `responses.create` call in `src/api/generator.py`; no `previous_response_id` is ever passed |
| do not mix different clipping rules in one run | `clip_rule` is a single config field; passed once per run |
| do not fit PCA separately per trajectory | PCA is fit in `cmd_analyze` on the full `(N, 1536)` matrix per observable |
| do not judge support only from 2D plots | classifier signal `robust_non_pca2_space` explicitly requires non-PCA-2 evidence; report structure demotes PCA-2 to visualization |
| do not use only one observable | classifier signal `robust_across_two_observables` enforces multi-observable requirement |
| do not skip baselines | pipeline generates `no_feedback` alongside recursive; time_shuffled is post-hoc automatic |

---

## Success criterion (req1 §Success criterion)

| req1 criterion | status |
|---|---|
| 1. reproducible recursive trajectories | ✓ (manifest + frozen config + per-step JSONL log) |
| 2. embedding datasets for multiple observables | ✓ (one subdir per observable) |
| 3. PCA projections | ✓ (2, 10, 20) |
| 4. recurrence/dwell/basin statistics | ✓ |
| 5. baseline comparisons | ✓ |
| 6. automatic report stating support level | ✓ |

---

## Build order (req1 §Final instruction for the coding agent)

| req1 build-order step | actual implementation order |
|---|---|
| 1. config + trajectory runner | `src/config.py` + `src/core/{context,trajectory}.py` |
| 2. OpenAI generation | `src/api/{openai_client, generator}.py` |
| 3. observables | `src/core/observables.py` |
| 4. embeddings | `src/api/embedder.py` |
| 5. PCA | `src/analysis/pca.py` |
| 6. recurrence | `src/analysis/recurrence.py` |
| 7. dwell | `src/analysis/dwell.py` + `clustering.py` |
| 8. basins | `src/analysis/basin.py` |
| 9. baselines | `src/core/baselines.py` + `time_shuffled` logic in `cmd_analyze` |
| 10. reporting | `src/reports/{summary,plots}.py` + `cmd_report` |

Followed verbatim.

---

## Additions beyond req1 scope

The following were added during the session in response to findings; not in the
original spec but documented here for completeness:

- **t-SNE for visualization and optional metric space** — `src/analysis/tsne.py`
- **v2 metrics** — basin_entry, late_recurrence, exit_return, bootstrap CIs, permutation tests — `src/analysis/{basin_entry,late_recurrence,exit_return,bootstrap}.py`
- **Two-axis classifier (H1a convergence vs H1b recurrence)** — `src/reports/summary.py::classify_two_axis`
- **`context_full` observable (fixed-size tail)** — for exp_noclip
- **Cross-condition comparison CLI** — `cmd_compare` in `src/main.py`
- **Debug tool for inspecting API message flow** — `src/utils/dump_messages.py`
- **Operator-regime follow-up experiment** — `src/experiments/operators/*` (isolated module); added periodicity, dispersion metrics, three-axis classifier — see REPORT2.md
- **Batch API + Evals wrappers** — `src/api/{batch_jobs,evals_runner}.py` (from req2; unused so far)

None of these break req1 compliance; all are additive.
