## 2. Background and related work

### 2.1 Attractors in neural dynamics

Attractor analysis has long been central to the study of recurrent
neural systems. In classical recurrent networks, one studies fixed
points, cycles, and low-dimensional manifolds through tools such as
Jacobian linearization, Lyapunov spectra, and effective dimensionality
(Hopfield, 1982; Sussillo & Barak, 2013; Maheswaranathan et al., 2019).
Those tools assume a smooth state-update map. Recursive language-model
loops are different: they evolve through sampled text rather than
through a differentiable latent recurrence. For that reason, we work
with empirical analogs of classical dynamical diagnostics,
recurrence, dwell structure, ensemble-spread Lyapunov exponents,
effective dimension, and density-derived potential landscapes, rather
than with exact local linearizations.

### 2.2 Attractor observations in language models

The dynamical-systems framing of LLM inference loops has emerged
rapidly in 2025. arXiv:2512.10350 (*Dynamics of Agentic Loops in
Large Language Models: A Geometric Theory of Trajectories*)
formalizes recursive LLM transformations as discrete dynamical
systems in semantic space, identifying three regimes, **contractive**
(convergence to stable semantic attractors), **oscillatory**
(cycling), and **exploratory** (unbounded divergence), through a
measurement protocol of local drift, global drift, dispersion, and
cluster persistence. They show empirically that prompt design selects
the regime: iterative paraphrasing → contractive, iterative negation
→ exploratory.

arXiv:2510.21258 (Du and Tanaka-Ishii, *Correlation Dimension of
Auto-Regressive Large Language Models*) introduces correlation
dimension as a fractal-geometric measure of "epistemological
complexity of text," applied broadly across autoregressive
architectures (Transformer and Mamba). They report that
correlation dimension drops during pretraining phase transitions
and during multiple forms of generated-text degeneration. We do
not claim their framework explicitly characterizes degeneration as
"attractor collapse"; rather, the *direction of their effect*,
sharp dimensionality drop coincident with degeneration, is
compatible with the absorbing-regime interpretation we report in
O3 (§5.2), where a near-zero sharpness-dim and a single-cluster
late window are exactly the kind of dimensional collapse a
correlation-dim drop would track on a different observable.

Earlier work characterized degeneration *symptomatically* but without
the dynamical-systems framing. Carlini et al. (2021) noted aggressive
top-k sampling in GPT-2 can produce repetitive collapse. Holtzman et
al. (2020) systematized "degeneration" failure modes (repetition,
blandness) and motivated nucleus sampling.

### 2.3 What this paper adds

Relative to prior regime-classification work, this paper makes three
specific advances.

First, it separates the recursive loop into **state**, **generator**,
and **nudge**. This makes it possible to distinguish effects of the
language model itself from effects of the context-update architecture.
Second, it introduces a measurable notion of **barrier height**: the
amount of injected text required to produce a specified switching
probability across basins. Third, it shows that barrier structure
refines the standard regime taxonomy. In addition to contractive,
oscillatory, and absorbing behavior, we identify two dialog-specific
regimes, dialogue-state-driven multi-basin dialog (D1) and drill-down dialog
(D2), whose distinguishing feature is not dispersion alone, but
their perturbation signature.

A concise comparison with the closest prior work:

| dimension | arXiv:2512.10350 | this paper |
|---|---|---|
| regime taxonomy | 3 (contractive, oscillatory, exploratory) | 5 (+ D1 dialogue-state-driven multi-basin, + D2 drill-down dialog) |
| diagnostic metrics | local drift, global drift, dispersion, cluster persistence | + recurrence rate, sharpness dim, basin predictability acc(k), V\* geodesic-derived geometric barriers, RG dendrogram coarse-graining |
| barrier-height measurement | not measured | **token-quantified** via 4-condition perturbation protocol (control / neutral / lorem / adversarial) × 3 sweep dimensions (regime / dose / injection-time) |
| theoretical framework | discrete dynamical system in semantic space (informal) | state-generator-nudge formalism (§3.1) with formal access bound (Lemma 1) and append-mode accumulation conjecture (Conjecture 1) |
| geometric/behavioral triangulation | n/a | **rank-stable V\* ordering across 6 inter-basin geodesics matches perturbation-derived dose-rankings (89-98% of parameter combinations; absolute V\* magnitudes are descriptive only, CV 14-24% across a 45-point parameter grid)** (§5.10) |
| reproducibility | trajectory artifacts in appendices; code "to be considered following peer review" (no public link) | 103/103 cell-verified numeric claims (`RESULTS.md`); 37/37 experiments at 100% applicable artifact coverage (`COVERAGE.csv`); raw trajectories LFS-tracked; full code, configs, and prompt templates publicly available |
| trajectory scope | $n=2$ (one contractive, one exploratory), single seed, 50 iterations, three clustering configurations | 50-1,350 trajectories per configuration across 37 experiments |
| model | `deepseek-r1:8b` via Ollama 0.12.9 (8B params, $T=0.8$, no explicit seed) | `gpt-4o-mini`, with within-vendor cross-generation replication on `gpt-4.1-nano` (37/37 cells; pub-scale headline verdicts preserved) |

