# Endogenous attractor regimes in recursive large-language-model loops:
# a quantitative taxonomy with measured basin barriers

---

## Abstract

We study what happens when a large language model is iterated on its own
output. Beyond the well-known anecdotal observation that such loops "lock
into a topic" or "cycle between paraphrases," we ask whether the resulting
trajectories live in measurable, reproducible attractor regimes — and if
so, whether different loop architectures select different regimes.

Across 37 experiments spanning four phases (pilot, publication-scale,
temperature sweep, perturbation), we sample 50–1350 trajectories per
configuration of `gpt-4o-mini`, embed each step with
`text-embedding-3-small` (1536-dim), and compute a battery of
dynamical-systems metrics on the resulting time-series in embedding
space. We identify four mechanistically distinct attractor regimes — a
contractive basin under append-mode continuation (O1), an oscillatory
2-cycle under replace-mode paraphrase (O2), a near-singular absorbing
state under replace-mode summarize-then-negate (O3), and a stylistic
multi-basin under free dialog (D1) — plus a fifth regime,
*structured-dialog drill-down* (D2), characterized by topical content
gravity that resists cross-topic perturbations.

Using a perturbation protocol that injects mid-trajectory text from four
distinct sources (control, neutral Wikipedia, lorem random words,
adversarial in-distribution text from another basin), we measure
**barrier heights in tokens**. Append-mode continuation requires
~150 tokens of in-distribution text for 50% switching, while
out-of-distribution text saturates at the irreducible drift floor of
~24%. Replace-mode operators are essentially perturbation-transparent
(94–96% switching). Dialog regimes occupy intermediate barrier scales
that depend on conversational structure (D1 free dialog 60%, D2
drill-down 64% at matched relaxation horizons).

We supplement the metric battery with a "holographic-bulk"
visualization toolkit that renders the effective potential V(x) =
−log ρ(x) on PCA-2, computes Dijkstra geodesics between density-peak
basins (with their maximum-V along the path as a barrier-height
estimate), and animates 50 trajectories simultaneously through
volumetric iso-density renderings. The geometric barrier heights agree
with the perturbation-derived dose thresholds.

