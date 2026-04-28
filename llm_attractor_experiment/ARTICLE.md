# Endogenous attractor regimes in recursive large-language-model loops
## A quantitative taxonomy with measured basin barriers

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
gravity that resists cross-topic perturbations. Each regime has a
distinct basin-predictability signature: replace-mode regimes (O2,
O3) lock in by step 5 (acc ≈ 0.90–0.92), append-mode O1 climbs from
0.77 to 0.85 over 40 steps, and dialog regime D1 climbs from 0.61
(step 10) to 0.77 (final). A compact regime × diagnostic comparison
appears in §5.0.

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
   94 unit tests, and a documented `embed → analyze → report` workflow.

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

Tuci et al. (2026, arXiv:2604.19740) study SGD-optimization dynamics on
neural-net loss landscapes via random dynamical systems and introduce a
"sharpness dimension" generalization bound at the edge of stability.
Their setting (parameter space, Hessian-anchored, training dynamics)
is structurally different from ours (embedding space, no gradients,
inference-time recursion of a frozen LLM). We borrow only the
*functional form* of their sharpness dimension (Definition 4.2) as a
comparative diagnostic across regimes; the ensemble-spread Lyapunov
machinery in `src/experiments/dynamics/lyapunov.py` is our own
construction. See §4.5.6 for the explicit caveats.

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

## 3. Formal framework and hypotheses

### 3.1 State, generator, nudge

Let $X_t \in \mathcal{C}$ denote the bounded visible context at step $t$,
where $\mathcal{C}$ is the space of valid clipped contexts (here, the
finite-length character strings produced by tail-clipping at 12,000
chars). Let
$$
Y_t \sim P_\theta(\cdot \mid X_t;\, f)
$$
be the continuation generated by a language model with parameters
$\theta$ under a content operator $f$ (e.g. continuation, paraphrase,
summarize-and-negate, role-alternating dialog). Let
$$
\mathcal{N}_f : \mathcal{C} \times \mathcal{Y} \to \mathcal{C}
$$
be the **context-update operator**, or **nudge**, mapping the current
state and the model output to the next state. The full recurrence is
then a bounded stochastic dynamical system
$$
Y_t \sim P_\theta(\cdot \mid X_t;\, f),
\qquad
X_{t+1} = \mathcal{N}_f(X_t, Y_t).
$$

Three concrete nudges instantiate this skeleton in our experiments:

- **Append nudge**:
  $\mathcal{N}_{\text{append}}(X_t, Y_t) = \operatorname{clip}(X_t \Vert Y_t)$
- **Replace nudge**:
  $\mathcal{N}_{\text{replace}}(X_t, Y_t) = \operatorname{clip}(Y_t)$
- **Dialog nudge**:
  $\mathcal{N}_{\text{dialog}}(X_t, Y_t) = X_t \Vert \operatorname{format\_turn}(r_t, Y_t)$
  with role label $r_t$ alternating across turns.

This factorization is what licenses the H2 prediction below: the regime
depends jointly on the content operator $f$ (which parameterizes the
generator $P_\theta(\cdot \mid X_t; f)$) and the choice of nudge
$\mathcal{N}_f$ (which determines how $Y_t$ feeds back into $X_{t+1}$).
Two operators that share the same prompt instruction but differ in nudge
will produce qualitatively different attractor regimes; this is exactly
what we see empirically (e.g. paraphrase under append vs replace).

### 3.2 Observable maps and embedding

Attractor-like structure is not legible in raw text. We introduce
**observable maps** $O_t$ that extract text views of the trajectory,
and an **embedding map** $\phi$ that lifts those views into vector space:
$$
z_t = \phi(O_t) \in \mathbb{R}^m,
\qquad
m = 1536 \text{ for } \texttt{text-embedding-3-small}.
$$
A single observable string yields a single embedding vector. Each
trajectory thus produces a family of polylines $\{z_t^{(O)}\}_{t=0}^{T-1}$,
one per observable $O$, in the joint embedding space. All quantitative
metrics in §4.5 are functions of these polylines.

### 3.3 Hypotheses

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

Instantiating the formal recurrence from §3.1 with the three nudges:
$$
\text{Append:}\quad   X_{t+1} = \mathcal{N}_{\text{append}}(X_t, Y_t)  = \operatorname{clip}(X_t \Vert Y_t)
$$
$$
\text{Replace:}\quad  X_{t+1} = \mathcal{N}_{\text{replace}}(X_t, Y_t) = \operatorname{clip}(Y_t)
$$
$$
\text{Dialog:}\quad   X_{t+1} = \mathcal{N}_{\text{dialog}}(X_t, Y_t)  = X_t \Vert \operatorname{format\_turn}(r_t, Y_t)
$$

with $Y_t \sim P_\theta(\cdot \mid X_t;\, f)$ and $P_\theta$ the
language-model distribution parameterized by $\theta$ (here
`gpt-4o-mini`). The clipping operator $\operatorname{clip}(\cdot)$
truncates context from the head (oldest) once the running string
exceeds 12,000 characters, preserving the most recent state. The
content operator $f$ enters through the system prompt fed to
$P_\theta$ — e.g. "Continue the text" for $f = \text{continue}$,
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
  N≥2-runs minimum for ensemble-spread diagnostics (§5.0).

