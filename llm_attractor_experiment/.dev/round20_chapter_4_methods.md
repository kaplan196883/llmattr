## 4. Methods

Before the per-component details below, the experimental skeleton is
short: we run paired recursive trajectories from the same seed and
prompt; in the treatment run we inject text at a fixed step; we embed
every step's observable output, project to a low-dimensional space, and
cluster final states jointly across treatment and control runs; the
perturbation is summarized by the perturbed run's final cluster relative
to its paired control's. We separately estimate the control-vs-control
divergence rate (how often two paired control runs already disagree
from sampling alone) and the persistent-escape rate (how often a
perturbed run jumps clusters at injection AND remains in the new
cluster at the terminal step). The remainder of §4 details each of
these components.

### 4.1 The recurrence

Instantiating the formal recurrence from §3.1 with the three nudges:
$$
\text{Append:}\quad X_{t+1} = \mathcal{N}_{\text{append}}(X_t, Y_t) = \operatorname{clip}(X_t \Vert Y_t)
$$
$$
\text{Replace:}\quad X_{t+1} = \mathcal{N}_{\text{replace}}(X_t, Y_t) = \operatorname{clip}(Y_t)
$$
$$
\text{Dialog:}\quad X_{t+1} = \mathcal{N}_{\text{dialog}}(X_t, Y_t) = X_t \Vert \operatorname{format\_turn}(r_t, Y_t)
$$

with $Y_t \sim P_\theta(\cdot \mid X_t;\, f)$ and $P_\theta$ the
language-model distribution parameterized by $\theta$ (here
`gpt-4o-mini`). The clipping operator $\operatorname{clip}(\cdot)$
truncates context from the head (oldest) once the running string
exceeds 12,000 characters, preserving the most recent state. The
content operator $f$ enters through the system prompt fed to
$P_\theta$, e.g. "Continue the text" for $f = \text{continue}$,
"Paraphrase the following" for $f = \text{paraphrase}$.

### 4.2 Sampling

Each experiment runs `N_traj = N_families × N_ICs × N_runs`
trajectories. Publication-scale defaults differ by experiment family:

- **Operator runs (O1, O2, O3)**: 15 prompt families × 30 initial
  conditions × 3 runs = **1,350 trajectories per regime**, run for
  40 steps. Total points per experiment: 1,350 × 40 = 54,000.
- **Dialog runs (D1)**: 5 dialog-suitable families × 30 initial
  conditions × 3 runs = **450 trajectories**, 40 steps. Total points:
  450 × 40 = 18,000 per role; both roles are embedded so the
  effective per-experiment point count is 36,000.
- **D2 (drill-down dialog)** is currently at exploratory scale only:
  5 families × 5 ICs × 1 run = 25 trajectories, 50 steps. Below the
  N≥2-runs minimum for ensemble-spread diagnostics (§11.2).

In every case trajectories run for 40 steps unless explicitly noted
(D2 uses 50; the T-sweep variants vary `steps_per_run`).

Initial conditions are 5-30 short seed texts per "family" (philosophical
prompts, practical-advice prompts, creative-writing prompts, reflective
prompts, emotional prompts). Across families we get diversity in topic
and tone; within families we get variability across seeds.

Sampling temperature `T = 0.8` unless varied (Phase 2b T-sweep).

### 4.3 Embedding

All trajectories are embedded with `text-embedding-3-small` (OpenAI),
producing 1536-dimensional vectors. We embed multiple *observables* per
step, each captures a different facet of the trajectory state, and
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

The names above use D1's role labels (user / agent). For dialogs
configured with different role labels, D2 uses *explorer* / *expert*,
the role-specific observables are named after the configured roles
(`last_explorer_turn`, `rolling_expert_k3`, etc.). Role names are read
from `cfg.dialog.role_a.name` / `cfg.dialog.role_b.name` at embed time;
the observable wiring in `src/experiments/dialog/observables.py` accepts
any role-name pair.

Embeddings are batched and cached per observable. The codebase also
includes (but does not currently use in publication runs) an OpenAI
**Batch API** integration (`src/api/batch_jobs.py`) that supports
asynchronous embedding at ~50% cost, plus an **OpenAI Evals** runner
(`src/api/evals_runner.py`) gated behind `use_evals: false` in all
configs. Both are infrastructure stubs available for future expansion.

Total token cost for synchronous embedding of the full repository:
~\$30 in embedding API calls.

#### 4.3.1 Single-context embedding mechanics

A subtle but important invariant: **for one observable string at one
trajectory step, we obtain exactly one 1536-dimensional vector.** No
chunking, no internal sliding window we manage, no per-token outputs.
The `text-embedding-3-small` model handles internal attention over up
to 8,191 input tokens and produces a single pooled representation
which `embed_texts` writes to one row of the output matrix:

```
"Continue the text. The fox was quick..." → text-embedding-3-small → v ∈ R^1536
```

After the API returns, we **L2-normalize** each row defensively so all
downstream cosine-similarity computations reduce to dot products and
numerical drift from float32 round-trips does not accumulate:

```
norms = ||v||_2 + 1e-12
v_norm = v / norms # ||v_norm||_2 = 1.0
```

The model is deterministic given the input, `hash(text) → vec` is a
stable mapping under fixed model version, so the embedding cache is
safe and `analyze` reruns on the same `embeddings.npy` are identical.

Per-trajectory step we therefore obtain `K` independent vectors where
`K = |observables|`, 3 for operator publication runs (output,
rolling_k3, context_tail), 8 for dialog publication runs (the three
generic plus last_<role-A>_turn, last_<role-B>_turn,
rolling_<role-A>_k3, rolling_<role-B>_k3, turn_pair). Some pilot
configs also enable `context_full`, bringing the counts to 4 / 9.
These are stored in `K` separate `embeddings.npy` files (one per
observable); each defines its own trajectory in 1536-d embedding
space.

#### 4.3.2 Token-budget analysis

The 8,191-token API limit is held with a ~4× safety margin by
construction:

| layer | constraint | typical value | upper bound (tokens) |
|---|---|---|---|
| Per-step generation | `max_output_tokens` | 120 (operator), 160 (dialog) | ≤ 160 |
| Running context cap | `max_context_chars` | 12,000 chars | ~3,000 |
| `output` observable | the single Y_t |, | ≤ 160 |
| `rolling_k3` | 3 × Y plus 2 separators |, | ~480 |
| `context_tail` | `[-4000:]` slice |, | ~1,000 |
| `context_full` | `[-8000:]` slice |, | ~2,000 |
| `turn_pair` (dialog) | last user + last agent |, | ~320 |
| `rolling_user_k3` / `rolling_agent_k3` | 3 turns of one role |, | ~480 |

