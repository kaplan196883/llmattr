# REPORT 1 — Setup and Results for `exp_default` (15-step trajectories)

**Date:** 2026-04-23
**Model under test:** `gpt-4o-mini`
**Embedding model:** `text-embedding-3-small` (1,536-dim, L2-normalized)
**Data directory:** `data/exp_default/`
**Next experiment in flight:** `exp_long` (40 steps/run) — see §7.

## 1. Hypothesis

> **H1.** In a bounded append-only recursive LLM loop, there exist endogenous
> attractor-like regimes that become observable in a suitable representation
> space.

The loop:

```
Y_t ~ P_theta(. | X_t, N)
X_{t+1} = clip(X_t || Y_t)
```

- `clip` = deterministic tail-char truncation at 12,000 chars
- No server-side conversation state; `store=False` on every Responses call
- Each step resends the full visible client-side context

## 2. Experimental setup

### 2.1 Design

| axis | value |
|---|---|
| prompt families | 3 (`reflective`, `story`, `conceptual`) |
| initial conditions per family | 5 |
| runs per initial condition | 3 |
| steps per run | 15 |
| regimes | `recursive` (main) + `no_feedback` (baseline) |
| total generated trajectories | 90 |
| total generated steps | **1,350** |
| wall time (generation) | ~64 min |
| OpenAI cost (gen + embed) | < $0.10 |

### 2.2 Generation parameters

- `temperature = 0.8`, `top_p = 1.0`, `max_output_tokens = 120`
- Developer prompt: "Continue the text naturally. Do not summarize or explain."
- Identical user message = full serialized `X_t`

### 2.3 Observables embedded per step

- `output` — `Y_t` only
- `rolling_k3` — `Y_{t-2} || Y_{t-1} || Y_t` joined by `<SEP>`
- `context_tail` — last 4,000 chars of `X_{t+1}`

Each observable is embedded jointly across all 1,350 steps → three (1350, 1536) matrices.

### 2.4 Analysis spaces

- **raw** — 1,536-dim unit-vector embeddings (cosine distance)
- **pca2**, **pca10** — PCA fit *jointly* per observable (never per-trajectory)
- **tsne2** — PCA-50 pre-reduction → t-SNE to 2D, `perplexity=30`, `random_state=42`

### 2.5 Baselines

- `no_feedback` — every step sends the original X₀ instead of the recursive context. Stationary sampler.
- `time_shuffled` — post-hoc: for each recursive trajectory, shuffle the order of points (and their cluster labels) and recompute metrics. Proper **temporal null**: same point cloud, destroyed dynamics.

## 3. Metrics

| metric | definition | spaces used |
|---|---|---|
| **recurrence rate** | fraction of pair indices (s,t) with \|z_s − z_t\| < ε and \|t − s\| > τ=3 | raw, pca2, pca10, tsne2 |
| **dwell** | mean length of contiguous runs of the same cluster label | pca10, tsne2 |
| **basin score** | fraction of runs from the same IC that occupy the dominant late-time cluster by step ≥ 0.7T | pca10, tsne2 |

Epsilon: 0.15 in raw/PCA (cosine/euclidean), scale-relative (`0.08 × std(coords)`) in t-SNE to account for the arbitrary scale.

## 4. Four analysis iterations on the same 1,350 steps

### Iteration 1 — DBSCAN (eps = 0.35, min_samples = 4)

**Result:** all 1,350 points collapsed into one cluster for every observable.

```
cluster_occupancy_output_pca10.csv   →  0: 1350
cluster_occupancy_rolling_k3_pca10   →  0: 1350
cluster_occupancy_context_tail_pca10 →  0: 1350
```

**Consequence:** dwell = 15.0 everywhere (entire trajectory in one cluster);
basin = 1.0 everywhere (only one cluster to converge to). Both signals
trivially positive. Recurrence still meaningful but baseline-dominated.

Classification: `weak_support` — driven by trivial basin. Not informative.

**Lesson:** DBSCAN eps must be tuned to the *embedding* scale. For L2-normalized
embeddings projected to PCA-10, eps = 0.35 is too coarse by ~4×.

### Iteration 2 — KMeans (n_clusters = 8)

**Result:** 8 balanced clusters per observable, e.g. for `output`:

```
0:152 1:158 2:257 3:118 4:194 5:125 6:171 7:175
```

**Recurrence** (no_feedback = only baseline in this iteration):

| observable | space | recursive | no_feedback | Δ |
|---|---|---:|---:|---:|
| output | pca10 | 0.026 | 0.401 | −0.38 |
| output | raw | 0.000 | 0.206 | −0.21 |
| rolling_k3 | pca10 | 0.088 | 0.804 | −0.72 |
| rolling_k3 | raw | 0.056 | 0.795 | −0.74 |
| context_tail | pca10 | 0.154 | 0.664 | −0.51 |
| context_tail | raw | 0.362 | 0.810 | −0.45 |