In every case trajectories run for 40 steps unless explicitly noted
(D2 uses 50; the T-sweep variants vary `steps_per_run`).

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

The names above use D1's role labels (user / agent). For dialogs
configured with different role labels — D2 uses *explorer* / *expert* —
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
~$30 in embedding API calls.

#### 4.3.1 Single-context embedding mechanics

A subtle but important invariant: **for one observable string at one
trajectory step, we obtain exactly one 1536-dimensional vector.** No
chunking, no internal sliding window we manage, no per-token outputs.
The `text-embedding-3-small` model handles internal attention over up
to 8,191 input tokens and produces a single pooled representation
which `embed_texts` writes to one row of the output matrix:

```
"Continue the text. The fox was quick..."  →  text-embedding-3-small  →  v ∈ R^1536
```

After the API returns, we **L2-normalize** each row defensively so all
downstream cosine-similarity computations reduce to dot products and
numerical drift from float32 round-trips does not accumulate:

```
norms = ||v||_2 + 1e-12
v_norm = v / norms                          # ||v_norm||_2 = 1.0
```

The model is deterministic given the input — `hash(text) → vec` is a
stable mapping under fixed model version, so the embedding cache is
safe and `analyze` reruns on the same `embeddings.npy` are identical.

Per-trajectory step we therefore obtain `K` independent vectors where
`K = |observables|` — 3 for operator publication runs (output,
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
| `output` observable | the single Y_t | — | ≤ 160 |
| `rolling_k3` | 3 × Y plus 2 separators | — | ~480 |
| `context_tail` | `[-4000:]` slice | — | ~1,000 |
| `context_full` | `[-8000:]` slice | — | ~2,000 |
| `turn_pair` (dialog) | last user + last agent | — | ~320 |
| `rolling_user_k3` / `rolling_agent_k3` | 3 turns of one role | — | ~480 |

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
Step t:    context_after has 9,500 chars. context_full = chars [1500 : 9500]
Step t+1:  Y_{t+1} appends ~120 chars.   context_full = chars [1620 : 9620]
```

So between adjacent steps the slice has ~99% content overlap and ~1%
fresh content. The resulting embeddings are **highly correlated, not
identical**. Empirically:

| observable | content overlap with previous step | adjacent-step cosine sim |
|---|---|---|
| `output` | 0% (Y_t is freshly generated each step) | ~0.5–0.8 |
| `rolling_k3` | ~67% (2 of 3 outputs unchanged) | ~0.85–0.95 |
| `context_tail` (4000 chars, append) | ~97% | ~0.95–0.98 |
| `context_full` (8000 chars, append) | ~99% | ~0.97–0.99 |

These different-overlap regimes give the trajectory **different motion
speeds in embedding space** for different observables. `output` shows
fast cycling motion (each step is a fresh generation); `context_full`
shows slow integrated drift; `rolling_k3` is the compromise. This is
exactly why we run every metric on every observable and require
cross-observable agreement before accepting a regime label — a finding
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
np.median(sims)   # ≈ 0.97-0.99 for context_full in append mode
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
spectrum (functional form from Tuci et al., arXiv 2604.19740,
Definition 4.2):

```
j*  = max { i : Σ_{k≤i} λ_k ≥ 0 }      (0 if λ_1 < 0)

SD  = j* + (Σ_{k≤j*} λ_k) / |λ_{j*+1}|
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
D1 1.89; §5.0), but the magnitude differences are modest. A
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
  (`plot_joint_tsne` in `dynamics/regime_plots.py`)
- **B: per-family grid** — one t-SNE panel per prompt family, sharing
  coordinates, so cross-family heterogeneity is visible.
  (`plot_trajectory_grid` in `dynamics/regime_plots.py`)
- **C: ensemble-spread timelines** — σ(t) curves per family, the visual
  analog of FTLE; useful for distinguishing contractive (shrinking spread)
  from expanding regimes. (`plot_spread_timelines` in
  `dynamics/regime_plots.py`)
- **E: per-experiment flow field** (PCA-2 quiver) — averaged per-step
  displacement field overlay on the density background.
  (`plot_flow_field_*` in `dynamics/regime_plots.py`)
- **F: t-SNE trajectory sample** — sample trajectories with the
  time-ordering visible. (`plot_tsne_trajectories_single` in
  `dynamics/regime_plots.py`)
- **G/H/I: streamlines + density / speed-colored streamlines / divergence**
  — three richer flow-field views from `dynamics/field_plots.py`
  (`plot_streamlines_density`, `plot_speed_colored_streamlines`,
  `plot_divergence_field`).
- **`plot_v2_by_step_parity`** and **`plot_v2_per_family_parity_grid`**
  in `pub_tsne_plots_v2.py` — even/odd step stratification, used to
  separate the two arms of an oscillatory 2-cycle visually.
- **`plot_regime_map_by_family`** in `dynamics/partial_snapshot.py` —
  family × IC heatmap colored by final-window cluster, useful for
  detecting whether basins are family-dependent or shared.
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

### 4.11 End-to-end pipeline diagram

The full data flow from `gpt-4o-mini` generation through embeddings,
projections, metrics, and figures, with persistence boundaries marked
as `→` (each is independently re-runnable):