We share the dynamical-systems framing and the contractive /
oscillatory pair; we *add* the cost-of-nudging measurement and the
two dialog regimes whose distinguishing signature appears only when
that measurement is made. Tacheny (2025) introduced the
dynamical-systems framing on a single open-source generator
(`deepseek-r1:8b`) with two proof-of-concept singular loops; this
paper scales the protocol, paired controls, perturbation
dose-response, within-vendor cross-generation replication, and
full-trajectory release, and adds the formal generator/nudge
separation that makes context-update mechanics a first-class
property of the loop.

Tuci et al. (2026) study SGD-optimization dynamics
on neural-net loss landscapes via random dynamical systems and
introduce a "sharpness dimension" generalization bound at the edge
of stability. Their setting (parameter space, Hessian-anchored,
training dynamics) is structurally different from ours (embedding
space, no gradients, inference-time recursion of a frozen LLM). We
borrow only the *functional form* of their sharpness dimension
(Definition 4.2) as a comparative diagnostic across regimes; the
ensemble-spread Lyapunov machinery in
`src/experiments/dynamics/lyapunov.py` is our own construction. See
§4.5.6 for the explicit caveats.

### 2.4 Effective potential and geometric barriers

The use of $V(x) = -\log \rho(x)$ as an empirical *effective potential* is
standard in chemical-physics free-energy analysis and reaction-rate
theory: ρ(x) is the stationary density of a stochastic trajectory
ensemble in some reduced coordinate system, and V is the potential
that would yield ρ as the Boltzmann weight at unit temperature. We
adopt this as a purely empirical / data-driven landscape over the
PCA-2 projection of trajectory embeddings; no thermodynamic claims
are made about the LLM itself.

The accompanying visualization battery, Dijkstra geodesics between
density peaks (with their maximum-V along the path used as a
geometric barrier estimate) and volumetric iso-density renderings,
is descriptive rather than theoretical. It converts the empirical
density into shapes a human reader can read off, without assuming
any particular generative model of ρ.

### 2.5 Dialog as a distinct dynamical setting

Most prior work on recursive LLM dynamics focuses on single-stream
operators such as continuation, paraphrase, or negation. Multi-turn
LLM dialog has been studied for capability and alignment purposes
(Park et al., 2023, "Generative Agents") but not, to our knowledge,
with embedding-space attractor analysis. Multi-turn dialog introduces
a different architecture: generated text is not merely appended or
replaced, but inserted into a role-structured conversational state.
This turns dialog into a distinct family of nudges. In our experiments,
dialog does not simply reproduce the operator regimes. Instead, it
generates its own attractor structure, including dialogue-state-driven multi-basin behavior (D1) and topic-anchored drill-down dynamics (D2).

### 2.6 Terminology

The dynamical-systems literature uses "attractor," "basin,"
"cluster," "sink," "barrier," "switch," "collapse," "regime," and
"nudge" with overlapping but non-identical scopes. To avoid
ambiguity in this paper, we fix a strict hierarchy with explicit
definitions. All later usage conforms to this glossary unless
otherwise noted.

**Text state $X_t$.**
The text state is the bounded visible context string available to
the generator at recursive step $t$.
*Don't confuse with:* the generated output $Y_t$, which is only
the model's next text sample.

**Observable $\mathcal{O}(X_t)$.**
An observable is a deterministic text view extracted from the state
or output, such as `output`, `rolling_k3`, or `context_tail`.
*Don't confuse with:* an embedding, which is the numerical vector
computed from the observable text.

**Embedding $z_t$.**
An embedding is the vector representation
$z_t = \mathrm{embed}(\mathcal{O}(X_t))$ used for distances,
projections, clustering, and diagnostics.
*Don't confuse with:* the text state itself, which remains a string.