Conversion uses `cl100k_base`'s ~4 chars/token average for English
prose; the bound holds even for code- or math-heavy text where the
ratio shifts to ~3 chars/token.

The running context `X_{t+1}` itself is **never embedded directly**.
It is used to feed the generator but every observable applies a `[-N:]`
tail-slice before the embedder sees the string. This slicing is the
single rule that prevents append-mode context growth from blowing the
embedder's token budget.

#### 4.3.3 Sliding-window content in append mode

In **append mode** the running context grows monotonically until it
hits the 12,000-char clip ceiling, then stabilizes. Once
`len(context_after) ≥ N`, the slice `context_after[-N:]` is **always
exactly N chars** but its **content shifts forward by `len(Y_t)` chars
each step** (~120 chars for operator runs):

```
Step t: context_after has 9,500 chars. context_full = chars [1500 : 9500]
Step t+1: Y_{t+1} appends ~120 chars. context_full = chars [1620 : 9620]
```

So between adjacent steps the slice has ~99% content overlap and ~1%
fresh content. The resulting embeddings are **highly correlated, not
identical**. Empirically:

| observable | content overlap with previous step | adjacent-step cosine sim |
|---|---|---|
| `output` | 0% (Y_t is freshly generated each step) | ~0.5-0.8 |
| `rolling_k3` | ~67% (2 of 3 outputs unchanged) | ~0.85-0.95 |
| `context_tail` (4000 chars, append) | ~97% | ~0.95-0.98 |
| `context_full` (8000 chars, append) | ~99% | ~0.97-0.99 |

These different-overlap regimes give the trajectory **different motion
speeds in embedding space** for different observables. `output` shows
fast cycling motion (each step is a fresh generation); `context_full`
shows slow integrated drift; `rolling_k3` is the compromise. This is
exactly why we run every metric on every observable and require
cross-observable agreement before accepting a regime label, a finding
that holds only on `output` could be a per-step fluctuation; one that
holds only on `context_full` could be a slow-drift artifact; one that
holds on both is robust evidence.

In **replace mode** (O2, O3) the running context is just the latest
`Y_t` (~120 tokens), so all four content-based observables (`output`,
`rolling_k3`, `context_tail`, `context_full`) collapse to the same
short string and yield the same embedding. The `rolling_k3` observable
remains distinct in replace mode because it concatenates outputs across
multiple steps explicitly.

#### 4.3.4 Adjacent-step similarity verification

This is verifiable on any append-mode publication run:

```python
import numpy as np, pandas as pd
v = np.load("data/exp_pub_O1_continue/embeddings/context_full/embeddings.npy")
m = pd.read_parquet("data/exp_pub_O1_continue/embeddings/context_full/metadata.parquet")
sub = m[(m.prompt_family=="philosophy") & (m.run_id=="run_000")].sort_values("step")
idx = sub.index.values
sims = [float(v[idx[i]] @ v[idx[i+1]]) for i in range(len(idx)-1)]
np.median(sims) # ≈ 0.97-0.99 for context_full in append mode
```

Truly identical embeddings across consecutive steps would only happen
in degenerate cases: an absorbing fixed point where `Y_t` becomes
constant, or empty-output steps. The first happens in O3 absorbing
where `output` embedding becomes essentially constant past step ~10
(driving the basin score to 1.0); we do not see the second in
practice.

#### 4.3.5 The "single context → single embedding" rule

To summarize the answer to a question that recurred during the project:

- One observable string ⇒ one 1536-d vector. No chunking, no per-token
  output, no model-side internal sliding window we control.
- One trajectory step ⇒ K vectors (K = 3 operator, 8 dialog at
  publication scale; +1 each if `context_full` is enabled), one per
  observable, each from an independent API call.
- One trajectory ⇒ `K × T` vectors total (T steps), arranged as K
  parallel polylines in 1536-d embedding space, each with its own
  PCA, t-SNE, clustering, and metric battery.

The embedding step itself is the only place data crosses from
free-form text into the deterministic numerical world; everything
downstream is reproducible from the cached `embeddings.npy +
metadata.parquet` pair.

### 4.4 Representation spaces

For each observable's embedding matrix `Z ∈ R^{N×1536}` we compute four
projections, each fit jointly across the full point cloud (never
per-run, never per-family) so coordinates are comparable:

#### 4.4.1 PCA-2 / PCA-10 / PCA-50

Linear projections via `sklearn.decomposition.PCA` with
`random_state=42`:

- `Z_PCA-2 ∈ R^{N×2}`, for density estimation, V landscape, and most
  2D plots. Carries 10-15% of total variance for short-output observables
  (`output`); higher (~25%) for longer-context observables.
- `Z_PCA-10 ∈ R^{N×10}`, used for K-means clustering, basin
  classification, basin-predictability regression, recurrence/dwell.
  Captures 30-50% of variance and gives clusters that are both stable
  under bootstrap and interpretable in the original embedding space.
- `Z_PCA-50 ∈ R^{N×50}`, pre-reduction stage for t-SNE only. Captures
  ~80% of variance and removes the high-dimensional noise that would
  otherwise dominate cosine distances at the t-SNE step.

#### 4.4.2 t-SNE

We fit `sklearn.manifold.TSNE(n_components=2)` with the following
parameters:

```python
TSNE(
    n_components=2,
    perplexity=30, # capped at (N-1)/4 for small N
    pre_pca_dim=50, # see 4.4.1 above
    metric="cosine", # matches embedding similarity
    init="pca", # PCA-init for stability
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
is essential, each condition's PCA-2 cloud must live in shared
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
recurrence(ε, τ) = #{(t, s) : ‖z_t − z_s‖₂ < ε ∧ |t − s| > τ} / [T(T−1)/2]
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

Sampling-based text generation has no smooth Jacobian (outputs are
discrete samples), so we construct a finite-time Lyapunov spectrum
from inter-run ensemble spread rather than from a one-step linearization.
This is our analog of the parameter-space Lyapunov framework that Tuci
et al. (2026) use for SGD; the construction here is independent and
specific to inference-time recursion. For each (family, IC) pair we
have N runs; at each step t the ensemble produces N embeddings forming
a covariance:

```
Σ_t = (1/(N−1)) · Σ_i (z_i^t − z̄^t)(z_i^t − z̄^t)ᵀ
```

The k-th finite-time Lyapunov exponent is the log-amplitude growth
rate of the k-th principal direction over the window
`[t_baseline, T−1]`:

```
λ_k = (1 / [2·(T − 1 − t_baseline)]) · log( μ_k(T−1) / μ_k(t_baseline) )
```

where `μ_k(t)` is the k-th eigenvalue of `Σ_t`. The factor `1/2`
converts variance growth to amplitude growth, and dividing by the
window length gives a per-step rate (units: inverse step). The top
exponent `λ_1` is interpreted as a finite-time Lyapunov exponent
(FTLE).

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

We use a Tuci-style fractional dimension over the ordered Lyapunov
spectrum (functional form from Tuci et al. (2026), Definition 4.2):

```
j* = max { i : Σ_{k≤i} λ_k ≥ 0 } (0 if λ_1 < 0)