**Dwell (pca10):**

| observable | recursive | no_feedback |
|---|---:|---:|
| output | 4.99 | 15.00 |
| rolling_k3 | 10.39 | 15.00 |
| context_tail | 11.25 | 15.00 |

**Basin score (pca10):** 41/45 (family, IC) pairs converged 3/3 runs; 4/45
converged 2/3. Mean 0.93.

Classification: `weak_support`. Signals: basin=yes, dwell=no, recurrence=no,
robust=no.

**Problem:** `no_feedback` is a degenerate *super-attractor*. Re-sending X₀
every step → outputs cluster tightly around a single stationary distribution
→ trivially high recurrence (0.4–0.8) and maximal dwell (15.0). The recursive
regime is a *weaker* attractor in absolute terms but is not trying to
out-attract a stationary sampler. Wrong A/B comparison.

### Iteration 3 — Added t-SNE as metric space

**Recurrence in t-SNE space:** regime gap shrinks vs PCA-10:

| observable | recursive | no_feedback |
|---|---:|---:|
| output | 0.194 | 0.432 |
| rolling_k3 | 0.307 | 0.490 |
| context_tail | 0.378 | 0.396 (nearly tied) |

**Dwell in t-SNE clusters:** same pattern as PCA-10 (baseline pinned at 15.0,
recursive 9.3–15.0 depending on observable).

**Basin in t-SNE:** every (family, IC) pair converged 3/3 runs for every
observable. **Strongest basin signal of any space.**

**Visual:** t-SNE plots show the cleanest structure of any space:
- `tsne_*_by_prompt_family.png` — three well-separated regions, with ~5 tight sub-clusters inside each (one per initial condition).
- `tsne_*_by_regime.png` — **no_feedback forms point-like centroids**; **recursive forms connected filaments** threading through and around them. This is the key qualitative finding: baseline = fixed points, recursive = trajectories flowing through a structured landscape.

Classification: still `weak_support` (same baseline-choice issue).

### Iteration 4 — Added `time_shuffled` as proper temporal null

`time_shuffled`: for each recursive trajectory, shuffle the point order and
recompute. Same point cloud, same cluster memberships, but temporal structure
destroyed. This is the null that tests whether observed structure comes from
dynamics vs from the static point distribution.

**Dwell (pca10) — time_shuffled as null:**

| observable | recursive | time_shuffled | effect |
|---|---:|---:|---|
| output | 4.99 | ~1–2 | **positive** |
| rolling_k3 | 10.39 | ~1–2 | **positive** |
| context_tail | 11.25 | ~1–2 | **positive** |

Dwell is now clearly above the temporal null in all three observables and all
clustering spaces — consistent with clusters persisting for multiple
consecutive steps.

**Recurrence — time_shuffled as null:**

| observable | space | recursive | time_shuffled |
|---|---|---:|---:|
| rolling_k3 | pca10 | 0.088 | **0.279** |
| context_tail | pca10 | 0.154 | **0.396** |
| rolling_k3 | raw | 0.056 | **0.287** |
| context_tail | tsne2 | 0.378 | **0.565** |

**Recurrence is LOWER in the recursive regime than in its time-shuffled
twin for every observable and every space.**

This is not a bug — it is the diagnostic. A smooth drifting trajectory has
high temporal continuity (nearby-in-time → nearby-in-space), so the
`|t−s| > τ` locality filter excludes many of the close pairs, driving
recurrence down. Shuffling the time order breaks the continuity and exposes
the underlying point-cloud similarity. A true *recurrent* attractor would
show recursive ≥ time_shuffled (the trajectory revisits neighborhoods beyond
what the point cloud alone predicts).

**Basin:** unchanged (near-perfect convergence; basin does not have a
natural time_shuffled null).

**Final classifier output:**

```
Classification: weak_support
  recurrence_above_baseline: no    (recursive < time_shuffled — drift, not orbit)
  dwell_above_baseline:     yes    (recursive >> time_shuffled)
  basin_convergence_positive: yes  (mean 0.93–1.00 across spaces)
  robust_across_two_observables: yes
  robust_non_pca2_space: no
```

## 5. Interpretation

The 15-step experiment produces a **coherent three-part picture**:

1. **Strong basin structure.** Same IC → same late-time cluster, nearly 100%
   of the time. Different ICs → different basins. This is attractor-like
   *convergence*.
2. **Strong dwell.** Once inside a cluster, trajectories stay there for
   multiple consecutive steps before transitioning. This is
   attractor-like *persistence*.