**Cluster.**
A cluster is a cell of the canonical K-means partition, fit on
PCA-10 embeddings with $k=12$ unless explicitly stated otherwise.
*Don't confuse with:* a basin, which requires additional temporal
or structural support beyond K-means membership.

**Basin / basin candidate.**
A basin candidate is a cluster or coarser embedding-space region
with evidence of persistence, recurrence/dwell, robustness,
contraction, re-entry, or collapse.
*Don't confuse with:* a raw cluster label, which may over-partition
or merge dynamical structure.

**Attractor-like regime.**
An attractor-like regime is a top-level recursive-loop behavior
whose basin candidates satisfy the operational criteria defined in
§3.1.3.
*Don't confuse with:* a classical deterministic attractor; our
claim is empirical and operational, not a smooth-state theorem.

**Regime label.**
A regime label is the human-readable name assigned to a generator-
nudge configuration after inspecting its diagnostics and
perturbation response.
*Don't confuse with:* a cluster label, which is an unsupervised
numerical partition index.

**Nudge.**
A nudge is the context-update operator $\mathcal{N}_f(X_t, Y_t)$
that writes generated or injected text into the next state.
*Don't confuse with:* a perturbation, which is externally injected
text used to test stability.

**Perturbation.**
A perturbation is controlled injected text inserted at a specified
step to test whether the trajectory changes its terminal cluster
or basin candidate.
*Don't confuse with:* ordinary generated text, which is sampled by
the model during unperturbed recursion.

**Switch / switching rate.**
A switch is final-step cluster disagreement between a perturbed
trajectory and its paired control trajectory, and switching rate
is the fraction of such events.
*Don't confuse with:* persistent basin escape, which requires
stronger evidence than final-cluster disagreement.

**Persistent basin escape.**
A persistent basin escape is a visible injection-time cluster jump
that remains in the post-injection basin through the terminal step.
*Don't confuse with:* stochastic post-injection divergence, where
final clusters differ without a durable basin-crossing event.

**Barrier height in tokens.**
Barrier height in tokens is the injected-token dose required to
produce at least 50% switching under a specified perturbation
protocol.
*Don't confuse with:* generated-token budget, which counts model
output after injection rather than injected text.

**Barrier height in nats.**
Barrier height in nats is the corresponding information cost
computed from conditional token surprisal, which is not numerically
measured in this battery.
*Don't confuse with:* the reported token barrier, which is
tokenizer-dependent and directly measured.

**Contractive.**
A contractive regime shows decreasing ensemble spread, low late
Lyapunov growth, or movement toward a stable basin candidate.
*Don't confuse with:* absorbing collapse, where trajectories become
trapped in a narrow template or fixed form.

**Oscillatory.**
An oscillatory regime shows repeated return to alternating states
or cycle arms, typically detected by lag-periodicity and high
recurrence.
*Don't confuse with:* generic recurrence, which need not imply a
period-2 or periodic structure.

**Absorbing.**
An absorbing regime traps trajectories in a fixed discourse form,
low-dimensional template, or near-invariant output pattern.
*Don't confuse with:* semantic convergence; in O3 the absorption
is template-formal, not topic-identical (see §5.14).

**Multi-basin.**
A multi-basin regime contains several supported basin candidates,
often corresponding to register, dialogue state, or recent-context
capture.
*Don't confuse with:* many K-means clusters; multi-basin status
requires structural support beyond cluster count.

**Sink.**
A sink is a descriptive visualization term for a local density or
flow-convergence region in projected embedding space.
*Don't confuse with:* an attractor-like regime, which is a full
trajectory-level classification.

**Collapse.**
Collapse is a strong reduction of trajectory diversity into a narrow
template, cluster, or low-dimensional region.
*Don't confuse with:* contraction, which can preserve multiple
supported basins while reducing dispersion.

**How we use these terms.**
In this paper, "attractor-like" is the only term used for top-level
regime claims. "Cluster" refers specifically to the canonical
K-means partition unless another clustering method is named.
"Basin" means a cluster or coarser region with structural support
from the diagnostic battery. "Switching rate" is the operational
final-step cluster-disagreement metric used in the perturbation
pilots. "Persistent basin escape" is the stricter measure
introduced in §5.15, requiring an injection-time jump that
remains in the new basin. Claims about barrier height are tied to
the stated switching definition unless explicitly marked as
persistent-escape barriers.

**The strict hierarchy is:**

`text state X_t → observable O(X_t) → embedding z_t → K-means cluster → basin candidate → attractor-like regime`

---