SD = j* + (Σ_{k≤j*} λ_k) / |λ_{j*+1}|
```

with SD = 0 when the spectrum is everywhere negative and SD = d when
the cumulative sum stays non-negative through the whole spectrum.
SD counts the effective number of *expanding* directions before global
contraction dominates: a near-neutral next eigenvalue lets SD float
above j*, a sharply contracting one keeps SD close to j*.

We borrow only the functional form. Tuci et al. anchor SD to a
generalization-bound theorem (their Theorem 4.5) for SGD on parameter
space; that theorem requires Jacobian-derived `λ_k` and a training-
data PAC framework, neither of which applies to inference-time
recursion of a frozen LLM. We treat SD as a comparative diagnostic
across regimes only.

**N=3 rank ceiling.** With N=3 runs per IC, the ensemble covariance
has rank ≤ 2, so the Lyapunov spectrum returned by
`compute_lyapunov_spectrum` has length 2. SD is therefore bounded
above by 2.0 in our experiments, and many trajectory cells saturate
at the ceiling. The mean SD_late on `context_tail` does still
differentiate regimes empirically (O1 1.70, O2 1.39, O3 1.45,
D1 1.89; §11.2), but the magnitude differences are modest. A
companion measure, **effective rank**, counts Lyapunov exponents
above −0.01; it gives a discrete count rather than a fractional
dimension and is reported alongside SD in `dynamics.csv`.

Both are computed in `src/experiments/dynamics/sharpness_dim.py`.

#### 4.5.7 Periodicity

To detect oscillatory regimes (O2-style 2-cycles, O4-style longer
cycles), we compute lag-distance autocorrelation. For trajectory points
`z_0, ..., z_{T-1}`:

```
mean_dist(k) = mean over (t, t+k) of ‖z_t − z_{t+k}‖_cos
```

The output statistics from `trajectory_periodicity` in
`src/experiments/operators/periodicity.py`:

- **`period_2_score`** = `mean_dist(1) − mean_dist(2)`, positive
  values indicate a 2-cycle (lag-2 points are closer than lag-1 points)
- **`period_3_score`**, analogous for 3-cycles
- **`best_period`**, the lag k ∈ [1, T/2] minimizing `mean_dist(k)`
- **`autocorr_distances`**, full vector of mean lag distances

This is run on every trajectory and aggregated per (regime, family) for
condition-vs-baseline tests.

#### 4.5.8 Dispersion

To distinguish contractive from exploratory dynamics we compute, in
`src/experiments/operators/dispersion.py`:

```
initial_dispersion = mean pairwise distance over t ∈ [0, T/4]
final_dispersion = mean pairwise distance over t ∈ [3T/4, T]
dispersion_growth = (final - initial) / initial
global_drift = ‖centroid(t=T) − centroid(t=0)‖
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
  `dwell_above_null`. 0-2 signals → strength {not_supported, weak,
  moderate, strong}.
- **H1b (recurrence / oscillation)**: signals are
  `late_recurrence_above_null`, `period_2_score > threshold`, and
  `best_period_majority > 1`. 0-3 signals.
- **H1c (divergence / no-attractor)**: signals are
  `dispersion_growing`, `drift_monotonically_outward`, and
  `no_stable_basin`. 0-3 signals.

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

#### 4.5.10 Basin predictability

For each trajectory we compute the K-means cluster at the late window
(`y` = cluster index at `t > 0.7T`). For each early step k we train a
multinomial logistic regression to predict y from PCA-10 at step k.
Cross-validation:

1. **Drop singleton classes**, clusters that contain only one
   trajectory member can't be split into train/test, so we filter
   them out before CV (recording `n_dropped_classes` and
   `n_dropped_traj` per row for audit).
2. **Adaptive stratified k-fold** with
   `n_splits = min(5, smallest_class_size)`. Publication-scale runs
   (n=1350 / regime) always reach the full 5-fold; reduced-scope
   T-sweep cells (n=150) and phase-1 pilots (n=75) fall back to 2-4
   folds when the smallest remaining cluster has fewer than 5
   members. When the late-window cluster grouping leaves fewer than
   2 non-singleton classes (rare; only occurs at very early
   predictor steps for some dialog cells) we write `NaN` for that
   (regime, step) cell.

The accuracy curve `acc(k)` is monotonic in good regimes, by some
early step the late basin is already determined.

#### 4.5.11 Perturbation switching

For each trajectory we run paired runs with the same prefix but four
different perturbation conditions injected at `t_inject`:

- `control`: no perturbation
- `neutral`: a paragraph (~80 tokens) of off-topic Wikipedia text drawn
  from an 8-paragraph hand-written pool (`corpora.NEUTRAL_WIKI`); the
  pilot default sends the full paragraph, dose-parametrized variants
  (`neutral_<N>`) resize to N tokens explicitly
- `lorem`: 70 random English words drawn from a hand-curated neutral
  word pool (`corpora._WORD_POOL`) chosen to avoid emotional or
  introspective vocabulary
- `adversarial`: late-step output from a *different* (family, IC) trajectory of the same regime

We compute the K-means cluster (joint PCA-10 across all conditions, k=12)
at the final available step (29 for 30-step, 49 for 50-step trajectories).
**Switching rate** = fraction of trajectories whose final cluster differs
from their paired control's. This endpoint counts final disagreement
only and is therefore deliberately sensitive to ordinary stochastic
divergence; it is meaningful only when read together with the
control-vs-control floor (§4.5.10 / §4.7) and the persistent-escape
analysis (§3.1.2, §5.14). A switching rate that is not net-corrected
is not evidence of basin redirection.

**Algorithm 1: Paired perturbation evaluation for a recursive loop.**