3. **Negative recurrence.** Trajectories do not orbit — they drift
   monotonically toward their basin and then dwell. No evidence of periodic
   or quasi-periodic return within 15 steps.

In dynamical-systems terms: the observed behavior is consistent with
**convergence to fixed-point-like regions**, not with **limit cycles or
strange attractors**. H1 is literally true ("attractor-like regimes") in the
convergence sense, but the orbit-style recurrence predicted by some readings
of H1 is absent *at this trajectory length*.

## 6. Limitations

1. **15 steps is short.** By the time a trajectory reaches its basin, only a
   few steps remain to demonstrate orbiting. Short trajectories cannot
   distinguish "drifting toward a basin" from "orbiting inside it".
2. **`temperature = 0.8`.** Warmer temperatures would force exploration
   *inside* the basin and potentially expose recurrence.
3. **Fixed `max_output_tokens = 120`.** Context grows slowly relative to the
   12,000-char clip limit, so the `context_tail` observable is barely
   affected by clipping within 15 steps.
4. **Single generation model.** Basin geometry may be model-specific.
5. **Classifier uses a single cut-point per signal.** No statistical tests
   of the effect sizes (bootstrap CI, permutation p-values).
6. **t-SNE metric space.** t-SNE distorts global distance. Using it for
   recurrence required a scale-relative epsilon, but the absolute numbers
   are not comparable across t-SNE fits. Results are used for consistency
   checking, not for magnitude claims.

## 7. Next experiment — `exp_long`

Configuration (running as of this writing):

| axis | value |
|---|---|
| experiment_id | `exp_long` |
| steps_per_run | **40** (up from 15) |
| initial_conditions_per_family | 3 (down from 5) |
| runs_per_condition | 3 |
| families | 3 |
| regimes | recursive + no_feedback + time_shuffled(post-hoc) |
| total generated steps | 40 × 54 = **2,160** |
| estimated wall time | ~100 min |

**Hypothesis under test:** with longer trajectories, once the basin is
reached (by ~step 10 in `exp_default`), the remaining 30+ steps should
exhibit recurrence *inside* the basin if H1's stronger ("orbiting") reading
holds. If instead the trajectories continue to drift or collapse toward a
fixed point, recurrence will remain below the time_shuffled null and H1's
convergence-only reading will be confirmed.

## 8. Artifacts

```
data/exp_default/
├── config.yaml                              # frozen config snapshot
├── raw/
│   ├── steps.jsonl                          # 1,350 step records
│   └── manifest.json                        # run-level completion status
├── embeddings/{output,rolling_k3,context_tail}/
│   ├── embeddings.npy                       # (1350, 1536) float32, L2-normalized
│   └── metadata.parquet                     # trajectory identity per row
├── metrics/
│   ├── pca_{2,10}_<obs>.csv                 # projections with metadata
│   ├── pca_*_explained_variance.csv
│   ├── pca_*_model.npz                      # components + mean
│   ├── tsne_<obs>.csv                       # 2D t-SNE + cluster labels
│   ├── clusters_<obs>_<space>.csv           # per-row cluster assignment
│   ├── cluster_occupancy_<obs>_<space>.csv  # per-cluster counts
│   ├── recurrence.csv                       # per-run per-space per-regime
│   ├── dwell.csv                            # per-cluster per-run
│   ├── basin.csv                            # per (family, IC) per observable
│   └── explained_variance.json
├── reports/
│   ├── report.md                            # auto-generated
│   └── plots/                               # 42 PNGs: PCA, t-SNE, dists, basin
└── run.log
```

Report and plots are regenerable from cached embeddings via
`python -m src.main analyze --config configs/default_tuned.yaml`
followed by `report`. Generation does not need to be re-run to try different
clustering or metric settings.

## 9. Takeaways for the experimental pipeline itself

- **Cluster tuning matters more than model choice** at this stage. A badly
  tuned DBSCAN eps produces trivially-positive basin and dwell with no
  signal content. KMeans with fixed k was more robust for a first pass.
- **Baseline choice is load-bearing.** `no_feedback` is the wrong null for
  recurrence/dwell because it constructs a degenerate stationary sampler.
  `time_shuffled` is the correct temporal null; enable it by default.
- **Visual evidence ran ahead of the classifier.** The t-SNE plots showed
  a striking qualitative difference between regimes (point-like centroids
  vs flowing filaments) before the quantitative classifier had enough
  signal to upgrade the verdict.
- **The four-label classifier is honest but crude.** It cannot distinguish
  "attractor as basin" from "attractor as limit cycle" — both would satisfy
  H1 literally. A future version should separate convergence (basin, dwell)
  from recurrence (orbit), and report them as two axes rather than one
  classification.