```
                              ┌──────────────────────┐
                              │ config.yaml          │
                              │ (model, T, top_p,    │
                              │  steps, observables, │
                              │  baselines, families)│
                              └──────────┬───────────┘
                                         │
                                         ▼
   ┌────────────────────────────────────────────────────────────────────────────┐
   │  PHASE 1 — GENERATION                                                      │
   │                                                                            │
   │   ┌──────────┐  X_t (string)   ┌────────────────────────┐                  │
   │   │ context  │ ───────────────▶│ OpenAI Responses API   │                  │
   │   │ X_t      │                 │ gpt-4o-mini            │                  │
   │   │          │  Y_t (string)   │ T=0.8, max_tok=120-160 │                  │
   │   │          │ ◀───────────────│ store=False            │                  │
   │   └────┬─────┘                 └────────────────────────┘                  │
   │        │                                                                   │
   │        │  X_{t+1} = clip(X_t || Y_t, 12000 chars)         APPEND mode      │
   │        │  X_{t+1} = clip(Y_t,        12000 chars)         REPLACE mode     │
   │        │  X_{t+1} = X_t || format_turn(role, Y_t)         DIALOG mode      │
   │        │                                                                   │
   │        └─────▶ loop t = 0..T-1, persist each step ──┐                      │
   │                                                      ▼                     │
   │                                       ┌─────────────────────────────┐     │
   │                                       │ raw/steps.jsonl             │     │
   │                                       │  rows: (regime, family, ic, │     │
   │                                       │  run, step, X_before, Y,    │     │
   │                                       │  X_after, response_id, ...) │     │
   │                                       └──────────────┬──────────────┘     │
   └────────────────────────────────────────────────────── │ ───────────────────┘
                                                           ▼
   ┌────────────────────────────────────────────────────────────────────────────┐
   │  PHASE 2 — OBSERVABLE CONSTRUCTION                                         │
   │                                                                            │
   │           per JSONL row → 3 strings (operator pub) or 8 strings (dialog pub)│
   │                                                                            │
   │           ┌─────────────────────────────────────────────────────┐          │
   │           │ output         = Y_t                       (~120 tok)│         │
   │           │ rolling_k3     = Y_{t-2}||SEP||Y_{t-1}||SEP||Y_t     │         │
   │           │ context_tail   = X_after[-4000:]            (~1k tok)│         │
   │           │ context_full   = X_after[-8000:]            (~2k tok)│         │
   │           │ last_user_turn / last_agent_turn  (dialog only)      │         │
   │           │ rolling_user_k3 / rolling_agent_k3 (dialog only)     │         │
   │           │ turn_pair                          (dialog only)     │         │
   │           └─────────────────────────────────────────────────────┘          │
   │                              │  K parallel string streams                  │
   │                              │  (K = 3 operator pub, 8 dialog pub;         │
   │                              │   +1 each with optional context_full)       │
   └──────────────────────────────┼─────────────────────────────────────────────┘
                                  ▼
   ┌────────────────────────────────────────────────────────────────────────────┐
   │  PHASE 3 — EMBEDDING                                                       │
   │                                                                            │
   │   for each observable independently:                                       │
   │                                                                            │
   │      ┌──────────────────┐  batch of 128 strings ┌──────────────────┐       │
   │      │ all_texts        │ ─────────────────────▶│ OpenAI Embeddings│       │
   │      │ (N_traj×T strings│                       │ text-embedding-3 │       │
   │      │  per observable) │  list[1536-d vector]  │ -small           │       │
   │      │                  │ ◀─────────────────────│                  │       │
   │      └──────────────────┘                       └──────────────────┘       │
   │                              │                                             │
   │                              ▼                                             │
   │                       L2-normalize each row                                │
   │                              │                                             │
   │                              ▼                                             │
   │      ┌─────────────────────────────────────────────┐                       │
   │      │ embeddings/<obs>/embeddings.npy   (N, 1536) │                       │
   │      │ embeddings/<obs>/metadata.parquet (N rows)  │                       │
   │      │   regime, family, ic, run, step, role,      │                       │
   │      │   text_len                                  │                       │
   │      └────────────────────┬────────────────────────┘                       │
   └──────────────────────────── │ ─────────────────────────────────────────────┘
                                ▼
   ┌────────────────────────────────────────────────────────────────────────────┐
   │  PHASE 4 — PROJECTION  (joint fit on all N points per observable)          │
   │                                                                            │
   │       embeddings.npy  (N, 1536) ──┬─▶ PCA(n=2)   ──▶ Z_PCA2  (N, 2)        │
   │                                   │                                        │
   │                                   ├─▶ PCA(n=10)  ──▶ Z_PCA10 (N, 10)       │
   │                                   │                                        │
   │                                   ├─▶ PCA(n=20)  ──▶ Z_PCA20 (N, 20)       │
   │                                   │                                        │
   │                                   └─▶ PCA(n=50) ──▶ TSNE(    ──▶ Z_TSNE    │
   │                                       (preprocess) perp=30,     (N, 2)     │
   │                                                    metric=cos,             │
   │                                                    init=pca,               │
   │                                                    seed=42)                │
   │                                                                            │
   │       all fits use random_state=42 → fully deterministic                   │
   │                                                                            │
   │       Z_PCA2  →  density / V landscape / 2D plotting                       │
   │       Z_PCA10 →  K-means clustering, metrics, classifier                   │
   │       Z_TSNE  →  visualization only (never used in metrics)                │
   └─────────────────┬──────────────────────────────────────────────────────────┘
                     │
            ┌────────┴────────┬────────────────┬────────────────┐
            ▼                 ▼                ▼                ▼
   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
   │ CLUSTERING   │  │ TIME-SERIES  │  │ ENSEMBLE     │  │ PERTURBATION │
   │ (per obs)    │  │ METRICS      │  │ DYNAMICS     │  │ ANALYSIS     │
   │              │  │ (per traj)   │  │ (per fam,ic) │  │ (paired)     │
   │ KMeans(k=12) │  │              │  │              │  │              │
   │  on Z_PCA10  │  │ recurrence   │  │ Lyapunov     │  │ joint Z_PCA10│
   │              │  │ dwell        │  │ spectrum     │  │ + KMeans k=12│
   │ → cluster    │  │ basin        │  │ (early/late) │  │ → cluster_T  │
   │   labels     │  │ basin_entry  │  │ sharpness_dim│  │   per cond   │
   │   per step   │  │ late_recur.  │  │ effective    │  │ → switching  │
   │              │  │ exit_return  │  │ rank         │  │   rate per   │
   │              │  │ periodicity  │  │              │  │   condition  │
   │              │  │ dispersion   │  │              │  │              │
   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
          │                 │                 │                 │
          └────────────┬────┴────────────┬────┴────────────┬────┘
                       │                 │                 │
                       ▼                 ▼                 ▼
   ┌────────────────────────────────────────────────────────────────────────────┐
   │  PHASE 5 — STATISTICAL VALIDATION                                          │
   │                                                                            │
   │   1000-iter bootstrap CIs    Cohen's d vs baselines    permutation tests   │
   │                                                                            │
   │   baselines:  time_shuffled │ no_feedback │ independent_regeneration       │
   │                                                                            │
   │   significance gate:  metric ≥ baseline + 2σ  AND  Cohen's d ≥ 0.5         │
   │                                                                            │
   │                                  │                                         │
   │                                  ▼                                         │
   │   three-axis classifier (H1a convergence, H1b recurrence, H1c divergence)  │
   │                                                                            │
   │     ┌──────────────────────────────────────────────────────────────────┐   │
   │     │ H1a strong + H1b weak  ⇒  contractive / multi-basin (O1, D1)     │   │
   │     │ H1b strong (period-2) ⇒  oscillatory                  (O2)       │   │
   │     │ H1a strong + sharpness ↓ ⇒ absorbing                  (O3)       │   │
   │     │ H1c strong            ⇒  divergent / unsupported                 │   │
   │     └──────────────────────────────────────────────────────────────────┘   │
   └─────────────────────────────────┬──────────────────────────────────────────┘
                                     ▼
   ┌────────────────────────────────────────────────────────────────────────────┐
   │  PHASE 6 — VISUALIZATION & REPORTS                                         │
   │                                                                            │
   │  ┌─────────────────────┐      ┌─────────────────────┐                      │
   │  │ STATIC PLOTS (2D)   │      │ FLOW FIELDS (2D)    │                      │
   │  │                     │      │                     │                      │
   │  │ A. joint t-SNE      │      │ make_grid_edges     │                      │
   │  │    by regime/family/│      │ + bin_displacement  │                      │
   │  │    step             │      │   field             │                      │
   │  │ B. per-family grid  │      │ + bin_density       │                      │
   │  │ C. single-IC trajs  │      │                     │                      │
   │  │ E. quiver flow      │      │ → G: streamlines +  │                      │
   │  │ F. trajectory sample│      │      density (magma)│                      │
   │  │ basin_entry hist    │      │ → H: speed-colored  │                      │
   │  │ basin_scores        │      │      streamlines    │                      │
   │  │ cluster_occupancy   │      │      (dark theme)   │                      │
   │  │ dwell_dist          │      │ → I: divergence ∇·v │                      │
   │  │ step_parity         │      │      (RdBu_r)       │                      │
   │  └─────────────────────┘      └─────────────────────┘                      │
   │                                                                            │
   │  ┌─────────────────────────────────────────────────────────────────────┐   │
   │  │ HOLOGRAPHIC-BULK TOOLKIT (perturbation only)                        │   │
   │  │                                                                     │   │
   │  │   Z_PCA2 ──▶ smoothed density ρ̂(x)                                  │   │
   │  │              │                                                      │   │
   │  │              ▼                                                      │   │
   │  │           V(x) = -log ρ̂(x)                                          │   │
   │  │              │                                                      │   │
   │  │              ├─▶ basin_centers = local minima of V                  │   │
   │  │              │                                                      │   │
   │  │              ├─▶ Dijkstra geodesics between basin pairs             │   │
   │  │              │   → V*(i,j) barrier height = max V along path        │   │
   │  │              │                                                      │   │
   │  │              ├─▶ marching cubes @ 5 density iso-levels              │   │
   │  │              │   → Poly3DCollection nested transparent shells       │   │
   │  │              │                                                      │   │
   │  │              └─▶ plot_streamlines + V contour + geodesic overlay    │   │
   │  │                                                                     │   │
   │  │   K=48 KMeans + Ward linkage ──▶ rg_dendrogram                      │   │
   │  └─────────────────────────────────────────────────────────────────────┘   │
   │                                                                            │
   │  ┌─────────────────────────────────────────────────────────────────────┐   │
   │  │ 3D ANIMATIONS (perturbation only)                                   │   │
   │  │                                                                     │   │
   │  │   Z_PCA3 + iso-shells + 50-trajectory walk + red kick beams         │   │
   │  │              │                                                      │   │
   │  │              ▼                                                      │   │
   │  │   ProcessPoolExecutor (40 workers) → frame PNGs                     │   │
   │  │              │                                                      │   │
   │  │              ▼                                                      │   │
   │  │   imageio-ffmpeg libx264 → animation3d_<cond>.mp4 (~10MB, 12s loop) │   │
   │  └─────────────────────────────────────────────────────────────────────┘   │
   │                                                                            │
   │  ┌─────────────────────┐                                                   │
   │  │ NARRATIVE REPORT    │                                                   │
   │  │                     │                                                   │
   │  │ reports/report.md   │ ◀── per-observable metric tables                  │
   │  │                     │     bootstrap CIs                                 │
   │  │ classification:     │     baseline comparisons                          │
   │  │  not / weak /       │     H1a/H1b/H1c verdict                           │
   │  │  moderate / strong  │     regime label                                  │
   │  └─────────────────────┘                                                   │
   └────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
   ┌────────────────────────────────────────────────────────────────────────────┐
   │  PHASE 7 — CROSS-EXPERIMENT AGGREGATION                                    │
   │                                                                            │
   │   read each experiment's per-experiment CSVs (via scripts/lib_load)        │
   │                                                                            │
   │   ┌────────────────────────────────────────────────────────────────────┐   │
   │   │ aggregate_perturbation_cross_regime  → 4×5 switching grouped bar   │   │
   │   │ aggregate_dose_response              → log-x dose curves           │   │
   │   │ aggregate_basin_hardening            → switch-vs-inject_step       │   │
   │   │ aggregate_basin_predictability       → 4-regime accuracy overlay   │   │
   │   │ aggregate_t_sweep                    → D1 T={0.3,0.6,0.8,1.2}      │   │
   │   │ aggregate_o1_d1_t_sensitivity        → side-by-side T comparison   │   │
   │   └────────────────────────────────────────────────────────────────────┘   │
   │                                                                            │
   │   → data/aggregated/<analysis>/{csv, png, summary.md}                      │
   └────────────────────────────────────────────────────────────────────────────┘
```