```
Input:
  task / seed x
  generator P_θ
  context-update rule N
  injection condition c
  injection step t_inj
  terminal step T
  observable map O
  equivalence rule C (clustering, patch-family, tests, etc.)

1. Run two unperturbed controls:
     A = RunLoop(x, P_θ, N, no injection)
     B = RunLoop(x, P_θ, N, no injection)

2. Estimate stochastic-floor event:
     floor_event = [C(O(A_T)) ≠ C(O(B_T))]

3. Run matched treatment:
     Z = RunLoop(x, P_θ, N, inject c at t_inj)

4. Raw switching:
     raw = [C(O(Z_T)) ≠ C(O(A_T))]

5. Injection-time jump:
     jump = [C(O(Z_{t_inj+1})) ≠ C(O(Z_{t_inj-1}))]

6. Persistent escape:
     persist = jump AND [C(O(Z_T)) = C(O(Z_{t_inj+1}))]

7. Aggregate over seeds / tasks / families:
     raw_rate = mean(raw), floor = mean(floor_event)
     net_rate = raw_rate − floor
     persistent_escape_rate = mean(persist)
```

The same algorithm applies to embedding clusters (this paper) and to
engineering observables: final patch family, files touched, test
pass/fail set, selected plan category, security-policy violation, or an
embedding of the full trace.

### 4.6 Baselines

Each baseline ablates a different mechanism so we can isolate which
property of the loop is producing the observed attractor:

- **`time_shuffled`** (post-hoc): reshuffle step labels within each
  trajectory and recompute the dynamics metrics. If the metric is
  unchanged, it depends only on the marginal point cloud and not on
  temporal structure, i.e., the "trajectory" is effectively a bag of
  embeddings, not a process. Implemented in
  `src/analysis/robustness.py:time_shuffle_labels`.
- **`no_feedback`** (`src/core/baselines.py:no_feedback_provider`):
  sample each step's output from the *seed only*, ignoring the
  accumulated context. This nulls the recurrence, the loop becomes N
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
- **Adaptive stratified k-fold CV** for basin predictability classifier
  accuracy: `n_splits = min(5, smallest_class_size)` so phase-1 pilots
  with small clusters fall back to 2-4 folds gracefully (NaN if even
  2-fold is impossible). See §4.5.10.
- **Wilson-style CI** on switching-rate proportions where bootstrap
  would be unstable (small denominators in dose-response cells).
- **Significance gate**: a regime / condition signal counts only if its
  diagnostic statistic is `≥ 2σ` above the baseline mean *and* its
  Cohen's d ≥ 0.5 (medium effect). Both criteria must hold; CI alone
  can pass with trivially small effects under sufficient N.

### 4.8 Static visualization battery

Beyond the perturbation toolkit (§4.10), every experiment generates a
standardized set of static plots, defined in
`src/experiments/dynamics/regime_plots.py`,
`src/experiments/dynamics/field_plots.py`,
`src/experiments/dynamics/pub_tsne_plots_v2.py`, and
`src/reports/plots.py`. Notable variants (letter "D" is reserved for
the perturbation-toolkit set described in §4.10 / §11.8; lettering
A-H is non-contiguous here):

- **A: joint t-SNE colored by regime / family / step**, global view of
  where the regimes and the families live in the joint embedding.
  (`plot_joint_tsne` in `dynamics/regime_plots.py`)
- **B: per-family grid**, one t-SNE panel per prompt family, sharing
  coordinates, so cross-family heterogeneity is visible.
  (`plot_trajectory_grid` in `dynamics/regime_plots.py`)
- **C: ensemble-spread timelines**, σ(t) curves per family, the visual
  analog of FTLE; useful for distinguishing contractive (shrinking spread)
  from expanding regimes. (`plot_spread_timelines` in
  `dynamics/regime_plots.py`)
- **E: per-experiment flow field** (PCA-2 quiver), averaged per-step
  displacement field overlay on the density background.
  (`plot_flow_field_*` in `dynamics/regime_plots.py`)
- **F: t-SNE trajectory sample**, sample trajectories with the
  time-ordering visible. (`plot_tsne_trajectories_single` in
  `dynamics/regime_plots.py`)
- **G/H/I: streamlines + density / speed-colored streamlines / divergence**
 , three richer flow-field views from `dynamics/field_plots.py`
  (`plot_streamlines_density`, `plot_speed_colored_streamlines`,
  `plot_divergence_field`).
- **`plot_v2_by_step_parity`** and **`plot_v2_per_family_parity_grid`**
  in `pub_tsne_plots_v2.py`, even/odd step stratification, used to
  separate the two arms of an oscillatory 2-cycle visually.
- **`plot_regime_map_by_family`** in `dynamics/partial_snapshot.py`,
  family × IC heatmap colored by final-window cluster, useful for
  detecting whether basins are family-dependent or shared.
- **`basin_entry_hist`**, **`basin_scores`**, **`cluster_occupancy`**,
  **`dwell_dist`** in `src/reports/plots.py`, distributional plots of
  the analysis primitives, one panel per observable.

Plots are rendered at 200 DPI to PNG. Each experiment's `reports/plots/`
folder ends up with 50-150 PNGs depending on the number of observables.

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
    starts_g = Z[i_0:i_{T-1}] shape (T-1, 2)
    deltas_g = Z[i_1:i_T] - Z[i_0:i_{T-1}] shape (T-1, 2)
S = concat(starts_g for all g) shape (M, 2)
D = concat(deltas_g for all g) shape (M, 2)
```

`(S, D)` is the empirical displacement-field dataset: `M` observed
single-step transitions in the projection.

We then discretize the projection bounds `[x_min - p, x_max + p]` ×
`[y_min - p, y_max + p]` (with 5% padding) into a `grid_n × grid_n`
grid (typically 26 for plots, 32-48 for animations). For each grid bin
`(i, j)` we compute:

```
count[i, j] = number of (s, d) pairs with s falling into bin (i, j)
sum_u[i, j] = sum of d_x over those pairs
sum_v[i, j] = sum of d_y over those pairs
U[i, j] = sum_u[i, j] / count[i, j] (NaN if count = 0)
V[i, j] = sum_v[i, j] / count[i, j] (NaN if count = 0)
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
resolution (~26-48), the **density** field used for V landscapes and
background heatmaps uses a higher-resolution Gaussian-smoothed
histogram via `_smooth_density_grid` in
`src/experiments/dynamics/field_plots.py`:

```
H = histogram2d(pts, bins=(x_edges, y_edges)) # raw counts, grid_n × grid_n
H_smooth = scipy.ndimage.gaussian_filter(H, sigma=sigma_cells)
```

with `grid_n = 96` and `sigma = 1.5-2.0` cells. This smoother density
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
is set to 1.6-2.0; arrowsize is small (0.9-1.2) so the density isn't
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
(`I_divergence_by_condition.png`) make this quantitative, for the O3
absorbing regime the divergence has a single deep minimum at the sink;
for O2 the divergence has a saddle structure between the two cycle
arms.

#### 4.9.5 The G/H/I plot triple