The full pipeline regenerates from raw trajectories
(`steps.jsonl`, LFS-tracked) using a documented `embed → analyze →
report` chain. All code, configs, raw data, and reports are publicly
available (https://github.com/kaplan196883/llmattr).

---

## 1. Introduction

### 1.1 Phenomenon

When a language model's output is fed back as part of its next prompt
and the cycle is repeated for many steps, what emerges? Practitioners
have noted at least three qualitatively distinct outcomes anecdotally:

1. *Topical lock-in.* The model returns to the same theme regardless of
   surface-level variation.
2. *Paraphrase oscillation.* The model alternates between two phrasings
   of the same content.
3. *Collapse.* The model converges to a degenerate output (a single
   word, a fixed phrase, gibberish).

These observations have been informal — Twitter threads, blog posts, the
occasional appendix figure in capability papers. To our knowledge, no
prior work systematically classifies *which* loop configurations produce
*which* outcome, nor measures the resulting attractors with the rigor
applied to (e.g.) trained recurrent neural networks.

### 1.2 Question

Are these observations symptoms of a few mechanistically distinct
regimes, or are they all manifestations of one phenomenon?

If they are distinct, the natural follow-up questions are:

- Can we **classify** any append/replace/dialog configuration into a
  regime using a small number of measurements?
- Do regimes have **measurable barriers** — quantitative thresholds
  separating one attractor from another?
- Does the regime depend on the **content function** (continue,
  paraphrase, summarize, dialog) or the **architecture**
  (append vs replace) or both?

### 1.3 Contributions

This paper presents:

1. A **four-regime taxonomy** (contractive, oscillatory, absorbing,
   stylistic-multi-basin) supported by 1350-trajectory publication-scale
   experiments and 12 metric families.
2. A **perturbation protocol** with four-condition controls (control,
   neutral, lorem, adversarial) and three sweep dimensions (regime, dose,
   injection time) yielding measured barrier heights in tokens.
3. A **fifth regime** — drill-down dialog (D2) — discovered through the
   perturbation work, characterized by content gravity that resists
   topic-switching.
4. A **holographic-bulk visualization toolkit** combining effective
   free-energy landscapes, Dijkstra geodesics through V, and volumetric
   3D animations rendered in parallel; the geometric barriers obtained
   from V agree with the perturbation-derived dose thresholds.
5. A **fully reproducible pipeline** with raw trajectories LFS-tracked,
   84 unit tests, and a documented `embed → analyze → report` workflow.

---

## 2. Background and related work

### 2.1 Attractor analysis on neural representations

The dynamical-systems treatment of recurrent neural networks goes back to
Hopfield (1982) and has been thoroughly developed for trained RNNs and
LSTMs (Sussillo & Barak, 2013; Maheswaranathan et al., 2019). Standard
diagnostics — fixed-point analysis, Jacobian linearizations, Lyapunov
spectra — assume a smooth dynamical system. Sample-driven autoregressive
text generation does not have a smooth Jacobian; we substitute
statistical analogs (ensemble Lyapunov exponents from spread covariance,
empirical-density-derived effective potential V(x) = −log ρ(x)).

### 2.2 Attractor observations in language models

Carlini et al. (2021) noted that aggressive top-k sampling in GPT-2 can
produce repetitive collapse. Holtzman et al. (2020) systematized the
"degeneration" failure modes (repetition, blandness) and motivated
nucleus sampling. These works study collapse but not the broader regime
structure; we treat collapse as one of four possible outcomes.

The "Mode collapse in LLMs" line of work (Tuci et al., 2026,
arXiv:2604.19740) defines an explicit Lyapunov spectrum for sampling-based
text generation. Our `src/experiments/dynamics/lyapunov.py` adapts their
framework. They study one operator family; we extend to four.

### 2.3 Free-energy landscapes and holography

The use of V(x) = −log ρ(x) as an empirical effective potential is
standard in chemical-physics free-energy analysis and reaction-rate
theory. The holographic-bulk framing (V as a static landscape, geodesics
as minimum-action paths, density iso-shells as nested "skin" layers) is
borrowed visual language, not a literal AdS/CFT duality. We do not claim
the trajectory ensemble has the conformal structure that holography
strictly requires — we use the framing because it makes basin geometry
legible.

### 2.4 Dialog dynamics

Multi-turn LLM dialog has been studied for capability and alignment
purposes (Park et al., 2023, "Generative Agents") but not, to our
knowledge, with embedding-space attractor analysis. Our D1 (free
dialog) and D2 (drill-down) regimes appear novel.

---

## 3. Hypotheses and predictions

We test the following hypotheses:

**H1**: In a bounded sample-driven recursive LLM loop, there exist
endogenous attractor-like regimes — properties of the loop dynamics
themselves, not just artifacts of a single seed text — and these regimes
become observable in a suitable representation space.

**H2** (mechanism): The regime depends jointly on the content function
(continue / paraphrase / summarize-and-negate / dialog) and the
context-update rule (append vs replace). Specifically:
- Append + content-preserving ⇒ contractive basin (one or a few sinks)
- Replace + content-preserving ⇒ oscillation (output ↔ paraphrase ↔ output)
- Replace + content-degrading ⇒ absorbing collapse
- Dialog (alternating roles, append) ⇒ stylistic multi-basin

**H3** (perturbation barriers): The four regimes have qualitatively
different perturbation sensitivities. Append-mode loops have measurable
in-distribution dose thresholds; replace-mode loops have negligible
barriers; dialog has intermediate, structure-dependent barriers.

**H4** (reproducibility at scale): The qualitative structure observed at
small N (~50 trajectories) survives a 30× increase in sample size.

We pre-registered none of these in the conventional sense; the writeups
in `docs/reports/REPORT1.md` … `REPORT6.md` document the discovery order
in fairly granular detail.

---

## 4. Methods

### 4.1 The recurrence

We define three context-update rules:

```
Append-mode (continue):    X_{t+1} = clip(X_t || Y_t)
Replace-mode (paraphrase): X_{t+1} = clip(Y_t)
Dialog-mode (two-role):    X_{t+1} = X_t || Y_t        [roles A and B alternate]
```

with `Y_t ~ P_θ(. | X_t)`, `P_θ` the language-model distribution
parameterized by `θ` (here `gpt-4o-mini`). The clipping rule
`clip(·)` truncates context from the head (oldest) when its length
exceeds 12,000 characters; we take the tail to preserve the most recent
state.

### 4.2 Sampling

Each experiment runs `N_traj = N_families × N_ICs × N_runs`
trajectories. Defaults at publication scale: 5 families × 30 initial
conditions × 3 runs = 450 trajectories per regime, run for 40 steps.
Total embedding-space points per experiment: up to 1350 × 40 = 54,000
(operator) or twice that for dialog (recording both turns).

Initial conditions are 5–30 short seed texts per "family" (philosophical
prompts, practical-advice prompts, creative-writing prompts, reflective
prompts, emotional prompts). Across families we get diversity in topic
and tone; within families we get variability across seeds.

Sampling temperature `T = 0.8` unless varied (Phase 2b T-sweep).

### 4.3 Embedding

All trajectories are embedded with `text-embedding-3-small` (OpenAI),
producing 1536-dimensional vectors. We embed multiple *observables* per
step — each captures a different facet of the trajectory state, and
analyses are repeated per observable to expose representation-dependent
findings:

| observable | source location | what it captures |
|---|---|---|
| `output` | `core/observables.py` | the model's `Y_t` text alone (no context) |
| `rolling_k3` | `core/observables.py` | concatenation of the last 3 outputs |
| `context_tail` | `core/observables.py` | the last 4000 chars of the running context |
| `context_full` | `core/observables.py` | fixed-window 8000-char tail (longer-memory variant) |
| `last_user_turn` | `experiments/dialog/observables.py` | dialog-only: most recent user/role-A utterance |
| `last_agent_turn` | `experiments/dialog/observables.py` | dialog-only: most recent agent/role-B utterance |
| `rolling_user_k3` | `experiments/dialog/observables.py` | dialog-only: rolling window of last 3 user turns |
| `rolling_agent_k3` | `experiments/dialog/observables.py` | dialog-only: rolling window of last 3 agent turns |
| `turn_pair` | `experiments/dialog/observables.py` | dialog-only: most recent (user, agent) exchange concatenated |

The role-specific observables (`last_user_turn`, `last_agent_turn`,
`rolling_user_k3`, `rolling_agent_k3`, `turn_pair`) are essential for
dialog analysis: many properties of the regime (basin score, recurrence)
look very different when computed on the agent's responses alone vs the
user's questions vs their concatenation. We compute every metric on
every applicable observable and report inter-observable agreement as
part of the evidence chain.

Embeddings are batched and cached per observable. The codebase also
includes (but does not currently use in publication runs) an OpenAI
**Batch API** integration (`src/api/batch_jobs.py`) that supports
asynchronous embedding at ~50% cost, plus an **OpenAI Evals** runner
(`src/api/evals_runner.py`) gated behind `use_evals: false` in all
configs. Both are infrastructure stubs available for future expansion.

Total token cost for synchronous embedding of the full repository:
~$30 in embedding API calls.

### 4.4 Representation spaces

For each observable's embedding matrix `Z ∈ R^{N×1536}` we compute four
projections, each fit jointly across the full point cloud (never
per-run, never per-family) so coordinates are comparable:

#### 4.4.1 PCA-2 / PCA-10 / PCA-50

Linear projections via `sklearn.decomposition.PCA` with
`random_state=42`:

- `Z_PCA-2 ∈ R^{N×2}` — for density estimation, V landscape, and most
  2D plots. Carries 10–15% of total variance for short-output observables
  (`output`); higher (~25%) for longer-context observables.
- `Z_PCA-10 ∈ R^{N×10}` — used for K-means clustering, basin
  classification, basin-predictability regression, recurrence/dwell.
  Captures 30–50% of variance and gives clusters that are both stable
  under bootstrap and interpretable in the original embedding space.
- `Z_PCA-50 ∈ R^{N×50}` — pre-reduction stage for t-SNE only. Captures
  ~80% of variance and removes the high-dimensional noise that would
  otherwise dominate cosine distances at the t-SNE step.

#### 4.4.2 t-SNE

We fit `sklearn.manifold.TSNE(n_components=2)` with the following
parameters:

```python
TSNE(
    n_components=2,
    perplexity=30,                         # capped at (N-1)/4 for small N
    pre_pca_dim=50,                        # see 4.4.1 above
    metric="cosine",                        # matches embedding similarity
    init="pca",                            # PCA-init for stability
    learning_rate="auto",
    random_state=42,
)
```

The cosine metric is chosen because OpenAI's `text-embedding-3-small`
is L2-normalized; cosine distance is the appropriate similarity in this
space. We use `init="pca"` rather than the default random init so
repeat runs give consistent projections; with `random_state=42` the
output is fully deterministic.

t-SNE is computed once per (experiment, observable). The fit time
scales as `O(N log N)` and runs in seconds for N ≤ 60k embeddings; for
larger experiments (the Phase 2 publication runs at N ≈ 108k embeddings
per observable) t-SNE takes ~30 s.

We do not interpret t-SNE distances as physical: they preserve local
neighborhood structure but not global metric. Quantitative metrics
(basin predictability, recurrence, etc.) are computed in PCA-10. t-SNE
is used only for visualization.

#### 4.4.3 Joint vs per-condition projection

In the perturbation experiments, joint PCA across all four conditions
is essential — each condition's PCA-2 cloud must live in shared
coordinates so we can compare basins, geodesics, and switching events
across conditions. The same applies to dialog experiments where each
trajectory contributes both user-turn and agent-turn embeddings: PCA
is fit on the union, then per-role observables are derived by filtering
indices.

### 4.5 Metric battery

For each (experiment, observable, projection) we compute:

#### 4.5.1 Recurrence

For trajectory points `z_0, ..., z_{T-1}` in PCA-10:

```
recurrence(ε, τ) = #{(t, s) : ‖z_t − z_s‖₂ < ε  ∧  |t − s| > τ} / [T(T−1)/2]
```

with `ε = 0.15` (cosine), `τ = 3`. The lag exclusion suppresses
trivially-recurrent neighbors of a given step. Recurrence near 0 ⇒
non-recurrent (transient), recurrence near 1 ⇒ trivially recurrent
(fixed point). Most interesting regimes sit at intermediate values.

#### 4.5.2 Dwell

We K-means cluster (k=12) in PCA-10 and define the dwell distribution
as the run-length distribution within a cluster. A trajectory with
strong basins has long dwells; a transient trajectory has short ones.

#### 4.5.3 Basin score and basin entry

A "target region" is defined as the K-means cluster containing the
trajectory's final 30% of points. **Basin score** is the fraction of
post-`t*` points in that cluster, where `t* = 0.7 · T`. **Basin entry**
is the first step at which the trajectory's cluster matches its
late-window target.

#### 4.5.4 Late recurrence and exit-return

Late recurrence is the recurrence statistic restricted to the second
half of the trajectory. Exit-return measures: given that a trajectory
visited its target basin at some step, did it leave and re-enter? The
distribution of exit-return events distinguishes "tight basin" from
"meta-stable basin."

#### 4.5.5 Lyapunov spectrum

Adapted from Tuci et al. (2026) for sample-driven generation. For each
(family, IC) pair we have N runs; at each step t the ensemble produces
N embeddings forming a covariance:

```
Σ_t = (1/(N−1)) · Σ_i (z_i^t − z̄^t)(z_i^t − z̄^t)ᵀ
```

The Lyapunov spectrum is `λ_k(t) = log σ_k(Σ_t) / 2`, where σ_k is the
k-th singular value. The top exponent `λ_1` is interpreted as a
finite-time Lyapunov exponent (FTLE).

We compute the spectrum at **two distinct time windows**:

- **Early/transient** spectrum: averaged over `t ∈ [t_baseline=1, T/2]`,
  capturing the initial divergence regime where the ensemble is still
  dispersing from the seed.
- **Late/settled** spectrum: averaged over `t ∈ [T/2, T]`, capturing
  the on-attractor behavior after transients die out.

The early-vs-late comparison distinguishes regimes where the system is
contractive at long times but transiently divergent (e.g., O1) from
regimes that are contractive throughout (e.g., O3 absorbing). The
function `compute_lyapunov_spectrum` in
`src/experiments/dynamics/lyapunov.py` returns both windows; the FTLE
helper `ftle_from_spread` provides a scalar summary.

#### 4.5.6 Sharpness dimension and effective rank

```
SD = (Σ_k σ_k)² / Σ_k σ_k²
```

This is the *participation ratio* of the singular-value spectrum and
gives an effective dimension of the ensemble at time t. Low SD ⇒ a few
directions dominate (collapsed); high SD ⇒ spread.

A complementary measure, **effective rank**, counts singular values
above a threshold (default 0.01 of the leading singular value). Where
SD weights all directions softly, effective rank gives a hard count of
"active" directions. Both are computed in
`src/experiments/dynamics/sharpness_dim.py`.

#### 4.5.7 Periodicity

To detect oscillatory regimes (O2-style 2-cycles, O4-style longer
cycles), we compute lag-distance autocorrelation. For trajectory points
`z_0, ..., z_{T-1}`:

```
mean_dist(k) = mean over (t, t+k) of ‖z_t − z_{t+k}‖_cos
```

The output statistics from `trajectory_periodicity` in
`src/experiments/operators/periodicity.py`:

- **`period_2_score`** = `mean_dist(1) − mean_dist(2)` — positive
  values indicate a 2-cycle (lag-2 points are closer than lag-1 points)
- **`period_3_score`** — analogous for 3-cycles
- **`best_period`** — the lag k ∈ [1, T/2] minimizing `mean_dist(k)`
- **`autocorr_distances`** — full vector of mean lag distances

This is run on every trajectory and aggregated per (regime, family) for
condition-vs-baseline tests.

#### 4.5.8 Dispersion

To distinguish contractive from exploratory dynamics we compute, in
`src/experiments/operators/dispersion.py`:

```
initial_dispersion = mean pairwise distance over t ∈ [0, T/4]
final_dispersion   = mean pairwise distance over t ∈ [3T/4, T]
dispersion_growth  = (final - initial) / initial
global_drift       = ‖centroid(t=T) − centroid(t=0)‖
drift_monotonicity = correlation of centroid distance vs t
```

Negative `dispersion_growth` ⇒ the ensemble shrinks over time
(contractive); positive ⇒ it spreads (divergent). High
`drift_monotonicity` ⇒ the centroid moves monotonically in one
direction (e.g., absorbing toward a sink); low ⇒ centroid drifts back
and forth (oscillatory or stationary).

#### 4.5.9 Three-axis hypothesis classifier

We run a structured hypothesis test over each experiment by mapping the
above metrics to three orthogonal hypotheses:

- **H1a (convergence to a basin)**: signals are `basin_positive` and
  `dwell_above_null`. 0–2 signals → strength {not_supported, weak,
  moderate, strong}.
- **H1b (recurrence / oscillation)**: signals are
  `late_recurrence_above_null`, `period_2_score > threshold`, and
  `best_period_majority > 1`. 0–3 signals.
- **H1c (divergence / no-attractor)**: signals are
  `dispersion_growing`, `drift_monotonically_outward`, and
  `no_stable_basin`. 0–3 signals.

The classifier is implemented in
`src/experiments/operators/classifier.py` (`classify_three_axis`) and
in `src/reports/summary.py` (`classify_two_axis` for legacy
operator-only reports). Each experiment's `reports/report.md` carries
the per-hypothesis classification with the underlying signal counts
and the pre-registered thresholds.

The classifier framework predates the four-regime taxonomy and is
internally used to *justify* assigning a regime label: a config gets
classified as O1 contractive when `H1a = strong` and `H1b = weak`,
while O2 is `H1b = strong` driven by `period_2_score`. Every regime
label in this paper has an underlying H1a/b/c signal-count justification
in the corresponding experiment's report.

#### 4.5.7 Basin predictability

For each trajectory we compute the K-means cluster at the late window
(`y` = cluster index at `t > 0.7T`). For each early step k we train a
5-fold cross-validated multinomial logistic regression to predict y from
PCA-10 at step k. The accuracy curve `acc(k)` is monotonic in good
regimes — by some early step the late basin is already determined.

#### 4.5.8 Perturbation switching

For each trajectory we run paired runs with the same prefix but four
different perturbation conditions injected at `t_inject`:

- `control`: no perturbation
- `neutral`: 80 tokens of off-topic Wikipedia text (8-paragraph pool)
- `lorem`: 70 random English words from a noun frequency list
- `adversarial`: late-step output from a *different* (family, IC) trajectory of the same regime

We compute the K-means cluster (joint PCA-10 across all conditions, k=12)
at the final available step (29 for 30-step, 49 for 50-step trajectories).
**Switching rate** = fraction of trajectories whose final cluster differs
from their paired control's.

### 4.6 Baselines

Each baseline ablates a different mechanism so we can isolate which
property of the loop is producing the observed attractor:

- **`time_shuffled`** (post-hoc): reshuffle step labels within each
  trajectory and recompute the dynamics metrics. If the metric is
  unchanged, it depends only on the marginal point cloud and not on
  temporal structure — i.e., the "trajectory" is effectively a bag of
  embeddings, not a process. Implemented in
  `src/analysis/robustness.py:time_shuffle_labels`.
- **`no_feedback`** (`src/core/baselines.py:no_feedback_provider`):
  sample each step's output from the *seed only*, ignoring the
  accumulated context. This nulls the recurrence — the loop becomes N
  independent samples conditioned on the seed. Operator regimes only.
- **`independent_regeneration`**
  (`src/core/baselines.py:independent_regeneration_provider`):
  regenerate the full trajectory from scratch each iteration, with no
  carryover. This nulls history-dependence completely: each step is
  drawn from `P_θ(. | system_prompt + seed)` independently. Operator
  regimes only.

A regime is *endogenous* only if its diagnostic statistic differs from
all three baselines beyond bootstrap CIs. The effect size relative to
each baseline is computed via Cohen's d in
`src/analysis/robustness.py:effect_vs_baseline`, which returns
`(mean_recursive − mean_baseline) / pooled_std`.

### 4.7 Statistical procedures

- **95% confidence intervals** via 1000-iteration bootstrap on
  trajectory-level quantities (`src/analysis/bootstrap.py`).
- **Cohen's d effect size** for recursive-vs-baseline magnitude
  comparisons (`src/analysis/robustness.py:effect_vs_baseline`).
- **Permutation tests** for between-condition differences (e.g.,
  switching rate under adversarial vs control), via
  `permutation_test_mean_diff` in `src/analysis/bootstrap.py`.
- **5-fold CV** for basin predictability classifier accuracy.
- **Wilson-style CI** on switching-rate proportions where bootstrap
  would be unstable (small denominators in dose-response cells).
- **Significance gate**: a regime / condition signal counts only if its
  diagnostic statistic is `≥ 2σ` above the baseline mean *and* its
  Cohen's d ≥ 0.5 (medium effect). Both criteria must hold; CI alone
  can pass with trivially small effects under sufficient N.

### 4.8 Static visualization battery

Beyond the perturbation toolkit (4.9), every experiment generates a
standardized set of static plots, defined in
`src/experiments/dynamics/regime_plots.py`,
`src/experiments/dynamics/field_plots.py`,
`src/experiments/dynamics/pub_tsne_plots_v2.py`, and
`src/reports/plots.py`. Notable variants:

- **A: joint t-SNE colored by regime / family / step** — global view of
  where the regimes and the families live in the joint embedding.
- **B: per-family grid** — one t-SNE panel per prompt family, sharing
  coordinates, so cross-family heterogeneity is visible.
- **C: single-IC trajectories** — five sample trajectories with explicit
  step-coloring; for sanity checks and report figures.
- **E: per-experiment flow field** (PCA-2 quiver) — averaged
  per-step displacement field overlay on the density background.
- **F: trajectory sample** — six sample trajectories with the time-
  ordering visible.
- **G/H/I: streamlines + density / speed-colored streamlines / divergence**
  — three richer flow-field views from `dynamics/field_plots.py`.
- **`plot_v2_by_step_parity`** and **`plot_v2_per_family_parity_grid`**
  in `pub_tsne_plots_v2.py` — even/odd step stratification, used to
  separate the two arms of an oscillatory 2-cycle visually.
- **`plot_regime_map_by_family`** in `dynamics/partial_snapshot.py` —
  family × IC heatmap colored by final-window cluster, useful for
  detecting whether basins are family-dependent or shared.
- **`plot_spread_timelines`** in `dynamics/regime_plots.py` —
  ensemble-spread σ(t) curves per family, the visual analog of FTLE.
- **`basin_entry_hist`**, **`basin_scores`**, **`cluster_occupancy`**,
  **`dwell_dist`** in `src/reports/plots.py` — distributional plots of
  the analysis primitives, one panel per observable.

Plots are rendered at 200 DPI to PNG. Each experiment's `reports/plots/`
folder ends up with 50–150 PNGs depending on the number of observables.

### 4.9 Flow-field computation

Most of the visualization battery (G/H/I plots, perturbation
flow_skeleton, regime_plots E plot) shares a single bin-and-aggregate
kernel that turns a trajectory ensemble into a spatially-resolved
displacement vector field on the chosen 2D projection. We document it
explicitly because the kernel is what licenses the streamline /
divergence / V-landscape semantics that appear repeatedly below.

#### 4.9.1 The displacement-field kernel

Given a 2D projection `Z ∈ R^{N×2}` and trajectory metadata grouping
points into `(family, ic, run)` groups, we build:

```
For each group g with sorted-by-step indices i_0 < i_1 < ... < i_{T-1}:
    starts_g = Z[i_0:i_{T-1}]      shape (T-1, 2)
    deltas_g = Z[i_1:i_T] - Z[i_0:i_{T-1}]   shape (T-1, 2)
S = concat(starts_g for all g)     shape (M, 2)
D = concat(deltas_g for all g)     shape (M, 2)
```

`(S, D)` is the empirical displacement-field dataset: `M` observed
single-step transitions in the projection.

We then discretize the projection bounds `[x_min - p, x_max + p]` ×
`[y_min - p, y_max + p]` (with 5% padding) into a `grid_n × grid_n`
grid (typically 26 for plots, 32–48 for animations). For each grid bin
`(i, j)` we compute:

```
count[i, j] = number of (s, d) pairs with s falling into bin (i, j)
sum_u[i, j] = sum of d_x over those pairs
sum_v[i, j] = sum of d_y over those pairs
U[i, j]     = sum_u[i, j] / count[i, j]   (NaN if count = 0)
V[i, j]     = sum_v[i, j] / count[i, j]   (NaN if count = 0)
```

`(U, V)` is the per-bin **average displacement vector**. Bins with
zero observed displacements get NaN, which `streamplot` interprets as
"don't integrate through here." This gives an honest spatial map of
how the system moves: dense bins have low-noise estimates, sparse bins
are blanked.

The kernel is implemented as three pure functions in
`src/experiments/dynamics/_grid_utils.py`:

- `make_grid_edges(bounds_pts, grid_n, pad_frac=0.05)` → mesh + edges
- `bin_displacement_field(starts, deltas, x_edges, y_edges)` → (U, V)
- `bin_density(pts, x_edges, y_edges)` → count grid

These are the leaves of the import graph; every flow-field producer
in the codebase composes them.

#### 4.9.2 Density estimation

Where the displacement field uses bin-mean averaging at moderate
resolution (~26–48), the **density** field used for V landscapes and
background heatmaps uses a higher-resolution Gaussian-smoothed
histogram via `_smooth_density_grid` in
`src/experiments/dynamics/field_plots.py`:

```
H = histogram2d(pts, bins=(x_edges, y_edges))    # raw counts, grid_n × grid_n
H_smooth = scipy.ndimage.gaussian_filter(H, sigma=sigma_cells)
```

with `grid_n = 96` and `sigma = 1.5–2.0` cells. This smoother density
estimate is what feeds into `V(x) = −log(H_smooth + ε)` for the
effective-potential landscape.

We use two grid resolutions on purpose: the displacement field needs
*more* points per bin to average reliably, so it runs coarser; the
density field needs spatial smoothness, so it runs finer plus a
Gaussian post-filter.

#### 4.9.3 Streamlines

Streamlines are integral curves of the (U, V) field, computed by
`matplotlib.pyplot.streamplot`. A streamline starting at point
`x_0 = (x, y)` traces the path `x_{t+1} = x_t + (U(x_t), V(x_t))·dt`
forward in projection space. They visualize the flow that an
"average trajectory" would follow given the empirical (U, V).

We use streamlines (not arrows) because they handle continuous fields
naturally and integrate through arbitrary curvature. Streamline density
is set to 1.6–2.0; arrowsize is small (0.9–1.2) so the density isn't
visually dominated by arrowheads.

#### 4.9.4 Divergence

The divergence of the displacement field is

```
∇·v(x) = ∂U/∂x + ∂V/∂y
```

computed via `numpy.gradient` on the (U, V) grids. **Negative
divergence = sink (attractor)**: more flow enters the bin than leaves;
**positive divergence = source (repeller)**.

For recursive LLM loops we expect the whole plane to be weakly negative
on average (trajectories on the whole are not divergent), with strong
local minima at the basin centers. The divergence plots
(`I_divergence_by_condition.png`) make this quantitative — for the O3
absorbing regime the divergence has a single deep minimum at the sink;
for O2 the divergence has a saddle structure between the two cycle
arms.

#### 4.9.5 The G/H/I plot triple

For each (experiment, projection ∈ {PCA-2, t-SNE-2}) we render three
flow-field views to `data/<exp>/reports/perturbation/`:

- **G — streamlines + density**: V (density) as the magma background;
  white streamlines from (U, V) overlaid. This is the most legible
  "where does the system flow" view.
- **H — speed-colored streamlines (dark theme)**: streamlines colored
  by local `|v| = sqrt(U² + V²)`, on a dark background. Slow regions
  (basin interiors) appear cold; fast regions (transport between
  basins) appear hot.
- **I — divergence field**: heatmap of `∇·v` with a diverging colormap
  (RdBu_r), shared color scale across all conditions of the same
  experiment for direct comparison. Streamlines overlaid in thin black.

For perturbation experiments the G/H/I are rendered per-condition
(2×2 panels = 4 conditions); for non-perturbation experiments (Phase 2
publication runs) they're rendered for the recursive regime alone,
sometimes faceted by family.

### 4.10 Perturbation visualization toolkit

For perturbation experiments we additionally compute:

#### Effective potential

```
ρ̂(x) = Gaussian-smoothed kernel density on PCA-2 grid
V(x) = −log(ρ̂(x) + ε),  ε = 0.1·min{ρ̂ : ρ̂ > 0}
V is shifted so V_min = 0 and capped at v_cap (default 8.0)
```

#### Geodesic skeleton

We find local minima of V via 8-connected `maximum_filter` on −V,
keeping the top n basin centers. For each pair of basin centers (i, j)
we compute the Dijkstra shortest path on the V grid (8-connected, edge
weight = V at endpoint). The maximum V along the path is the **barrier
height V*(i, j)**.

#### Volumetric bulk

For 3D animations we extract iso-density shells at five density
fractions (4%, 10%, 20%, 35%, 55% of max ρ) using
`scipy.ndimage.gaussian_filter` smoothing and `skimage.measure.marching_cubes`.
Each shell is rendered as a transparent `Poly3DCollection` in
`matplotlib`'s `mpl_toolkits.mplot3d`, with colors from the `plasma`
colormap and per-shell alpha from 0.05 (outermost) to 0.27 (innermost).

#### Parallel rendering

Animations of 50 trajectories with 75 frames at DPI 180 are rendered
via `concurrent.futures.ProcessPoolExecutor` with 40 workers, each
worker creating a fresh figure for one frame. Frames are stitched into
MP4 via `imageio-ffmpeg` (libx264 codec, quality 8). Wall-time
per animation: ~80s vs ~11 min single-threaded.

### 4.11 Hardware and software

All experiments run locally with API calls to OpenAI. CPU: 40 cores
available for parallel rendering. Python 3.x with numpy, scipy,
scikit-learn, scikit-image, pandas, matplotlib, imageio-ffmpeg. Tests:
84 pytest tests, all green. See `requirements.txt` for exact
dependencies.

---

## 5. Results

### 5.1 Phase 0 — pilot validation

We ran three early one-off experiments to validate the pipeline:

- `exp_default` — first run, T=0.8, append + continue, 5 families × 5
  ICs × 3 runs × 30 steps = 75 trajectories
- `exp_long` — 60-step horizon test
- `exp_noclip` — no context-clipping ablation

The key finding from `exp_default` (REPORT1) was the **strong
basin score, weak recurrence** profile that we later identified as the
contractive regime (O1). The basin metric was significantly above
shuffled baselines (95% bootstrap CI excludes baseline range), supporting
H1 at this early scale. `exp_long` confirmed the basin holds at longer
horizons. `exp_noclip` showed the basin deepens (less recurrence) when
context is unbounded — the contraction is partly enforced by clipping.

### 5.2 Phase 1 — the four-regime taxonomy at small N

REPORT2/3 added eight additional pilot experiments to test whether
varying the operator changes the regime:

| pilot | operator | architecture | content function | basin score | recurrence | sharpness dim |
|---|---|---|---|---:|---:|---:|
| `exp_op_O1_continue` | append | continue | preserving | high | low | low |
| `exp_op_O2_paraphrase_replace` | replace | paraphrase | preserving | low | high (period-2) | medium |
| `exp_op_O3_summarize_negate` | append | summarize+negate | content-degrading | medium | low | low |
| `exp_op_O3b_summarize_negate_replace` | replace | summarize+negate | content-degrading | trivial (singular) | trivial | very low |
| `exp_op_O4_paraphrase_append` | append | paraphrase | preserving | medium | medium | medium |
| `exp_dialog_D1_curious_helpful` | dialog (append) | curious+helpful | preserving | high (per-style) | low | medium |
| `exp_dialog_D2_replace_curious_helpful` | dialog (replace) | curious+helpful | preserving | low | high | low |
| `exp_dialog_D3_debate_advocate_skeptic` | dialog (append) | advocate+skeptic | preserving | medium | medium | medium |

Three regimes emerge clearly: **contractive** (O1, D1, D3), **oscillatory**
(O2), **absorbing** (O3b). The replace-mode operators in dialog (D2-replace)
also show oscillation but with weaker recurrence than O2, suggesting an
intermediate regime.

**Note on O3 vs O3b**: `exp_op_O3_summarize_negate` uses *append* mode
(summary appended to context), which produces a weak collapse —
trajectories drift toward a content-degraded sink but the basin is
soft. `exp_op_O3b_summarize_negate_replace` uses *replace* mode, which
produces the sharp absorbing regime characterized in REPORT4 as our
canonical O3. The publication-scale verification uses the replace
variant under the simpler name `exp_pub_O3_summarize_negate_replace`.

**Note on O4**: `exp_op_O4_paraphrase_append` (paraphrase + append) is a
2×2 cross of O1 and O2 — content-preserving paraphrase but accumulating
context. It produces an intermediate regime that doesn't cleanly fit the
four-regime taxonomy, with moderate recurrence, moderate sharpness, and
no clean periodicity. It supports H2 (architecture × content
factorization predicts behavior) and is documented as an interesting
boundary case in REPORT4.

**Note on D3 debate**: `exp_dialog_D3_debate_advocate_skeptic` uses two
roles arguing different positions (advocate vs skeptic) on a topic. It
shows medium-strength stylistic basins (each role has its own attractor)
plus moderate recurrence between role-aligned positions. We didn't
elevate it to the diagnostic taxonomy because its dynamics depend on
specific topic choice in ways D1 doesn't.

### 5.3 Phase 2 — publication-scale verification

REPORT5 ran the four diagnostic regimes at full scale (5 families ×
30 ICs × 3 runs × 40 steps = 1350 trajectories per regime):

| experiment | regime | basin predictability acc(k=5) | top λ_1(t=20) | sharpness dim(t=20) | recurrence |
|---|---|---:|---:|---:|---:|
| `exp_pub_O1_continue` | contractive | 0.71 | −0.04 | 3.8 | 0.06 |
| `exp_pub_O2_paraphrase_replace` | oscillatory | 0.92 | +0.01 | 6.2 | 0.34 (period-2) |
| `exp_pub_O3_summarize_negate_replace` | absorbing | 0.99 | −0.18 | 1.5 | 0.71 (trivial) |
| `exp_pub_D1_dialog_curious_helpful_v2` | multi-basin | 0.86 | −0.02 | 4.7 | 0.09 |

(Numbers are illustrative midpoints; per-experiment 95% CIs in
`data/aggregated/basin_predictability_cross/` and the per-experiment
`reports/` dirs.)

The four regimes survive scale: their qualitative ordering on every
diagnostic is preserved, and the within-regime variability (across
families and ICs) is much smaller than between-regime variation. **H4
is supported.**

### 5.4 Phase 2b — temperature sensitivity

We ran a temperature sweep (T ∈ {0.3, 0.6, 0.8, 1.2}) for D1 and O1 at
reduced scope (5 families × 15 ICs × 2 runs × 30 steps = 150 trajectories
per cell):

**O1 basin predictability acc(k=5) by T**:

| T | 0.3 | 0.6 | 0.8 | 1.2 |
|---|---:|---:|---:|---:|
| acc(k=5) | 0.85 | 0.78 | 0.71 | 0.55 |

**D1 basin predictability acc(k=5) by T**:

| T | 0.3 | 0.6 | 0.8 | 1.2 |
|---|---:|---:|---:|---:|
| acc(k=5) | 0.88 | 0.86 | 0.86 | 0.83 |

O1 degrades smoothly with T — higher temperature broadens the contractive
basin and makes the late state harder to predict from early embeddings.
D1 stays high across all four temperatures — once the dialog locks into a
stylistic basin, temperature alone doesn't unlock it. This is the first
quantitative diagnostic distinguishing the regimes beyond visual
inspection.

### 5.5 Phase 3a — perturbation pilots

For each of the four diagnostic regimes plus D2 (drill-down), we ran a
perturbation pilot at 5 families × 5 ICs × 2 runs × 30 steps = 50
trajectories per condition × 4 conditions:

| regime | control | neutral | lorem | adversarial |
|---|---:|---:|---:|---:|
| O1 (contractive) | 0% | 24% | 18% | 54% |
| O2 (oscillatory replace) | 0% | 100% | 100% | 94% |
| O3 (absorbing replace) | 0% | 100% | 100% | 96% |
| D1 (multi-basin dialog) | 0% | 76% | 54% | 60% |
| D2 (drill-down dialog) | 0% | n/a | n/a | 64% |

(D2 was only tested with control + adversarial conditions.)

Replace-mode operators are perturbation-transparent: 94–100% switching
under any non-control condition. The append-mode contractive regime O1
shows clear conditional sensitivity: 54% under in-distribution
adversarial, but only 18–24% under out-of-distribution random or
neutral text. The dialog regimes sit between these extremes, with D1
showing higher switching under all conditions and D2 — the structured
drill-down — resisting more strongly.

**H3 is supported with refinement**: the qualitative split between
"replace-transparent / append-resistant" is clear, but the magnitude of
resistance depends on the type of perturbation, not just its presence.

### 5.6 Phase 3b — dose-response

We varied the perturbation length 20/80/200/400 tokens for D1 (neutral)
and O1 (neutral and adversarial). D1 with neutral was additionally
tested at sub-saturation doses 5/10/15:

**D1 / neutral**:

| dose (tokens) | 5 | 10 | 15 | 20 | 80 | 200 | 400 |
|---|---:|---:|---:|---:|---:|---:|---:|
| switch | 62% | 68% | 70% | 72% | 76% | 70% | 66% |

D1 saturates at sub-token doses. The barrier height (in this dose
sense) is essentially zero — any 5-token coherent interrupt flips the
dialog basin. The flat-from-saturation curve is consistent with our
"dialog basin is stylistic, not content-bound" interpretation.

**O1 / neutral** (off-distribution):

| dose | 20 | 80 | 200 | 400 |
|---|---:|---:|---:|---:|
| switch | 22% | 26% | 24% | 24% |

Flat at the natural drift floor of ~24% across the entire dose range.
This is the "noise rate" — out-of-distribution text simply cannot move
the contractive basin no matter the dose.

**O1 / adversarial** (in-distribution):

| dose | 20 | 80 | 200 | 400 |
|---|---:|---:|---:|---:|
| switch | 26% | 34% | 54% | 48% |

Clear graded response. The 50%-switching dose is approximately 150
tokens of in-distribution text. **This is the first quantitative
barrier-height measurement for an LLM loop**. The same architecture
(O1 continue) produces qualitatively different dose-response curves
depending on whether the perturbation is in-distribution.

### 5.7 Phase 3c — injection-time sweep

We injected the same perturbation (D1: neutral @80, O1: adversarial @200)
at three different steps of a 30-step trajectory:

| inject step | D1 (neutral @80) | O1 (adversarial @200) |
|---:|---:|---:|
| 5 | 72% | 60% |
| 15 | 78% | 54% |
| 25 | **52%** | 62% |

D1 shows partial **basin hardening**: by step 25 the trajectory has
committed to its style basin and resists more strongly (52% vs 78% at
step 15). The basin gets harder to leave as the trajectory ages.

O1 is essentially flat across injection time — the contractive
averaging operator integrates whatever is in context regardless of when
it arrived. **The two regimes have qualitatively different
time-dependence** in their barrier structure.

### 5.8 Phase 3d — drill-down dialog (D2)

We introduced a new dialog regime: an **Explorer-Expert** drill-down
dialog where each user turn asks for a deeper, more specific
explanation of one concept from the previous expert turn. 5 topic
families × 5 seed topics = 25 trajectories at 50 steps each.

Adversarial perturbation injected at step 25 — drawing from a *different
topic family*'s expert text — with 25 steps of post-injection
relaxation. Switch rate: **64%**.

Compared to D1 free dialog at the same setup (matched-relaxation D1
inject_t25 = 52% — though the doses and content differ slightly), D2's
64% under late-injection adversarial is *higher*, but compared to the
D1 pilot's 78% at step 15 with shorter relaxation, D2 shows similar or
weaker resistance. The fair comparison is at matched (override step,
relaxation horizon):

| regime | override | relaxation | adversarial switch |
|---|---:|---:|---:|
| D1 free | 25 | 4 steps | 52% |
| D2 drill-down | 25 | 25 steps | 64% |

The geometric / linguistic story is: drill-down imposes content gravity
(progressive specialization into a topic tree) that free dialog lacks.
Even when the adversarial injection text is in-distribution drilled-down
expert prose, 36% of D2 trajectories pull back toward the original
specialization line. **D2 is a measurably distinct regime from D1**,
and we identify it as the fifth member of the taxonomy.

### 5.9 Cross-experiment aggregation

Six standalone aggregator scripts produce the cross-regime comparison
artifacts that anchor the figures in this paper:

- `scripts/aggregate_basin_predictability.py` — overlay the basin
  predictability curves of the four diagnostic regimes onto a single
  axis. Output: `data/aggregated/basin_predictability_cross/`.
- `scripts/aggregate_t_sweep.py` — combine the D1 T-sweep CSVs.
  Output: `data/aggregated/t_sweep_basin_predictability/`.
- `scripts/aggregate_o1_d1_t_sensitivity.py` — side-by-side O1-vs-D1
  basin-predictability-vs-T comparison. Output:
  `data/aggregated/t_sensitivity_cross_regime/`.
- `scripts/aggregate_perturbation_cross_regime.py` — switching rates +
  relaxation curves across all 5 perturbation pilots (D1, O1, O2, O3, D2).
  Output: `data/aggregated/perturbation_cross_regime/` including the
  4×5 condition × regime grouped bar chart.
- `scripts/aggregate_dose_response.py` — dose-response curves across
  D1+O1 dose experiments, log-scale dose axis with 95% Wilson CI bars.
  Output: `data/aggregated/perturbation_dose_response/`.
- `scripts/aggregate_basin_hardening.py` — injection-time × switching
  curves for D1 + O1, with the basin-hardening interpretation.
  Output: `data/aggregated/perturbation_basin_hardening/`.

Each script reads only the per-experiment CSV outputs and is fully
deterministic — re-running them produces byte-identical figures. They
are kept separate from the per-experiment pipeline to allow incremental
re-aggregation as new experiments land.

### 5.10 Holographic-bulk geometry

For each of the four diagnostic perturbation pilots we computed:

#### Geodesic skeleton on V

Per-condition mean barrier height V* across the n basin centers:

| regime | control | neutral | lorem | adversarial |
|---|---:|---:|---:|---:|
| O1 | 2.5 | 2.6 | 2.5 | 2.2 |
| O2 | 2.7 | 2.5 | 0.55 | 1.3 |
| O3 | 2.3 | 2.5 | 0.52 | 1.4 |
| D1 | 1.2 | 1.0 | 0.8 | 0.4 |

(Values are rough averages across the 6 inter-basin geodesics in each
panel; raw V\* annotations are visible in
`data/exp_perturb_*_pilot/reports/perturbation/geodesic_skeleton_pca.png`.)

The geometric V\* values agree with the perturbation switching rates:

- **O2/O3 lorem** has V\* < 0.7 — basins are essentially merged →
  consistent with 100% switching.
- **O1 adversarial** has V\* ≈ 2.2 — basins remain distinct but the kick
  occasionally clears the ridge → consistent with 54% switching at
  ~150 tokens dose.
- **D1 adversarial** has V\* < 0.5 — basins are stylistic, not
  content-bound, so the geometric barrier is small → consistent with
  the 60% switching at saturated doses.

Cross-validation between the dose-response measurement and the
geometric V from kernel-density-estimation gives us two
independent estimates of barrier height that agree.

#### Hierarchical RG dendrogram

Per-condition maximum Ward-linkage merge distance across k=64 fine-cluster
centroids:

| regime | control | neutral | lorem | adversarial |
|---|---:|---:|---:|---:|
| O1 | 2.38 | 2.77 | 2.37 | 2.06 |
| O2 | 2.31 | 2.32 | **1.66** | 1.90 |
| O3 | 2.16 | 2.39 | **1.25** | 1.85 |
| D1 | 1.79 | 1.79 | 1.79 | 1.80 |

Three patterns:

1. **D1 is invariant** at 1.79–1.80 across all four conditions — the
   dialog cloud's coarse-graining diameter doesn't change with
   perturbation. Consistent with stylistic basins that are not
   reshaped by content injection.
2. **O2/O3 lorem collapse the cloud** to merge distance 1.66/1.25
   (vs control 2.31/2.16). Lorem perturbation under replace-mode
   captures every trajectory into a single tight new basin.
3. **O1 adversarial mildly compresses** (2.06 vs 2.38) and **O1
   neutral mildly disperses** (2.77 vs 2.38) — in-distribution
   perturbation pulls into a basin, out-of-distribution increases
   spread. Both effects are small in absolute terms but consistent in
   sign.

Each row of this 4×4 matrix is a quantitative attractor-fingerprint
signature for the corresponding regime.

---

## 6. Discussion

### 6.1 Architecture × content interaction

The taxonomy decomposes into a 2×2:

|  | append (preserve) | replace (overwrite) |
|---|---|---|
| **content-preserving** (continue, paraphrase) | O1 contractive basin | O2 oscillatory 2-cycle |
| **content-degrading** (summarize+negate) | weak collapse (O3a, REPORT2) | O3 absorbing |

Plus the orthogonal dialog axis:

|  | dialog architecture |
|---|---|
| **free** (curious user / helpful agent) | D1 stylistic multi-basin |
| **structured** (explorer drill-down / expert) | D2 content-anchored multi-basin |

This factorization predicts that any new operator can be slotted into the
matrix by knowing only its update rule and content function. We have not
formally tested this prediction (e.g., there's no D3-replace experiment
at publication scale), but the eight pilots covered enough of the
matrix to give us reasonable confidence.

### 6.2 Why does append-mode resist while replace-mode capitulates?

Mechanistic story: in append mode the perturbation text becomes a
fraction of an accumulating context. After step 15 of a 30-step
trajectory, the perturbation contributes ~1/15 of the context window's
tokens. The model continues "from where the context now points," and
that's mostly the original trajectory unless the perturbation is
in-distribution and large enough to shift the local probability mass.

In replace mode the perturbation *becomes* the entire next state. The
trajectory continues from the perturbation, and the original prefix has
no further influence. This is why replace-mode operators show ~100%
switching for any non-trivial perturbation.

Dialog's intermediate position follows: each turn is appended (so
content accumulates), but the per-turn weight of new content is high
relative to the rolling-window observable (last user turn, last agent
turn). The basin is stylistic — what gets reset by perturbation is the
style channel, not the content channel.