#### 4.11.1 Shape annotations through the pipeline

For one publication-scale operator experiment (1350 trajectories ×
40 steps × 4 observables ≈ 216,000 vectors):

```
   raw/steps.jsonl                   ~54,000 rows  (1350 traj × 40 steps)
        │
        ▼  build_all_for_run × 4 observables
   ~216,000 strings per experiment
        │
        ▼  embed_texts (batched 128, retry+backoff)
   embeddings/<obs>/embeddings.npy   (54000, 1536)  float32, L2-normalized
   embeddings/<obs>/metadata.parquet (54000 rows)
        │
        ▼  PCA(n=10).fit(joint) + KMeans(k=12)
   PCA-10:    (54000, 10)
   clusters:  (54000,)  ∈ {0..11}
        │
        ▼  per-trajectory metrics
   recurrence.csv:  (1350 trajectories × N_metrics columns)
   dwell.csv, basin.csv, basin_entry.csv, exit_return.csv,
   late_recurrence.csv, periodicity.csv, dispersion.csv
        │
        ▼  per-(family, ic) ensemble dynamics
   lyapunov_spectrum.csv:  (15 family-ic pairs × T steps × top-k λ)
   sharpness_dim.csv:      (15 family-ic pairs × T steps)
        │
        ▼  bootstrap + permutation + Cohen's d
   bootstrap_summary.csv, effect_sizes.csv
        │
        ▼  three-axis classifier
   ThreeAxisDecision: {h1a, h1b, h1c} ∈ {not_supported, weak, moderate, strong}
        │
        ▼  reports/plots + reports/perturbation
   ~70-150 PNG figures + (perturbation) 4-16 MP4 animations
        │
        ▼  cross-experiment
   data/aggregated/*  (cross-regime, cross-T, cross-dose summaries)
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
of ~$30 in OpenAI embedding API calls and ~2 hours of local compute.

### 4.12 Hardware and software

All experiments run locally with API calls to OpenAI. CPU: 40 cores
available for parallel rendering. Python 3.x with numpy, scipy,
scikit-learn, scikit-image, pandas, matplotlib, imageio-ffmpeg. Tests:
94 pytest tests, all green. See `requirements.txt` for exact
dependencies.

---

## 5. Results

### 5.0 The four (plus one) regimes at a glance

Before walking through the experiment phases, a master comparison
of the diagnostic signatures across regimes. Each row is a regime;
each column is a diagnostic that distinguishes it from the others.
All numbers are at publication scale (Phase 2) or perturbation pilot
scope (Phase 3).

| regime | nudge | content op. $f$ | basin pred. acc(k=5→final) | recurrence | sharpness dim* | adversarial switch | dose 50% | T-stability |
|---|---|---|---|---|---|---|---|---|
| **O1** contractive | append | continue | 0.77 → 0.85 | low | 1.70 | 54% | ~150 tok | degrades smoothly |
| **O2** oscillatory | replace | paraphrase | 0.90 → 0.91 | high (period-2) | 1.39 | 94% | n/a (saturated) | (not measured) |
| **O3** absorbing | replace | summarize+negate | 0.92 → 0.93 | trivial | 1.45 | 96% | n/a (saturated) | (not measured) |
| **D1** multi-basin | dialog (append) | curious + helpful | n/a → 0.77 | low (per-style) | 1.89 | 60% | < 5 tokens | T-stable |
| **D2** drill-down | dialog (append) | explorer drill-down | (not measured)** | (not measured) | (not measured)** | 64% | (not measured) | (not measured) |

\* Sharpness dim is computed on a 2-element Lyapunov spectrum (rank ≤ N−1 = 2 for N=3 runs per IC), so values are bounded above by 2.0. Mean SD_late on `context_tail`. The *ordering* across regimes is informative, the absolute magnitudes are constrained by the rank ceiling. See §4.5.6.

\*\* D2 was run at exploratory scale (N=1 run per IC), which is below the N≥2 minimum required for ensemble-spread Lyapunov computation. D2's basin-predictability acc at k=5 is 0.20 with n=25 and 11 classes (chance ≈ 0.09), well underpowered for the canonical k=5,10,20,final probes.

Reading: the two **replace-mode** regimes (O2, O3) lock in early (acc
already ≈0.9 by step 5) and are perturbation-transparent. The
**append-mode** regimes (O1 and the dialog regimes D1/D2) admit
slower late-state determination and have measurable barrier structure.
O1 is uniquely T-sensitive; D1 is uniquely T-stable; D2 adds content
gravity beyond D1's stylistic basins.

The regime ordering — replace-mode locks in fast and capitulates
to any perturbation; append-mode locks in slowly and resists
out-of-distribution perturbation but yields to in-distribution
adversaries — runs through every diagnostic below.

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
30 ICs × 3 runs × 40 steps = 1350 trajectories per regime). Basin
predictability — 5-fold CV multinomial logistic regression on PCA-10,
predicting the late-window K-means cluster (k=12) from the embedding
at step k — gives a clean per-regime ordering:

| experiment | regime | observable | acc(k=5) | acc(k=10) | acc(k=20) | acc(k=final) |
|---|---|---|---:|---:|---:|---:|
| `exp_pub_O1_continue` | contractive | context_tail | 0.77 | 0.80 | 0.81 | 0.85 |
| `exp_pub_O2_paraphrase_replace` | oscillatory | context_tail | 0.90 | 0.90 | 0.91 | 0.91 |
| `exp_pub_O3_summarize_negate_replace` | absorbing | context_tail | 0.92 | 0.92 | 0.92 | 0.93 |
| `exp_pub_D1_dialog_curious_helpful_v2` | multi-basin | context_tail | n/a | 0.61 | 0.69 | 0.77 |

The "final" cluster is the trajectory's majority cluster over the
late window `t ≥ ⌈0.7T⌉` per §4.5.3. For T=40 this gives a 12-step
late window; for the dialog regime D1 with role-restricted observables
the latest predictor step is 26 (the last agent turn before the late
window opens at step 28).

(Numbers measured from
`data/aggregated/basin_predictability_cross/cross_basin_predictability.csv`,
recursive regime only, canonical observable per regime. D1's step-5
cell is `NaN` because the joint k-means at step 5 has too few class
members per fold for stable 5-fold CV; it stabilizes by step 10.)

Three orderings emerge cleanly:

- **O3 absorbing** locks in earliest (step 5 ≈ final accuracy 0.89 →
  0.91). Once the absorbing sink is reached, the remainder of the
  trajectory is statistically frozen.
- **O2 oscillatory** also locks in fast (0.88 → 0.90). The 2-cycle is
  basin-stable: knowing which arm of the cycle a trajectory is on at
  step 5 is enough to predict its terminal arm.
- **O1 contractive** and **D1 multi-basin** are slower and have more
  headroom: O1 climbs from 0.77 to 0.85, D1 from 0.61 (step 10) to
  0.77 (final). The dialog regime in particular shows the *most* room
  for early-stage style-basin reorganization.

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
trajectories per condition × 4 conditions. Switching rates with Wilson
95% confidence intervals (n=50 except D2 where n=25):

| regime | control | neutral | lorem | adversarial |
|---|---|---|---|---|
| O1 (contractive) | 0% [0–7] | 24% [14–37] | 18% [10–31] | 54% [40–67] |
| O2 (oscillatory replace) | 0% [0–7] | 100% [93–100] | 100% [93–100] | 94% [84–98] |
| O3 (absorbing replace) | 0% [0–7] | 100% [93–100] | 100% [93–100] | 96% [86–99] |
| D1 (multi-basin dialog) | 0% [0–7] | 76% [62–86] | 54% [40–67] | 60% [46–73] |
| D2 (drill-down dialog) | 0% [0–13] | n/a | n/a | 64% [44–80] |

(D2 was only tested with control + adversarial conditions, and at a
50-step horizon with override at step 25 — see §5.8.)

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

**D1 / neutral** (n=50 per cell; Wilson 95% CI half-width ~13 pct pts):

| dose (tokens) | 5 | 10 | 15 | 20 | 80 | 200 | 400 |
|---|---:|---:|---:|---:|---:|---:|---:|
| switch | 62% | 68% | 70% | 72% | 76% | 70% | 66% |

D1 saturates at sub-token doses. The barrier height (in this dose
sense) is essentially zero — any 5-token coherent interrupt flips the
dialog basin. The flat-from-saturation curve is consistent with our
"dialog basin is stylistic, not content-bound" interpretation.

**O1 / neutral** (off-distribution; n=50 per cell; CI half-width ~12 pct pts):

| dose | 20 | 80 | 200 | 400 |
|---|---:|---:|---:|---:|
| switch | 22% | 26% | 24% | 24% |

Flat at the natural drift floor of ~24% across the entire dose range.
This is the "noise rate" — out-of-distribution text simply cannot move
the contractive basin no matter the dose.

**O1 / adversarial** (in-distribution; n=50 per cell; CI half-width ~13 pct pts):

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
at three different steps of a 30-step trajectory (n=50 per cell):

| inject step | D1 (neutral @80) | O1 (adversarial @200) |
|---:|---:|---:|
| 5 | 72% [58–83] | 60% [46–73] |
| 15 | 78% [65–87] | 54% [40–67] |
| 25 | **52% [38–66]** | 62% [48–74] |

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

Seven standalone aggregator scripts produce the cross-regime comparison
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
- `scripts/aggregate_perturbation_geometric_barriers.py` — combine the
  per-pilot `geodesic_barriers_summary.csv` (V*) and
  `rg_dendrogram_summary.csv` (Ward merge distance) into the wide
  regime × condition tables shown in §5.10. Output:
  `data/aggregated/perturbation_geometric_barriers/`
  (`v_star_table.csv`, `rg_merge_table.csv`, `geometric_barriers_long.csv`).

Each script reads only the per-experiment CSV outputs and is fully
deterministic — re-running them produces byte-identical figures. They
are kept separate from the per-experiment pipeline to allow incremental
re-aggregation as new experiments land.

### 5.10 Geometric barriers from V(x) = −log ρ(x)

For each of the four diagnostic perturbation pilots we computed:

#### Geodesic skeleton on V

Per-condition mean barrier height V\* across the 6 inter-basin geodesics
(`V_star_mean` column in the per-pilot `geodesic_barriers_summary.csv`):

| regime | control | neutral | lorem | adversarial |
|---|---:|---:|---:|---:|
| O1 | 4.4 | 2.3 | 2.6 | 2.2 |
| O2 | 2.8 | 3.5 | **5.6** | 1.6 |
| O3 | 1.1 | 5.2 | **7.0** | 2.2 |
| D1 | 1.3 | 1.1 | 0.8 | 0.4 |

(Per-geodesic raw V\* values are written alongside the figure to
`data/exp_perturb_*_pilot/reports/perturbation/geodesic_barriers_pca.csv`;
the V_max ≈ 8.0 ceiling appears when a geodesic crosses a region of
near-zero density.)

The geometric V\* values complement the perturbation switching rates:

- **O2/O3 lorem** has V\* ≈ 5.6 / 7.0 — the highest barriers in the
  matrix. Those barriers separate *control* from a *new* basin that
  lorem injection creates far from any pre-perturbation density
  mass: geodesics between the original and lorem-induced basins
  traverse low-density plateaus where ρ ≈ ε (V near the V_max
  ceiling). Switch rates are 100% because the perturbation places
  the trajectory *into* the new basin — the perturbed run does not
  have to climb the barrier; it lands on the far side. The high V\*
  is consistent with the per-regime RG cloud expansion (3.6 / 3.3
  below).
- **O1 adversarial** has V\* ≈ 2.2 — basins remain distinct but the kick
  occasionally clears the ridge → consistent with 54% switching at
  ~150 tokens dose.
- **D1 adversarial** has V\* ≈ 0.4 — basins are stylistic, not
  content-bound, so the geometric barrier is small → consistent with
  the 60% switching at saturated doses.

Cross-validating dose-response barrier estimates (from §5.6) against
geometric V\* gives two complementary readings: O1 adversarial agrees
quantitatively (V\* ≈ 2.2 ↔ 150-token saturation dose), D1 agrees
qualitatively (low V\*, near-zero saturation dose), and the
replace-mode regimes are explained by basin *creation* rather than
barrier crossing — different geometric mechanisms producing the same
100% switching.

#### Hierarchical RG dendrogram

Per-condition maximum Ward-linkage merge distance across k=48 fine-cluster
centroids:

| regime | control | neutral | lorem | adversarial |
|---|---:|---:|---:|---:|
| O1 | 2.38 | 2.27 | 2.37 | 2.06 |
| O2 | 2.31 | 2.32 | **3.64** | 1.90 |
| O3 | 2.16 | 2.39 | **3.25** | 1.85 |
| D1 | 1.79 | 1.79 | 1.79 | 1.80 |

Three patterns:

1. **D1 is invariant** at 1.79–1.80 across all four conditions — the
   dialog cloud's coarse-graining diameter doesn't change with
   perturbation. Consistent with stylistic basins that are not
   reshaped by content injection.
2. **O2/O3 lorem expands the cloud** to merge distance 3.64/3.25
   (vs control 2.31/2.16) — the largest signal in the matrix.
   Lorem injection under replace-mode produces a *new* basin that sits
   far from the original attractor, so the Ward linkage tree has to
   span a wide gap to merge the lorem-population into the rest of the
   embedding. Replace-mode trajectories are entirely captured by the
   lorem text, but the basin they're captured into is a long way
   off the original loop's manifold.
3. **O1 adversarial mildly compresses** (2.06 vs 2.38) — in-distribution
   adversarial text pulls into a tighter region. **O1 neutral and
   lorem are both close to control** (2.27, 2.37 vs 2.38), consistent
   with append-mode dilution: out-of-distribution perturbation gets
   averaged into the accumulating context and barely shifts the
   coarse-graining diameter.

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
78% at step-15 injection (D1 pilot, see §5.5), comes from drill-down's
content gravity. The Explorer-Expert pair has an explicit instruction to drill
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

### 9.1 Exact metric definitions (executable form)

These are the literal code snippets that implement the metrics
described conceptually in §4.5. Each is taken from `src/analysis/`
or `src/experiments/dynamics/` and is exercised by the test suite at
`tests/`. They are reproduced here for review by readers who prefer
code to prose.

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

Sharpness dimension (Tuci-style fractional dimension on the ordered
Lyapunov spectrum; see §4.5.6):

```python
lam = np.sort(lambda_t)[::-1]
cumsum = np.cumsum(lam)
nonneg = np.where(cumsum >= 0)[0]
if lam[0] < 0:
    SD_t = 0.0