For each (experiment, projection ∈ {PCA-2, t-SNE-2}) we render three
flow-field views to `data/<exp>/reports/perturbation/`:

- **G, streamlines + density**: V (density) as the magma background;
  white streamlines from (U, V) overlaid. This is the most legible
  "where does the system flow" view.
- **H, speed-colored streamlines (dark theme)**: streamlines colored
  by local `|v| = sqrt(U² + V²)`, on a dark background. Slow regions
  (basin interiors) appear cold; fast regions (transport between
  basins) appear hot.
- **I, divergence field**: heatmap of `∇·v` with a diverging colormap
  (RdBu_r), shared color scale across all conditions of the same
  experiment for direct comparison. Streamlines overlaid in thin black.

For perturbation experiments the G/H/I are rendered per-condition
(2×2 panels = 4 conditions); for non-perturbation experiments (Phase 2
publication runs) they're rendered for the recursive regime alone,
sometimes faceted by family.

### 4.10 Perturbation visualization toolkit (summary)

For perturbation experiments we compute an empirical potential
$V(x) = -\log \hat\rho(x)$ from a Gaussian-smoothed KDE on PCA-2,
locate basin centers via 8-connected local-minima detection on $V$,
and compute geodesic barriers $V^\star$ between basin pairs via
Dijkstra shortest-path on the $V$ grid. 3D animations render
iso-density shells at five density fractions using
`skimage.measure.marching_cubes`. Full implementation details
(grid parameters, smoothing constants, alpha schedules, parallel
rendering via `ProcessPoolExecutor`) are in §11.8.

### 4.11 End-to-end pipeline diagram

The full data flow from `gpt-4o-mini` generation through embeddings,
projections, metrics, and figures, with persistence boundaries marked
as `→` (each is independently re-runnable):