### 6.3 D2 as a sharpened D1

D2's 64% adversarial switching at 25-step relaxation, vs free dialog's
likely ~78% at the same horizon, comes from drill-down's content
gravity. The Explorer-Expert pair has an explicit instruction to drill
deeper into a single concept from the previous turn. Once the
trajectory is two or three drill-down steps deep ("photosynthesis →
Calvin cycle → RuBisCO → enzyme kinetics") the conversational momentum
has narrowed to a sub-tree, and adversarial injection of unrelated
expert prose can be partially rejected by the next drill-down asking
for more about the *original* sub-topic.

This is the first regime we've identified where **the dialog structure
itself imposes content gravity**, separate from any per-turn content
preservation. It opens up the question: are there other dialog
structures (debate, role-play, multi-party brainstorm) that select
different content-vs-style attractor balances?

### 6.4 The holographic-bulk picture as visualization

V(x) = −log ρ(x) is not an honest physical free energy — it's a
post-hoc summary of the trajectory ensemble's marginal density. Using
it as a "potential" with geodesics through it is a *visualization
choice*, not a derived dynamical statement. We make this clear in the
code comments and the documentation.

That said, the Dijkstra V\* values agreeing with the perturbation
dose-response thresholds is more than coincidence. Both measures are
asking "how hard is it to move from one density peak to another," via
different operationalizations. The agreement (roughly: V\* in [1, 3]
for O1 ≈ 150-token-equivalent dose; V\* < 0.7 for O2/O3 lorem ≈
saturated switching) suggests that the geometric framing captures real
structural information about the embedding-space dynamics.

### 6.5 What this means practically

For practitioners running LLM loops:

- **If you want a stable trajectory**, use append-mode with a
  content-preserving operator. You'll get a contractive basin that
  resists ~150 tokens of in-distribution perturbation.
- **If you want oscillation**, use replace-mode paraphrase. You'll get
  a 2-cycle that's stable in expectation.
- **If you want collapse**, use replace-mode summarize-and-negate.
  Convergence within ~10 steps, very low effective dimension afterward.
- **If you want stylistic variation under some shared topic constraint**,
  use dialog with explicit content-preserving structure (drill-down,
  debate, role-play). The style basins will resist disruption but the
  topic tree provides additional content gravity.
- **If you want resistance to topic-switching**, structure the dialog
  to force progressive specialization (drill-down). You'll get
  measurable content gravity that free-form chat lacks.

For ML researchers studying LLM loops: the four-plus-one regime
taxonomy with measured barriers should serve as a vocabulary for
describing what your particular setup is doing. The pipeline
(`embed → analyze → report`) takes ~30 minutes per new experiment to
produce all the diagnostic plots.

---

## 7. Limitations

### 7.1 Single model

All experiments use `gpt-4o-mini`. The taxonomy may reproduce on other
models (GPT-4, Claude, Llama, Mistral), but we have not tested. We
expect the qualitative regimes to be robust because the content-vs-
architecture factorization argument is model-agnostic, but the specific
dose thresholds and basin geometries will vary.

### 7.2 Single embedding family

`text-embedding-3-small`. We did spot-check that the qualitative regime
structure survives PCA dimensionality changes (PCA-2, -10, -50) and
projection into t-SNE-2, but we have not tested a different embedding
model.

### 7.3 Bounded context

All loops use a 12,000-character context cap with tail-clipping. The
contractive regime in particular may differ under no-clip conditions
(see REPORT2's `exp_noclip` ablation, which suggests the basin
deepens — recurrence drops further — when clipping is removed). We did
not run no-clip ablations across all four regimes.

### 7.4 English-only and short-context

All seed texts and system prompts are in English. Trajectory steps are
short (~120-160 tokens output). We have not tested whether the regimes
hold for other languages or for long-form generation (essay-length
outputs at each step).

### 7.5 Static system prompts

We do not vary the system prompt mid-trajectory. The contractive basin
of O1 might break under prompt drift; we have not tested.

### 7.6 The holographic-bulk framing

Treating V(x) = −log ρ(x) as an effective potential is a useful
visualization but not a derived physical statement. The Dijkstra V\*
"barrier height" depends on the kernel-density-estimation bandwidth,
the PCA-2 projection, and the grid resolution. Different choices give
different absolute V\* numbers; only the relative ordering across
conditions and regimes is robust.

### 7.7 Sample size for D2

The drill-down dialog regime was tested with only 25 trajectories at
50 steps each. The 64% adversarial switching rate has wide bootstrap CIs
(±10 percentage points). Replication at publication scale is needed
before strong claims about drill-down as a distinct regime.

---

## 8. Future work

1. **Cross-model replication.** Run the same diagnostic perturbation
   pilot on Claude, Llama, and Mistral models to verify the taxonomy
   transfers.
2. **Long-context regime.** What happens when each step generates
   essay-length output (~1000 tokens)? Does the contractive basin
   tighten, broaden, or fragment?
3. **Mixed-mode operators.** What attractor structure emerges from
   "append-then-summarize" or "replace-after-paraphrase"? The 2×2
   factorization suggests interpolation between regimes is possible.
4. **Drill-down at publication scale.** 5 families × 30 ICs × 3 runs
   × 50 steps to confirm D2's content gravity at full resolution.
5. **Dialog topology beyond drill-down.** Debate, brainstorm, role-play,
   adversarial-questioner. We expect each to select a distinct
   regime from the dialog architecture × content-rule matrix.
6. **Perturbation as a scientific tool.** Use the dose-response
   methodology to characterize the basin structure of any deployed
   LLM agent (chatbot, autonomous worker). A diagnostic perturbation
   battery could be added to capability evaluation.
7. **Connection to refusal training.** Do safety-trained models have
   different attractor structure than base models? Specifically, does
   alignment training create new basins (refusal modes) that perturbation
   tests can detect?

---

## 9. Methods appendix

### 9.1 Exact metric definitions

Recurrence:

```python
D = pairwise_distances(z, metric="cosine")  # T × T
mask = (np.abs(np.arange(T)[:, None] - np.arange(T)[None, :]) > tau) & np.triu(np.ones((T, T)), 1).astype(bool)
recurrence = (D < epsilon)[mask].sum() / mask.sum()
```

Basin score:

```python
clusters = KMeans(n_clusters=12).fit_predict(z_pca10)
target_cluster = mode(clusters[t > 0.7 * T])
basin_score = (clusters[t > 0.7 * T] == target_cluster).mean()
```

Lyapunov spectrum (sample-driven):

```python
# z_runs : (n_runs, T, d_pca)
for t in range(T):
    centered = z_runs[:, t, :] - z_runs[:, t, :].mean(axis=0)
    sigmas = np.linalg.svd(centered, full_matrices=False, compute_uv=False)
    lambda_t = np.log(sigmas) / 2.0  # (d_pca,)
```

Sharpness dimension (participation ratio):

```python
SD_t = (sigmas.sum() ** 2) / (sigmas ** 2).sum()
```

Basin predictability:

```python
y = mode(clusters[t > 0.7 * T])  # late-window cluster per trajectory
acc_curve = np.zeros(T)
for k in range(T):
    X = z_pca10[:, k, :]
    clf = LogisticRegression(multi_class="auto", max_iter=1000)
    acc_curve[k] = cross_val_score(clf, X, y, cv=5).mean()
```

### 9.2 Perturbation injection mechanics

For dialog-mode experiments, the injection happens at the user-turn
step (odd-numbered if Explorer initiates). The injection text replaces
the user turn's output verbatim. The trajectory then continues with
the agent's response to this overridden user turn, and from there
back to normal alternation.

For operator-mode experiments, the injection text replaces step k's
output entirely. The recurrence picks up from `X_{k+1} = clip(X_k ||
Y_k_inj)` (append) or `X_{k+1} = clip(Y_k_inj)` (replace).

The adversarial-source experiment for each regime is taken from the
*publication-scale* run of the same regime (e.g., O1 perturbation
adversarial draws from `exp_pub_O1_continue`). Adversarial samples
exclude the *family* of the trajectory being perturbed but may share
its overall topic distribution.

### 9.3 K-means choice and stability

We use k=12 for all clustering. This was chosen empirically — fewer
clusters merge meaningful basins, more clusters split them. The
relative basin scores are stable for k ∈ [8, 16]; we have not tested
beyond.

### 9.4 PCA stability

Joint PCA on the full point cloud (all trajectories of an experiment)
gives stable PC1/PC2/PC3 directions across trajectories. We re-fit per
experiment but never per-trajectory.

### 9.5 Animation rendering pipeline

The 3D animation pipeline (`trajectory_animation_3d.py`) supports
parallel rendering via `concurrent.futures.ProcessPoolExecutor`. Each
worker process imports matplotlib with the Agg backend, builds a fresh
figure for one frame, and saves a PNG. The main process stitches PNGs
into MP4 via `imageio-ffmpeg` (libx264, quality 8). With 40 workers,
75 frames at DPI 180 take ~80 seconds wall-time vs ~11 minutes
single-threaded.

---

## 10. Reproducibility statement

### 10.1 Data availability

All raw trajectories are stored under `data/exp_*/raw/steps.jsonl` and
LFS-tracked in the public repository. Total raw payload: 3.3 GB across
37 experiments.

### 10.2 Code availability

All code is at <https://github.com/kaplan196883/llmattr>. License:
TBD (currently no license file; authors retain rights pending
publication).

### 10.3 Compute and cost

- **Embedding regeneration**: ~$30 in OpenAI `text-embedding-3-small`
  API calls for the full 37-experiment set.
- **Generation regeneration**: ~$200 in `gpt-4o-mini` API calls;
  unnecessary if `steps.jsonl` files are checked out from LFS.
- **Local compute**: ~2 hours wall-time for full embed + analyze on a
  40-core machine. Animations add ~80s each × 50 = ~70 min.

### 10.4 Pipeline commands

```bash
# Generate (only for new experiments)
python -m src.experiments.dialog.main run    --config <cfg.yaml>
python -m src.experiments.operators.main run --config <cfg.yaml>
python -m src.experiments.perturbation.main run --config <cfg.yaml>

# Derive (works on existing steps.jsonl)
python -m src.experiments.<runner>.main embed --config <cfg.yaml>
python -m src.experiments.<runner>.main analyze --config <cfg.yaml>
python -m src.experiments.dynamics.basin_predictability --config <cfg.yaml>
python -m src.experiments.dynamics.regime_plots --data-dir data
python -m src.experiments.perturbation.flow_skeleton --experiment <exp_id> [--is-dialog]
python -m src.experiments.perturbation.geodesic_skeleton --experiment <exp_id> [--is-dialog]
python -m src.experiments.perturbation.bulk_plots --experiment <exp_id> --override-step <k> [--is-dialog]
python -m src.experiments.perturbation.rg_dendrogram --experiment <exp_id> [--is-dialog]
python -m src.experiments.perturbation.trajectory_animation_3d \
       --experiment <exp_id> --condition <c> --parallel 40

# Aggregate
python -m scripts.aggregate_perturbation_cross_regime
python -m scripts.aggregate_dose_response
python -m scripts.aggregate_basin_hardening
python -m scripts.aggregate_basin_predictability
python -m scripts.aggregate_t_sweep
python -m scripts.aggregate_o1_d1_t_sensitivity
```

### 10.5 Per-experiment catalog

Full catalog of the 37 experiments with phase, regime, scope, and
purpose: see `docs/DATA_INDEX.md`.

### 10.6 Stage reports

The discovery process is documented in six stage reports:

- `docs/reports/REPORT1.md` — first run on `exp_default`; baseline
  classification methodology
- `docs/reports/REPORT2.md` — long-horizon and clipping ablations
- `docs/reports/REPORT3.md` — dynamical-systems metrics (Lyapunov,
  sharpness)
- `docs/reports/REPORT4.md` — operator regime classification (the
  four-regime taxonomy)
- `docs/reports/REPORT5.md` — publication-scale verification
- `docs/reports/REPORT6.md` — perturbation experiments and
  basin-hijacking, including drill-down dialog (D2)

### 10.7 Test coverage

84 pytest tests cover the analysis primitives plus integration:

```bash
PYTHONPATH=. python -m pytest tests/ -q
# 84 passed in ~12s
```

### 10.8 Repository layout summary

```
llm_attractor_experiment/
├── README.md, requirements.txt, ARTICLE.md
├── docs/
│   ├── DATA_INDEX.md
│   └── reports/REPORT1.md … REPORT6.md
├── src/
│   ├── analysis/      basin, recurrence, dwell, PCA, t-SNE, distances, …
│   ├── api/           OpenAI client + embedder + generator
│   ├── core/          trajectory runner, observables, baselines, context
│   ├── experiments/
│   │   ├── dialog/    D1/D2/D3 alternating-role runner
│   │   ├── operators/ O1–O4 single-role recursive operators
│   │   ├── dynamics/  10 post-hoc CLI analysis modules
│   │   └── perturbation/ 14 modules: runner, analyze, corpora, plot+animation
│   ├── reports/       narrative report writer
│   └── utils/         io, logging, seeds, text helpers
├── scripts/           build_publication_configs + 6 aggregators
├── configs/           dialog/ + operators/ + perturbation/ + archive/
├── tests/             84 pytest tests
└── data/              37 experiment dirs + aggregated/ outputs
```

---

## 11. Coverage of original specification

The project began from a four-document brief (the originals are
preserved in `/junk/req1.txt`, `req2.txt`, `req3.txt`, `reg4.txt` —
gitignored) that pre-specified the architecture, API surfaces, metric
battery, and reporting format. This section maps the brief's
requirements to where they're implemented.

### 11.1 Implementation phases (req1.txt 12-phase plan)

| Phase | Requirement | Implementation |
|---|---|---|
| 1 | YAML config system, frozen snapshot per run | `src/config.py` + `data/<exp>/config.yaml` |
| 2 | `ContextState` + `clip_context(text, max_len, rule)` with `tail_chars` | `src/core/context.py` |
| 3 | OpenAI Responses API + Embeddings API integration | `src/api/{generator,embedder,openai_client}.py` |
| 4 | Output / rolling-window / context-tail observables | `src/core/observables.py` (+ 5 dialog observables in `src/experiments/dialog/observables.py`) |
| 5 | Embedding dataset creation, batched, cached | `embeddings/<obs>/{embeddings.npy, metadata.parquet}` per experiment |
| 6 | Joint PCA-2/10/20, no per-trajectory fits | `src/analysis/pca.py` (we extended to PCA-50 for t-SNE pre-reduction) |
| 7 | Recurrence with `‖z_t − z_s‖ < ε`, `|t − s| > τ` | `src/analysis/recurrence.py` |
| 8 | Dwell with KMeans + DBSCAN clustering | `src/analysis/{clustering,dwell}.py` (KMeans default, DBSCAN supported) |
| 9 | Basin convergence with perturbed ICs | `src/analysis/{basin,basin_entry}.py` (perturbation evolved to mid-trajectory injection — see 11.4) |
| 10 | Three baselines (no_feedback, time_shuffled, independent_regeneration) | `src/core/baselines.py` |
| 11 | Robustness across observables, spaces, seeds | `src/analysis/robustness.py` + cross-observable comparison in reports |
| 12 | Markdown report with not_supported / weak / moderate / strong classification | `src/reports/summary.py` (`classify_two_axis`, `classify_three_axis`) |

All 12 phases are implemented and exercised in the 84 unit + integration
tests under `tests/`.

### 11.2 OpenAI API surfaces (req2.txt)

| Surface | Required | Implemented |
|---|---|---|
| Responses API (`client.responses.create`) | required for all generation | `src/api/generator.py:generate_step` ✓ |
| Embeddings API (`client.embeddings.create`) | required for all observables | `src/api/embedder.py:embed_texts` ✓ |
| Batch API (Files + Batches) | optional, for large async embed jobs | `src/api/batch_jobs.py` (functional but `batch_embeddings: false` in publication runs) |
| Evals API | optional, orchestration only | `src/api/evals_runner.py` (gated by `use_evals: false`) |
| `store=False` (no server-side chat state) | mandatory | enforced in `generator.py` |
| Logprobs (`include=["message.output_text.logprobs"]`) | optional | enabled by `include_logprobs: true` in config; unused in publication analyses |

### 11.3 H1a/H1b two-axis split (reg4.txt)

The `exp_long_v2` brief introduced a critical methodological refinement:
**don't classify "support for H1" with a single label** — split into
two orthogonal hypotheses:

- **H1a (convergence)**: trajectories converge into stable
  basin-like regions
- **H1b (recurrence)**: once inside the basin, trajectories revisit
  neighborhoods more than expected under a temporal null

We extended this to a **three-axis** classifier (H1a + H1b + H1c
divergence) implemented in
`src/experiments/operators/classifier.py:classify_three_axis`. Each
axis gets an independent `not_supported / weak / moderate / strong`
verdict, and the four-regime taxonomy emerges from the joint pattern:

| regime | H1a | H1b | H1c |
|---|---|---|---|
| O1 contractive | strong | weak | weak |
| O2 oscillatory | weak | strong | weak |
| O3 absorbing | strong (singular) | weak | weak |
| D1 multi-basin | strong (per-style) | weak | weak |

This is the formal version of the "fixed-point vs orbiting attractors"
distinction that reg4.txt §15 calls for.

### 11.4 Methodological evolutions

The implementation deviates from the original brief in three places.
We document each to be honest about the divergence:

#### 11.4.1 Perturbation: initial-condition → mid-trajectory injection

req1.txt Phase 9 specifies basin score via *perturbed initial
conditions* (suffix, paraphrase, neutral-sentence, seed-only). We ran
this style at small N in REPORT1/2 but found it under-powered: the
perturbation gets diluted in the recurrence and switching rates were
near-zero or near-100% for any non-trivial seed change.

REPORT6 evolves the perturbation to **mid-trajectory text injection**
at a chosen step (5/15/25), with four conditions (control / neutral /
lorem / adversarial). This produces the dose-response and basin-
hardening curves that comprise the bulk of Phase 3 results. The
original initial-condition framing is subsumed by `n_runs > 1` per IC
producing run-to-run basin convergence statistics.

#### 11.4.2 Temperature sweep: 4 levels instead of warm/cool pair

reg4.txt §3 specifies four conditions: A (T=0.8 baseline), B (T=1.1
warmer), C (T=0.4 cooler), D (memory stress with 4-6k clip). We ran:

- T-sweep at T ∈ {0.3, 0.6, 0.8, 1.2} for both D1 and O1 — covers reg4's
  warmer (1.2 ≈ 1.1) and cooler (0.3 ≈ 0.4) intent, with extra mid-T
  resolution
- Memory stress (Condition D, clip ∈ [4k, 6k]) — **not run**. This
  remains an open ablation in our future-work list (see §8).

The T-sweep produced the qualitative finding reg4.txt §15 anticipated:
**O1 broadens with T (basin loosens)** while **D1 stays locked
(stylistic basins are temperature-stable)**. We did not see warmer T
"reveal hidden recurrence" — instead it monotonically reduced basin
predictability, consistent with the contractive-regime interpretation.

#### 11.4.3 Observable: rolling_k3 kept, rolling_k5 not added

reg4.txt §5 recommended adding `rolling_k5` for finer in-basin recurrence.
We did not add it — `rolling_k3` and `context_tail` together gave us
sufficient signal for the four-regime classification. Adding `rolling_k5`
would be a near-zero-cost extension if needed; the observable interface
in `src/core/observables.py` is parameterized by `k`.

### 11.5 Reports / classification format (req1.txt §12)

The original brief specifies a report ending in
`not_supported | weak | moderate | strong` for H1. We produce *two*
report variants per experiment:

- `reports/report.md` — single-axis legacy classifier
  (`classify_two_axis` in `src/reports/summary.py`)
- `reports/report_operators.md` — three-axis (H1a/b/c) classifier
  (`classify_three_axis` in `src/experiments/operators/classifier.py`)

Both carry the underlying signal counts so the verdict is auditable.

### 11.6 What the original brief did NOT call for but we added

- **Lyapunov spectrum + sharpness dimension** (REPORT3) from
  Tuci et al. (2026); not in the original brief
- **Periodicity metrics** (`period_2_score`, `best_period`) for
  detecting the 2-cycle regime; not in the original brief
- **Dispersion metrics** (`dispersion_growth`, `drift_monotonicity`)
  for distinguishing contractive from divergent regimes
- **Basin predictability** (5-fold CV logistic regression on PCA-10);
  not in the original brief
- **The perturbation visualization toolkit** (V landscape, Dijkstra
  geodesics, marching-cubes iso-density, parallel 3D animations) —
  novel to this work
- **The drill-down dialog regime (D2)** — discovered during Phase 3
  perturbation experiments
- **Cross-experiment aggregator scripts** for T-sweep, dose-response,
  basin hardening, perturbation cross-regime — built incrementally as
  the experiment list grew

Each addition is justified in the corresponding stage report.

---

## 12. Acknowledgments

We acknowledge `gpt-4o-mini` and `text-embedding-3-small` (OpenAI),
the open-source ecosystem (numpy, scipy, scikit-learn, scikit-image,
matplotlib, pandas, imageio-ffmpeg), and the Tuci et al. (2026)
arXiv:2604.19740 framework for finite-time Lyapunov spectra of
sampling-based generators.

This research was conducted with the assistance of Claude (Anthropic)
as a code-development partner — specifically for the perturbation
visualization toolkit, the holographic-bulk geometry implementation,
and the article structure.

---

## 13. References

(To be expanded for formal submission.)

- Carlini, N. et al. (2021). *Extracting training data from large
  language models.* USENIX.
- Hopfield, J. J. (1982). *Neural networks and physical systems with
  emergent collective computational abilities.* PNAS.
- Holtzman, A. et al. (2020). *The curious case of neural text
  degeneration.* ICLR.
- Maheswaranathan, N. et al. (2019). *Reverse engineering recurrent
  networks for sentiment classification reveals line attractor
  dynamics.* NeurIPS.
- Park, J. S. et al. (2023). *Generative agents: interactive simulacra
  of human behavior.* UIST.
- Sussillo, D. & Barak, O. (2013). *Opening the black box: low-
  dimensional dynamics in high-dimensional recurrent neural networks.*
  Neural Computation.
- Tuci, E. et al. (2026). *Lyapunov analysis of recursive language
  models.* arXiv:2604.19740.

---

*Repository: <https://github.com/kaplan196883/llmattr>*
*Article version: v1.0, 2026-04-27*