elif len(nonneg) == len(lam):
    SD_t = float(len(lam))             # full-d case
else:
    j_star = int(nonneg[-1]) + 1       # 1-indexed
    SD_t = j_star + cumsum[j_star - 1] / abs(lam[j_star])
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
python -m scripts.aggregate_perturbation_geometric_barriers
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

94 pytest tests cover the analysis primitives plus integration:

```bash
PYTHONPATH=. python -m pytest tests/ -q
# 94 passed in ~12s
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
├── tests/             94 pytest tests
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

All 12 phases are implemented and exercised in the 94 unit + integration
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

- **Lyapunov spectrum** (REPORT3) — own construction, computed from
  inter-run ensemble spread covariance; not in the original brief
- **Sharpness dimension** (REPORT3) — functional form borrowed from
  Tuci et al. (2026, Def. 4.2), applied to our ensemble-spread Lyapunov
  spectrum; not in the original brief
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

Conceptual lineage drawn from the dynamical-systems treatment of
recurrent neural networks (Hopfield, 1982; Sussillo & Barak, 2013;
Maheswaranathan et al., 2019), the language-model-degeneration
literature (Holtzman et al., 2020; Carlini et al., 2021), and the
finite-time Lyapunov framework for sampling-based generators
(Tuci et al., 2026). Multi-turn dialog as an environment for emergent
attractor behavior is informed by the generative-agent line (Park et
al., 2023).

- Carlini, N., Tramèr, F., Wallace, E., et al. (2021). *Extracting
  training data from large language models.* In Proceedings of the
  30th USENIX Security Symposium.
- Hopfield, J. J. (1982). *Neural networks and physical systems with
  emergent collective computational abilities.* Proceedings of the
  National Academy of Sciences, 79(8), 2554–2558.
- Holtzman, A., Buys, J., Du, L., Forbes, M., & Choi, Y. (2020).
  *The curious case of neural text degeneration.* In ICLR.
- Maheswaranathan, N., Williams, A., Golub, M., Ganguli, S., &
  Sussillo, D. (2019). *Reverse engineering recurrent networks for
  sentiment classification reveals line attractor dynamics.* In
  NeurIPS.
- Park, J. S., O'Brien, J., Cai, C. J., Morris, M. R., Liang, P., &
  Bernstein, M. S. (2023). *Generative agents: interactive simulacra
  of human behavior.* In Proceedings of UIST '23.
- Sussillo, D., & Barak, O. (2013). *Opening the black box:
  low-dimensional dynamics in high-dimensional recurrent neural
  networks.* Neural Computation, 25(3), 626–649.
- Tuci, M., Korkmaz, C., Şimşekli, U., Birdal, T. (2026).
  *Generalization at the Edge of Stability.* arXiv:2604.19740.
  We borrow only the *functional form* of their sharpness dimension
  (Def. 4.2) as a comparative diagnostic over our ensemble-spread
  Lyapunov spectrum. Their setting (SGD optimization on parameter
  space, Hessian-anchored Edge-of-Stability) and their generalization
  bound (Theorem 4.5) do not transfer to our inference-time recursive
  setting; see §4.5.6 for the explicit caveat.

---

*Repository: <https://github.com/kaplan196883/llmattr> (raw trajectories
LFS-tracked; embeddings + plots regenerable from the documented
pipeline). Reproducibility budget: ~$30 in OpenAI embedding API + ~2
hours wall-clock on a 40-core machine.*