```tex-raw
\noindent\textit{\small Driven by \texttt{config.yaml}: model, $T$, top-$p$, steps, observables, baselines, families.}
\flowarrow

\begin{tcolorbox}[pipelinephase={PHASE 1, GENERATION}]
Per step $t$, generate $Y_t$ from context $X_t$ via the OpenAI Responses API
(\texttt{gpt-4o-mini}, $T = 0.8$, \texttt{max\_tokens} $\in [120, 160]$,
\texttt{store=False}); then apply the nudge to produce $X_{t+1}$:
\begin{itemize}\setlength\itemsep{0pt}
  \item \textbf{Append:}\, $X_{t+1} = \operatorname{clip}(X_t \,\Vert\, Y_t,\,12000\text{ chars})$
  \item \textbf{Replace:}\, $X_{t+1} = \operatorname{clip}(Y_t,\,12000\text{ chars})$
  \item \textbf{Dialog:}\, $X_{t+1} = X_t \,\Vert\, \operatorname{format\_turn}(\text{role}, Y_t)$
\end{itemize}
Loop $t = 0,\ldots,T-1$; persist each step to \texttt{raw/steps.jsonl} as rows
\texttt{(regime, family, ic, run, step, X\_before, Y, X\_after, response\_id, \dots)}.
\end{tcolorbox}
\flowarrow

\begin{tcolorbox}[pipelinephase={PHASE 2, OBSERVABLE CONSTRUCTION}]
Per JSONL row, derive $K$ parallel string streams ($K = 3$ operator pub, $K = 8$ dialog pub;
$+1$ each with optional \texttt{context\_full}):
\begin{itemize}\setlength\itemsep{0pt}
  \item \texttt{output} $= Y_t$ (${\sim}120$ tok)
  \item \texttt{rolling\_k3} $= Y_{t-2} \,\Vert\, \mathrm{SEP} \,\Vert\, Y_{t-1} \,\Vert\, \mathrm{SEP} \,\Vert\, Y_t$
  \item \texttt{context\_tail} $=$ \texttt{X\_after[-4000:]} (${\sim}1\,$k tok)
  \item \texttt{context\_full} $=$ \texttt{X\_after[-8000:]} (${\sim}2\,$k tok)
  \item \texttt{last\_user\_turn}, \texttt{last\_agent\_turn}, \texttt{rolling\_user\_k3}, \texttt{rolling\_agent\_k3}, \texttt{turn\_pair} (dialog only)
\end{itemize}
\end{tcolorbox}
\flowarrow

\begin{tcolorbox}[pipelinephase={PHASE 3, EMBEDDING}]
For each observable independently: batch of 128 strings $\to$
\texttt{text-embedding-3-small} $\to$ list of 1536-dim vectors.
L2-normalize per row. Persist as
\texttt{embeddings/<obs>/embeddings.npy} of shape $(N,\,1536)$ and
\texttt{embeddings/<obs>/metadata.parquet} ($N$ rows; columns
\texttt{regime, family, ic, run, step, role, text\_len}).
\end{tcolorbox}
\flowarrow

\begin{tcolorbox}[pipelinephase={PHASE 4, PROJECTION (joint fit on all $N$ points per observable)}]
\begin{itemize}\setlength\itemsep{0pt}
  \item \texttt{embeddings.npy} $(N, 1536)$ \quad$\to$\quad
        \textbf{PCA(2)} $\to Z_{\mathrm{PCA2}}$ \;|\;
        \textbf{PCA(10)} $\to Z_{\mathrm{PCA10}}$ \;|\;
        \textbf{PCA(50)} $\to$ \textbf{t-SNE}(perp=30, metric=cos, init=pca, seed=42) $\to Z_{\mathrm{TSNE}}$
  \item All fits use \texttt{random\_state=42} $\Rightarrow$ fully deterministic.
  \item Routing: $Z_{\mathrm{PCA2}}$ for density / $V$ landscape / 2D plotting; $Z_{\mathrm{PCA10}}$ for K-means + metrics + classifier; $Z_{\mathrm{TSNE}}$ for visualization only (never used in metrics).
\end{itemize}
\end{tcolorbox}

\begin{center}
\begin{tikzpicture}[
  >={Stealth[length=2.6mm]}, line width=0.5pt,
  childbox/.style={draw, rectangle, rounded corners=2pt, align=left,
                   font=\footnotesize\sffamily, inner sep=4pt,
                   fill=gray!4, text width=2.85cm,
                   minimum height=2.0cm}
]
  \matrix (m) [matrix of nodes,
               column sep=4mm,
               nodes={childbox, anchor=north}] {
    {\textbf{CLUSTERING} (per obs)\\[2pt] KMeans $k{=}12$ on $Z_{\mathrm{PCA10}}$\\$\to$ cluster labels per step}
    &
    {\textbf{TIME-SERIES} (per traj)\\[2pt] recurrence, dwell, basin, basin\_entry, late\_recur, exit\_return, periodicity, dispersion}
    &
    {\textbf{ENSEMBLE} (per fam, ic)\\[2pt] Lyapunov spectrum (early/late), sharpness\_dim, effective rank}
    &
    {\textbf{PERTURBATION} (paired)\\[2pt] joint $Z_{\mathrm{PCA10}}$ + KMeans $k{=}12$\\$\to$ cluster$_T$ per cond, switching rate}
    \\
  };
  % horizontal busbar 5mm above the matrix top
  \coordinate (busL) at ([xshift=0pt, yshift=5mm] m-1-1.north);
  \coordinate (busR) at ([xshift=0pt, yshift=5mm] m-1-4.north);
  \draw (busL) -- (busR);
  % single feed arrow from above into the busbar centre
  \coordinate (busC) at ($(busL)!0.5!(busR)$);
  \draw[->] ([yshift=6mm]busC) -- (busC);
  % four drop arrows from busbar to children
  \foreach \i in {1,2,3,4} {
    \draw[->] ([yshift=5mm] m-1-\i.north) -- (m-1-\i.north);
  }
\end{tikzpicture}
\end{center}
\flowarrow

\begin{tcolorbox}[pipelinephase={PHASE 5, STATISTICAL VALIDATION}]
1000-iter bootstrap CIs, Cohen's $d$ vs baselines, permutation tests.
Baselines: \texttt{time\_shuffled} $\mid$ \texttt{no\_feedback} $\mid$ \texttt{independent\_regeneration}.
Significance gate: $\text{metric} \geq \text{baseline} + 2\sigma$ \emph{and} Cohen's $d \geq 0.5$.

Three-axis classifier ($\mathrm{H1a}$ convergence, $\mathrm{H1b}$ recurrence, $\mathrm{H1c}$ divergence):
\begin{tcolorbox}[pipelinesub={Verdicts}]
\begin{tabular}{@{}ll@{}}
$\mathrm{H1a}$ strong + $\mathrm{H1b}$ weak & $\Rightarrow$ contractive (O1) / dialogue-state multi-basin (D1)\\
$\mathrm{H1b}$ strong (period-2) & $\Rightarrow$ oscillatory (O2)\\
$\mathrm{H1a}$ strong + sharpness $\downarrow$ & $\Rightarrow$ absorbing (O3)\\
$\mathrm{H1c}$ strong & $\Rightarrow$ divergent / unsupported\\
\end{tabular}
\end{tcolorbox}
\end{tcolorbox}
\flowarrow

\begin{tcolorbox}[pipelinephase={PHASE 6, VISUALIZATION \& REPORTS}]
\begin{tcolorbox}[pipelinesub={STATIC PLOTS (2D)}]
A.~joint t-SNE by regime/family/step \;|\; B.~per-family grid \;|\; C.~single-IC trajectories \;|\; E.~quiver flow \;|\; F.~trajectory sample \;|\; basin\_entry histogram \;|\; basin\_scores \;|\; cluster\_occupancy \;|\; dwell\_dist \;|\; step\_parity.
\end{tcolorbox}
\begin{tcolorbox}[pipelinesub={FLOW FIELDS (G/H/I plot triple)}]
\texttt{make\_grid\_edges} + \texttt{bin\_displacement\_field} + \texttt{bin\_density} $\to$
G: streamlines + density (magma) \;|\; H: speed-colored streamlines (dark theme) \;|\; I: divergence $\nabla\!\cdot\!\mathbf{v}$ (RdBu\_r).
\end{tcolorbox}
\begin{tcolorbox}[pipelinesub={EMPIRICAL POTENTIAL LANDSCAPE TOOLKIT (perturbation only)}]
$Z_{\mathrm{PCA2}} \to$ smoothed density $\hat\rho(x) \to V(x) = -\log\hat\rho(x) \to$
basin centers (local minima of $V$) \;|\;
Dijkstra geodesics between basin pairs $\to V^\star(i,j) = \max V$ along path \;|\;
marching cubes at 5 density iso-levels $\to$ \texttt{Poly3DCollection} nested transparent shells \;|\;
\texttt{plot\_streamlines} + $V$ contour + geodesic overlay.
Hierarchical RG: $K = 48$ KMeans + Ward linkage $\to$ \texttt{rg\_dendrogram}.
\end{tcolorbox}
\begin{tcolorbox}[pipelinesub={3D ANIMATIONS (perturbation only)}]
$Z_{\mathrm{PCA3}}$ + iso-shells + 50-trajectory walk + red kick beams $\to$
\texttt{ProcessPoolExecutor} (40 workers) renders frame PNGs $\to$
\texttt{imageio-ffmpeg} libx264 $\to$ \texttt{animation3d\_<cond>.mp4} (${\sim}10\,$MB, 12s loop).
\end{tcolorbox}
\begin{tcolorbox}[pipelinesub={NARRATIVE REPORT}]
\texttt{reports/report.md} $\leftarrow$ per-observable metric tables, bootstrap CIs, baseline comparisons, $\mathrm{H1a}$/$\mathrm{H1b}$/$\mathrm{H1c}$ verdict, regime label.
Classification: not / weak / moderate / strong.
\end{tcolorbox}
\end{tcolorbox}
\flowarrow

\begin{tcolorbox}[pipelinephase={PHASE 7, CROSS-EXPERIMENT AGGREGATION}]
Read each experiment's per-experiment CSVs (via \texttt{scripts/lib\_load}), then:
\begin{itemize}\setlength\itemsep{0pt}
  \item \texttt{aggregate\_perturbation\_cross\_regime} $\to$ $4{\times}5$ switching grouped bar
  \item \texttt{aggregate\_dose\_response} $\to$ log-$x$ dose curves
  \item \texttt{aggregate\_basin\_hardening} $\to$ switch-vs-inject\_step
  \item \texttt{aggregate\_basin\_predictability} $\to$ 4-regime accuracy overlay
  \item \texttt{aggregate\_t\_sweep} $\to$ D1 $T \in \{0.3, 0.6, 0.8, 1.2\}$
  \item \texttt{aggregate\_o1\_d1\_t\_sensitivity} $\to$ side-by-side $T$ comparison
\end{itemize}
Output: \texttt{data/aggregated/<analysis>/\{csv, png, summary.md\}}.
\end{tcolorbox}
```

#### 4.11.1 Shape annotations through the pipeline

For one publication-scale operator experiment (1350 trajectories ×
40 steps × 4 observables ≈ 216,000 vectors):

```tex-raw
\begin{tcolorbox}[pipelinesub={\texttt{raw/steps.jsonl}}]
${\sim}54{,}000$ rows = $1350$ trajectories $\times$ $40$ steps.
\end{tcolorbox}
\flowarrow

\begin{tcolorbox}[pipelinesub={String corpus \,\textit{\small via \texttt{build\_all\_for\_run} $\times 4$ observables}}]
${\sim}216{,}000$ strings per experiment.
\end{tcolorbox}
\flowarrow

\begin{tcolorbox}[pipelinesub={Embeddings \,\textit{\small via \texttt{embed\_texts} (batched 128, retry+backoff)}}]
\texttt{embeddings/<obs>/embeddings.npy}\,:\, $(54000,\,1536)$ float32, L2-normalized.\\
\texttt{embeddings/<obs>/metadata.parquet}\,:\, $54000$ rows.
\end{tcolorbox}
\flowarrow

\begin{tcolorbox}[pipelinesub={Latent representation \,\textit{\small via PCA($n{=}10$).fit(joint) + KMeans($k{=}12$)}}]
\texttt{PCA-10}\,:\, $(54000,\,10)$ \qquad \texttt{clusters}\,:\, $(54000,)\;\in\{0\ldots11\}$.
\end{tcolorbox}
\flowarrow

\begin{tcolorbox}[pipelinesub={Per-trajectory metrics}]
\texttt{recurrence.csv}\,:\, $(1350\;\text{trajectories} \times N_{\text{metrics}}\;\text{columns})$.\\
\texttt{dwell.csv}, \texttt{basin.csv}, \texttt{basin\_entry.csv}, \texttt{exit\_return.csv}, \texttt{late\_recurrence.csv}, \texttt{periodicity.csv}, \texttt{dispersion.csv}.
\end{tcolorbox}
\flowarrow

\begin{tcolorbox}[pipelinesub={Per-(family, ic) ensemble dynamics}]
\texttt{lyapunov\_spectrum.csv}\,:\, ($15$ fam-ic pairs $\times T$ steps $\times$ top-$k\;\lambda$).\\
\texttt{sharpness\_dim.csv}\,:\, ($15$ fam-ic pairs $\times T$ steps).
\end{tcolorbox}
\flowarrow

\begin{tcolorbox}[pipelinesub={Statistical summaries \,\textit{\small via bootstrap + permutation + Cohen's $d$}}]
\texttt{bootstrap\_summary.csv}, \texttt{effect\_sizes.csv}.
\end{tcolorbox}
\flowarrow

\begin{tcolorbox}[pipelinesub={Three-axis classifier verdict}]
\texttt{ThreeAxisDecision}: $\{h_{1a},\,h_{1b},\,h_{1c}\} \in \{\texttt{not\_supported},\,\texttt{weak},\,\texttt{moderate},\,\texttt{strong}\}$.
\end{tcolorbox}
\flowarrow

\begin{tcolorbox}[pipelinesub={Reports \,\textit{\small \texttt{reports/plots}, \texttt{reports/perturbation}}}]
${\sim}70$--$150$ PNG figures $+$ (perturbation) $4$--$16$ MP4 animations.
\end{tcolorbox}
\flowarrow

\begin{tcolorbox}[pipelinesub={Cross-experiment aggregates}]
\texttt{data/aggregated/*}\,:\, cross-regime, cross-$T$, cross-dose summaries.
\end{tcolorbox}
```

#### 4.11.2 Persistence boundaries and rerun semantics

The vertical `→` arrows in the diagram are persistence boundaries:
each writes a deterministic intermediate to disk that downstream phases
read back. This means any single phase can be rerun without redoing
prior work:

| boundary | data type | re-run trigger |
|---|---|---|
| `steps.jsonl` | one JSONL row per (regime, family, ic, run, step) | re-run only if the trajectory configuration or model version changes |
| `embeddings.npy` + `metadata.parquet` | (N, 1536) float32 + N-row metadata | re-run only if observable definitions or the embedding model change |
| `pca_*.csv`, `tsne.csv` | projected coordinates | re-run only if PCA/t-SNE parameters change (random_state=42 makes this deterministic) |
| `metrics/*.csv` | per-trajectory and per-(family, ic) metrics | re-run on any metric definition change; cheap (~1 minute per experiment) |
| `reports/*.png` and `*.mp4` | rendered figures | re-run on any plotting code change; gitignored (regenerable) |

The LFS-tracked source of truth is `steps.jsonl`. Everything downstream
is regenerable from that plus the code, with a documented re-run cost
of ~\$30 in OpenAI embedding API calls and ~2 hours of local compute.

### 4.12 Hardware and software

All experiments run locally on a single workstation with API calls
to OpenAI for generation and embeddings; no GPU is required. The
host used to build the released artefacts is an HP ProLiant DL360
Gen9 with two Intel Xeon E5-2687W v3 processors (2 × 10 physical
cores at 3.10 GHz base, 40 logical threads total) and 256 GB of RAM,
running Windows 10 Pro 64-bit. Embedding ingestion, dimensionality
reduction, clustering, density-and-geodesic-barrier computation, and
animation rendering are all CPU-only.

The Python environment is Python 3.14 with numpy 2.3, scipy 1.16,
scikit-learn 1.8, scikit-image 0.26, pandas 2.3, matplotlib 3.10,
and imageio-ffmpeg 0.6 (resolved versions used to produce the
released artefacts; the code itself targets Python 3.10+). The full
dependency lock is in `requirements.txt`. Animations are stitched
via imageio-ffmpeg using the libx264 codec. The pytest suite of 99
tests is green end-to-end and runs in roughly 13 seconds in this
environment.

Parallel rendering of trajectory animations and basin diagnostics
uses `concurrent.futures.ProcessPoolExecutor` with up to 40 workers,
matching the number of logical threads on the host. The framework
makes no other hardware assumptions; the analysis pipeline runs on
any Linux, macOS, or Windows machine with the dependency stack above
and enough RAM to hold a single experiment's trajectories and PCA-10
embeddings in memory (a few GB per experiment).

### 4.13 Decision-grade endpoints

The metric battery in §4.5 is intentionally broad: it is used to
diagnose, visualize, and stress-test recursive dynamics from several
angles. The paper's headline claims, however, should not depend on
dozens of partially redundant quantities. For decision purposes, we
treat the following five endpoints as load-bearing. Each endpoint
has a fixed numerical pass rule; results that do not clear the rule
are reported as diagnostic, exploratory, or in-flight rather than as
supported regime claims. The table separates: (i) whether a regime
qualifies as attractor-like, (ii) whether its late basin is predictable
without prompt-family leakage, (iii) whether its perturbation response
has the expected regime signature, (iv) whether a token-valued barrier
is localized, and (v) whether "switching" can be interpreted as
persistent basin escape rather than final-step divergence.

```tex-raw
{\footnotesize
\begin{tabularx}{\textwidth}{@{}>{\raggedright\arraybackslash}p{2.6cm}Y>{\raggedright\arraybackslash}p{3.5cm}Y>{\raggedright\arraybackslash}p{2.6cm}@{}}
\toprule
\textbf{endpoint} & \textbf{definition} & \textbf{measured at} & \textbf{threshold for ``regime claim is supported''} & \textbf{defined in}\\
\midrule
\textbf{Operational attractor score C1--C4} &
Count of the four attractor criteria passed: late-window basin persistence, recurrence/dwell above null, embedder robustness, and contraction / re-entry / collapse. &
Publication-scale O1, O2, O3, D1 on canonical observables; D2 exploratory status checked separately. Summary table in \S3.1.3. &
\textbf{Strong attractor:} 4/4 criteria PASS. \textbf{Attractor-like:} $\geq$3/4 PASS. \textbf{Not attractor:} $<$3/4 PASS. Missing publication-scale measurements count as FAIL unless structurally inapplicable. &
\S3.1.3; metric components in \S\S4.5.1--4.5.7\\
\addlinespace[2pt]
\textbf{Leakage-free basin predictability acc\_group(k=10)} &
GroupKFold-by-prompt-family accuracy of predicting the late-window K-means basin from the PCA-10 state at step k=10. &
Publication-scale O1/O2/O3/D1, \texttt{context\_tail}, K-means k=12, \path{data/aggregated/group_aware_basin_pred.csv}. &
To claim \textbf{cross-family basin predictability}: acc\_group(k=10) $\geq$ \textbf{0.70}. To claim the original stratified number is \textbf{leakage-free}: $\Delta$ = acc\_stratified $-$ acc\_group $<$ \textbf{0.10}. &
\S4.5.10; group-aware stress test \S5.11\\
\addlinespace[2pt]
\textbf{Perturbation switching signature} &
Final-step switching rate: fraction of perturbed trajectories whose final K-means cluster differs from the paired control trajectory. &
O1 dose-response at matched 200-token dose; O2/O3/D1 perturbation pilots; \path{data/aggregated/perturbation_cross_regime/} and \path{data/aggregated/perturbation_dose_response/}. &
\textbf{O1 selective sensitivity:} S\_adv(200) $\geq$ \textbf{0.50} and S\_adv(200) / max(S\_neutral(200), S\_lorem(200)) $\geq$ \textbf{2.0}, with max OOD switching $\leq$ \textbf{0.30}. \textbf{Replace-mode capitulation:} min non-control switching across O2/O3 neutral/lorem/adversarial $\geq$ \textbf{0.85}. &
\S4.5.11; behavioral results \S\S5.5--5.8\\
\addlinespace[2pt]
\textbf{Behavioral ED50 token barrier} &
The perturbation dose $\tau$ at which a 4-parameter logistic fit to the O1 adversarial dose-response reaches 50\% switching, with prompt-family-cluster bootstrap uncertainty. &
O1 adversarial dose sweep (original sparse: $\tau \in \{20, 80, 200, 400\}$, n=50/cell; dense rerun in \S5.6.1 uses n=200/cell $\times$ 8 doses); \texttt{fit\_ed50\_hierarchical.py}; reported in \S11.1 / \S5.6. &
To claim a \textbf{localized token barrier}: ED50 point estimate finite and the 95\% family-cluster bootstrap CI lies wholly inside the probed interval \textbf{[20, 400] tokens}. If the point estimate is inside but the CI crosses the interval boundary, report only ``finite but unlocalized / in flight.'' &
Barrier definition \S3.1.1; dose protocol \S4.5.11; ED50 analysis \S5.6\\
\addlinespace[2pt]
\textbf{Persistent basin-escape rate} &
Fraction of trajectories that visibly change cluster at injection AND remain in that post-injection cluster at the terminal step. &
O1 adversarial sparse-dose sweep using \texttt{joint\_pca10\_clusters.csv}; summary in \path{data/aggregated/persistence_summary.csv}. &
To interpret switching as \textbf{persistent basin escape} rather than final-step divergence: persistent escape rate $\geq$ \textbf{0.50} at the claimed barrier dose. If $<$0.50, switching may still be reported, but not as clean basin escape. &
Switching definition \S4.5.11; persistence reanalysis \S5.15\\
\bottomrule
\end{tabularx}
}
```

On the current data, after the dense-dose rerun (§5.6.1) and the
endpoint-decomposition framework (§3.1.2):

- **Operational attractor score (C1-C4)**: O1/O2/O3/D1 pass the
  omnibus criterion; D2 does not.
- **Leakage-free basin predictability**: only O1 passes the stricter
  acc\_group(k=10) ≥ 0.70 and Δ < 0.10 rule; O2/O3/D1 fail under
  group-aware CV (§5.11).
- **Perturbation switching signature**: O1 selective sensitivity
  passes (S\_adv(200) = 0.620 in the dense rerun, ratio to
  S\_neutral/S\_lorem ≈ 2.8). Replace-mode O2/O3 capitulation passes
  by point estimate but is partly tautological (state-overwrite
  intervention; see §5.6.1 / §11.5).
- **Behavioral $\mathrm{ED50}_{\mathrm{raw}}$ token barrier**:
  **passes** at $\approx 40$ tokens (4PL=36, GLMM=41,
  bootstrap median=52); 95% CI [8.5, 242] is wide because of the
  5-family-cluster heavy tail.
- **$\mathrm{ED50}_{\mathrm{net}}$ above natural floor**: **does
  not pass**, net effect saturates at +32 pp at dose 400, below
  the +50 pp threshold (§3.1.2).
- **Persistent basin-escape rate**: **does not pass**, at dose 400,
  only 16% of trajectories are kicked-and-persisted (§5.15 dense
  data), well below the 50% threshold. So "switching" is not
  claimed as clean basin escape. The strict
  $\mathrm{ED50}_{\mathrm{persist}}$ is undefined in the tested range.

**Observable choices outside embedding clusters.** In the present
experiments, the equivalence rule $C(O(X_T))$ is a K-means cluster of
an embedding-space observable. In tool-using coding agents, the same
endpoint structure can be instantiated with engineering observables:
final patch family (`git diff --stat`), files touched, the
failing/passing test set, the selected plan category, the tool-call
sequence, a security-policy violation, or an embedding of the full
trajectory trace. Algorithm 1 (§4.5.11) requires only a consistent,
pre-specified equivalence rule and paired controls; it does not require
that "cluster" literally mean an embedding cluster. This is what makes
the three-endpoint decomposition portable across application domains.

---
